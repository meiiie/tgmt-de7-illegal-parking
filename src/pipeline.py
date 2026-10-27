"""De 7 - phat hien & canh bao xe dung/do trai phep.
Backend: 'yolo' (baseline: YOLO26 + ByteTrack/BoT-SORT) | 'sam3' (loi: SAM 3.1 multiplex video, text prompt).
Re-ID: DINOv3 (tuy chon) noi lai timer dwell khi track mat/doi ID (che khuat, ranh gioi chunk).
Logic: ROI polygon -> dung yen -> dwell timer -> phan biet ket xe -> alert CSV/JSON + snapshot + clip.
"""
import argparse, collections, csv, json, os, shutil, sys, tempfile, time
import cv2, numpy as np

VEH = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}  # COCO ids

# ---------------- backends: yield (frame_idx, frame_bgr, dets[{id,box,cls,mask}]) ----------------
MAX_SIDE = 0  # >0: thu nho frame (canh dai) truoc moi xu ly -> giam VRAM/IO cho SAM 3.1

def frames(video, stride, max_frames):
    cap = cv2.VideoCapture(video); fi = -1
    while True:
        ok, f = cap.read(); fi += 1
        if not ok or (max_frames and fi >= max_frames): break
        if fi % stride == 0:
            if MAX_SIDE and max(f.shape[:2]) > MAX_SIDE:
                r = MAX_SIDE / max(f.shape[:2]); f = cv2.resize(f, (round(f.shape[1] * r), round(f.shape[0] * r)), interpolation=cv2.INTER_AREA)
            yield fi, f

def yolo_backend(a, timers):
    from ultralytics import YOLO
    model = YOLO(a.model)
    n = 0
    for fi, f in frames(a.video, a.stride, a.max_frames):
        t0 = time.perf_counter()
        ck = n // a.yolo_reset if a.yolo_reset else 0  # gia lap ranh gioi chunk: reset tracker -> ID moi
        r = model.track(f, persist=not (a.yolo_reset and n % a.yolo_reset == 0 and n > 0),  tracker=a.tracker, imgsz=a.imgsz, conf=a.conf,
                        classes=list(VEH), device=a.device, verbose=False, half=a.half)[0]
        timers["model"] += time.perf_counter() - t0
        dets = []
        if r.boxes.id is not None:
            for b, tid, c, sc in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.id.int().cpu().tolist(), r.boxes.cls.int().cpu().tolist(), r.boxes.conf.cpu().tolist()):
                dets.append({"id": ck * 100000 + tid, "box": b, "cls": VEH.get(c, str(c)), "mask": None, "score": float(sc)})
        n += 1
        yield fi, f, dets

def yolo_box_prompts(model, frame, conf=0.25, max_boxes=32, min_wh=4):
    """Box YOLO26 (xe) tren frame dau chunk -> prompt hinh hoc cho SAM 3.1: [x,y,w,h] chuan hoa 0..1, nhan 1 (positive)."""
    H, W = frame.shape[:2]
    r = model.predict(frame, conf=conf, classes=list(VEH), verbose=False)[0]
    b = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else np.zeros((0, 4))
    order = np.argsort(-r.boxes.conf.cpu().numpy()) if len(b) else []
    out = []
    for k in order[:max_boxes]:
        x1, y1, x2, y2 = np.clip(b[k], 0, [W, H, W, H])
        if x2 - x1 >= min_wh and y2 - y1 >= min_wh: out.append([float(x1 / W), float(y1 / H), float((x2 - x1) / W), float((y2 - y1) / H)])
    return out, [1] * len(out)

def sam3_backend(a, timers):
    """SAM 3.1: chia video thanh chunk (frame da lay mau -> thu muc JPEG), moi chunk 1 session + text prompt.
    ID giua cac chunk duoc noi bang IoU + DINOv3 trong DwellEngine (offset ID theo chunk)."""
    import torch
    from sam3.model_builder import build_sam3_multiplex_video_predictor
    # T4 (sm75): sam3 decoder ep SDPA FLASH (khong ho tro bf16 tren Turing) -> cho phep EFFICIENT/MATH
    import sam3.model.decoder as _dec
    from torch.nn.attention import sdpa_kernel as _sk, SDPBackend as _B
    _dec.sdpa_kernel = lambda *x, **y: _sk([_B.FLASH_ATTENTION, _B.EFFICIENT_ATTENTION, _B.MATH])
    # bf16 khong co kernel EFFICIENT tren sm75 -> roi ve MATH (attention matrix ~5 GB, OOM). Ep q,k,v sang fp16 cho attention.
    import types, torch.nn.functional as _F
    _bf16_ok = torch.cuda.is_available() and torch.cuda.get_device_capability()[0] >= 8
    def _sdpa(q, k, v, *x, **y):
        dt = q.dtype
        if not _bf16_ok and dt == torch.bfloat16: q, k, v = q.half(), k.half(), v.half()
        # chia query thanh block de neu roi ve MATH thi ma tran attention nho (<~0.5 GB)
        nq, nk = q.shape[-2], k.shape[-2]
        bs = max(256, int(1.2e8 // max(nk * max(q[..., :1, :1].numel(), 1), 1)))
        if nq * nk * q[..., :1, :1].numel() > 2e8 and not y.get("attn_mask") is not None:
            out = torch.cat([_F.scaled_dot_product_attention(q[..., i:i + bs, :], k, v, *x, **y) for i in range(0, nq, bs)], dim=-2)
        else:
            out = _F.scaled_dot_product_attention(q, k, v, *x, **y)
        return out.to(dt)
    _dec.torchF = types.SimpleNamespace(**{n: getattr(_F, n) for n in dir(_F) if not n.startswith("__")})
    _dec.torchF.scaled_dot_product_attention = _sdpa
    kw = dict(use_fa3=a.fa3, compile=False, max_num_objects=a.max_objects)
    if a.sam3_ckpt: kw["checkpoint_path"] = a.sam3_ckpt
    pred = build_sam3_multiplex_video_predictor(**kw)
    # workaround upstream (sam3@7f473cf): base start_session truyen offload_state_to_cpu nhung multiplex init_state khong nhan
    _orig = pred.model.init_state
    def _init_state(**k):
        k.pop("offload_state_to_cpu", None); return _orig(**k)
    pred.model.init_state = _init_state
    # T4 16GB: detector mac dinh batch 16 frame 1008x1008 -> OOM; giam batch grounding/postprocess
    for attr in ("batched_grounding_batch_size", "postprocess_batch_size"):
        if hasattr(pred.model, attr): setattr(pred.model, attr, a.det_batch)
    ymodel = None
    if a.box_prompt:
        from ultralytics import YOLO
        ymodel = YOLO(a.box_prompt)
    print("SAM3 loaded, VRAM MB", round(torch.cuda.memory_allocated() / 2**20), flush=True)
    buf, chunk_id = [], 0
    def run_chunk(buf, chunk_id):
        tmp = tempfile.mkdtemp(prefix="sam3chunk_")
        for i, (fi, f) in enumerate(buf): cv2.imwrite(f"{tmp}/{i:05d}.jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 95])
        H, W = buf[0][1].shape[:2]
        t0 = time.perf_counter()
        with torch.autocast("cuda", dtype=a.amp_dtype, enabled=a.amp_dtype is not None):
            sid = pred.handle_request(dict(type="start_session", resource_path=tmp, offload_video_to_cpu=a.offload_video))["session_id"]
            req = dict(type="add_prompt", session_id=sid, frame_index=0, text=a.prompt)
            if ymodel is not None:
                bx, bl = yolo_box_prompts(ymodel, buf[0][1], max_boxes=a.max_objects)
                if bx: req.update(bounding_boxes=bx, bounding_box_labels=bl)
                timers.setdefault("box_prompts", []).append(len(bx))
            pred.handle_request(req)
            outs = {r["frame_index"]: r["outputs"] for r in pred.handle_stream_request(dict(type="propagate_in_video", session_id=sid))}
            pred.handle_request(dict(type="close_session", session_id=sid))
        timers["model"] += time.perf_counter() - t0
        shutil.rmtree(tmp, ignore_errors=True)
        for i, (fi, f) in enumerate(buf):
            o = outs.get(i, {}); dets = []
            ids = o.get("out_obj_ids", np.zeros(0)); bx = o.get("out_boxes_xywh", np.zeros((0, 4))); ms = o.get("out_binary_masks")
            pr = o.get("out_probs", None)
            for k, oid in enumerate(np.asarray(ids).tolist()):
                x, y, w, h = [float(v) for v in bx[k]]
                if max(x, y, w, h) <= 1.5: x, y, w, h = x * W, y * H, w * W, h * H
                if w < 2 or h < 2: continue
                dets.append({"id": chunk_id * 100000 + int(oid), "box": np.array([x, y, x + w, y + h]), "cls": a.prompt,
                             "mask": ms[k] if ms is not None else None, "score": float(np.asarray(pr)[k]) if pr is not None and len(pr) > k else None})
            yield fi, f, dets
    for fi, f in frames(a.video, a.stride, a.max_frames):
        buf.append((fi, f))
        if len(buf) >= a.chunk_frames:
            yield from run_chunk(buf, chunk_id); buf, chunk_id = [], chunk_id + 1
            torch.cuda.empty_cache()
    if buf: yield from run_chunk(buf, chunk_id)

# ---------------- DINOv3 re-ID ----------------
class Reid:
    def __init__(s, name, device):
        import torch
        from transformers import AutoImageProcessor, AutoModel
        s.torch, s.dev = torch, device
        s.proc = AutoImageProcessor.from_pretrained(name); s.m = AutoModel.from_pretrained(name).to(device).eval()
    def embed(s, frame, box, mask=None):
        x1, y1, x2, y2 = [int(v) for v in box]; H, W = frame.shape[:2]
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(W, x2), min(H, y2)
        crop = frame[y1:y2, x1:x2].copy()
        if crop.size == 0: return None
        if mask is not None and mask.shape[:2] == (H, W):
            crop[~mask[y1:y2, x1:x2].astype(bool)] = 0
        inp = s.proc(images=cv2.cvtColor(crop, cv2.COLOR_BGR2RGB), return_tensors="pt").to(s.dev)
        with s.torch.no_grad():
            e = s.m(**inp).pooler_output[0]
        e = e / e.norm(); return e.float().cpu().numpy()

class Stitcher:
    """Noi ID qua ranh gioi chunk (SAM 3.1 moi chunk 1 session; YOLO reset tracker): ID cuc bo moi xuat hien
    -> ghep voi track toan cuc vua mat (khong co mat o frame nay, mat <= gap_s) neu IoU >= iou_thr
    va (neu co DINOv3) cosine >= sim_thr. Khong khop -> ID toan cuc moi."""
    def __init__(s, reid, iou_thr=0.3, sim_thr=0.5, gap_s=20.0, emb_every=10):
        s.reid, s.iou_thr, s.sim_thr, s.gap_s, s.emb_every = reid, iou_thr, sim_thr, gap_s, emb_every
        s.map, s.g, s.next, s.n_stitch, s.time = {}, {}, 1, 0, 0.0
    def _emb(s, frame, d):
        if s.reid is None: return None
        t0 = time.perf_counter(); e = s.reid.embed(frame, d["box"], d.get("mask")); s.time += time.perf_counter() - t0; return e
    def __call__(s, frame, t, dets):
        used = {s.map[d["id"]] for d in dets if d["id"] in s.map}
        for d in dets:
            lid = d["id"]; d["raw_id"] = lid
            if lid not in s.map:
                cand = [(iou(g["box"], d["box"]), gid) for gid, g in s.g.items() if gid not in used and 0 < t - g["t"] <= s.gap_s]
                cand = sorted([c for c in cand if c[0] >= s.iou_thr], reverse=True)
                e = self_e = s._emb(frame, d) if cand else None
                gid = None
                for _, cg in cand:
                    ge = s.g[cg]["emb"]
                    if e is None or ge is None or float(np.dot(e, ge)) >= s.sim_thr: gid = cg; break
                if gid is None: gid = s.next; s.next += 1
                else: s.n_stitch += 1
                s.map[lid] = gid; used.add(gid)
                s.g.setdefault(gid, {"emb": None, "n": 0})
                if self_e is not None: s.g[gid]["emb"] = self_e
            gid = s.map[lid]; g = s.g[gid]; g["box"], g["t"] = d["box"], t; g["n"] += 1
            if s.reid is not None and (g["emb"] is None or g["n"] % s.emb_every == 0): g["emb"] = s._emb(frame, d)
            d["id"] = gid
        for gid in [k for k, v in s.g.items() if t - v.get("t", t) > s.gap_s * 3]: del s.g[gid]
        return dets

def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy; u = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i
    return i / u if u > 0 else 0

# ---------------- logic ----------------
def load_zones(path, w, h):
    cfg = json.load(open(path)); zones = []
    for z in cfg["zones"]:
        pts = np.array(z["polygon"], dtype=np.float32)
        if pts.max() <= 1.0: pts *= [w, h]
        zones.append({"name": z["name"], "poly": pts.astype(np.int32), "max_dwell_s": float(z.get("max_dwell_s", cfg.get("max_dwell_s", 10)))})
    return cfg, zones

def in_zone(zones, x, y):
    for z in zones:
        if cv2.pointPolygonTest(z["poly"], (float(x), float(y)), False) >= 0: return z
    return None

class Track:
    def __init__(s, tid, cls):
        s.id, s.cls = tid, cls; s.hist = collections.deque(maxlen=256)
        s.still_since = None; s.last_seen = 0; s.alerted = False; s.zone = None; s.emb = None; s.is_still = False; s.box = None
    def stationary(s, t, win_s, tol):
        old = [p for p in s.hist if t - p[0] >= win_s]
        if not old: return False
        p0, p1 = old[-1], s.hist[-1]
        return np.hypot(p1[1]-p0[1], p1[2]-p0[2]) < tol * max(p1[3], 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True); ap.add_argument("--zones", required=True)
    ap.add_argument("--backend", default="yolo", choices=["yolo", "sam3"])
    ap.add_argument("--model", default="yolo26n.pt"); ap.add_argument("--tracker", default="bytetrack.yaml")
    ap.add_argument("--imgsz", type=int, default=640); ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--device", default=None); ap.add_argument("--half", action="store_true")
    ap.add_argument("--prompt", default="car"); ap.add_argument("--sam3_ckpt", default=None)
    ap.add_argument("--chunk_frames", type=int, default=150); ap.add_argument("--max_objects", type=int, default=16)
    ap.add_argument("--fa3", action="store_true"); ap.add_argument("--offload_video", action="store_true"); ap.add_argument("--det_batch", type=int, default=16); ap.add_argument("--amp", default="fp16", choices=["none", "fp16", "bf16"])
    ap.add_argument("--reid", default="none", help="none | HF id, vd facebook/dinov3-vits16-pretrain-lvd1689m")
    ap.add_argument("--reid_thr", type=float, default=0.75); ap.add_argument("--dedup_iou", type=float, default=0.3); ap.add_argument("--min_area", type=float, default=200)
    ap.add_argument("--stride", type=int, default=1); ap.add_argument("--max_frames", type=int, default=0)
    ap.add_argument("--max_side", type=int, default=0, help="thu nho canh dai frame (px), 0 = giu nguyen")
    ap.add_argument("--dump_tracks", action="store_true", help="ghi out/tracks.csv: frame,t,raw_id,id,x1,y1,x2,y2,score,still,dwell")
    ap.add_argument("--stitch", action="store_true", help="noi ID qua ranh gioi chunk (IoU + DINOv3 neu co --reid)")
    ap.add_argument("--stitch_iou", type=float, default=0.3); ap.add_argument("--stitch_sim", type=float, default=0.5); ap.add_argument("--stitch_gap_s", type=float, default=20.0)
    ap.add_argument("--yolo_reset", type=int, default=0, help="YOLO: reset tracker moi N frame mau (gia lap chunk de test stitch)")
    ap.add_argument("--box_prompt", default=None, help="YOLO weights (vd yolo26s.pt): box xe o frame dau moi chunk lam prompt hinh hoc cho SAM 3.1 (cung text)")
    ap.add_argument("--sanity", type=int, default=0, help="chi chay N frame dau, in SANITY so box; exit 3 neu 0 box")
    ap.add_argument("--out", default="outputs/run"); ap.add_argument("--save_video", action="store_true")
    a = ap.parse_args()
    global MAX_SIDE; MAX_SIDE = a.max_side
    import torch; torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "4")))
    cuda = torch.cuda.is_available() and a.device != "cpu"
    a.amp_dtype = None if (a.amp == "none" or not cuda) else (torch.float16 if a.amp == "fp16" else torch.bfloat16)
    if cuda: torch.cuda.reset_peak_memory_stats()
    os.makedirs(a.out + "/evidence", exist_ok=True)
    cap = cv2.VideoCapture(a.video); fps = cap.get(cv2.CAP_PROP_FPS) or 25; W, H = int(cap.get(3)), int(cap.get(4)); cap.release()
    if a.max_side and max(W, H) > a.max_side: r = a.max_side / max(W, H); W, H = round(W * r), round(H * r)
    backend = yolo_backend if a.backend == "yolo" else sam3_backend
    if a.sanity:  # kiem tra nhanh truoc khi chay full (vd prompt sai -> 0 box)
        a.chunk_frames = a.sanity; nb, nf = 0, 0
        for fi, _, dets in backend(a, {"model": 0.0, "reid": 0.0}):
            nb += len(dets); nf += 1
            if nf >= a.sanity: break
        vram = round(torch.cuda.max_memory_allocated() / 2**20, 1) if cuda else None
        print("SANITY", json.dumps({"video": a.video, "prompt": a.prompt, "frames": nf, "boxes": nb, "vram_peak_mb": vram}), flush=True)
        sys.exit(0 if nb > 0 else 3)
    cfg, zones = load_zones(a.zones, W, H)
    win_s, tol, grace_s = cfg.get("still_window_s", 2.0), cfg.get("still_tol", 0.15), cfg.get("lost_grace_s", 3.0)
    reid_keep_s = cfg.get("reid_keep_s", 30.0)
    jam_ratio, jam_min = cfg.get("jam_ratio", 0.6), cfg.get("jam_min_vehicles", 4)
    ring = collections.deque(maxlen=max(1, int(cfg.get("clip_s", 6) * fps / a.stride)))
    reid = Reid(a.reid, "cuda" if cuda else "cpu") if a.reid != "none" else None
    vw = cv2.VideoWriter(a.out + "/annotated.mp4", cv2.VideoWriter_fourcc(*"mp4v"), fps / a.stride, (W, H)) if a.save_video else None
    timers = {"model": 0.0, "reid": 0.0}
    tracks, lost, alerts, n_proc, jam_frames, n_reid = {}, {}, [], 0, 0, 0
    backend = yolo_backend if a.backend == "yolo" else sam3_backend
    stitcher = Stitcher(reid, a.stitch_iou, a.stitch_sim, a.stitch_gap_s) if a.stitch else None
    dump = None
    if a.dump_tracks:
        dump_f = open(a.out + "/tracks.csv", "w", newline=""); dump = csv.writer(dump_f)
        dump.writerow(["frame", "t", "raw_id", "id", "x1", "y1", "x2", "y2", "score", "still", "dwell"])
    t_start = time.perf_counter()
    for fi, frame, dets in backend(a, timers):
        t = fi / fps; n_proc += 1; seen = []
        if stitcher: dets = stitcher(frame, t, dets)
        for d in dets:
            tr = tracks.get(d["id"])
            if tr is None:
                tr = tracks[d["id"]] = Track(d["id"], d["cls"])
                # re-ID: ke thua timer cua track da mat tai cung vi tri
                cand = [l for l in lost.values() if iou(l.box, d["box"]) >= 0.5]
                if cand:
                    ok = None
                    if reid is not None:
                        t0 = time.perf_counter(); e = reid.embed(frame, d["box"], d["mask"]); timers["reid"] += time.perf_counter() - t0
                        tr.emb = e
                        sims = [(float(np.dot(e, l.emb)), l) for l in cand if l.emb is not None and e is not None]
                        if sims and max(sims, key=lambda s: s[0])[0] >= a.reid_thr: ok = max(sims, key=lambda s: s[0])[1]
                    else:
                        ok = max(cand, key=lambda l: iou(l.box, d["box"])) if a.backend == "sam3" else None
                    if ok is not None:
                        tr.still_since, tr.zone, tr.alerted, tr.hist = ok.still_since, ok.zone, ok.alerted, ok.hist
                        del lost[ok.id]; n_reid += 1
            x1, y1, x2, y2 = d["box"]
            tr.hist.append((t, (x1+x2)/2, y2, y2-y1)); tr.last_seen = t; tr.box = tuple(int(v) for v in d["box"]); tr.mask = d["mask"]
            seen.append(tr)
        for tr in seen:
            st = tr.stationary(t, win_s, tol); tr.is_still = st
            z = in_zone(zones, tr.hist[-1][1], tr.hist[-1][2])
            if st and z is not None:
                if tr.still_since is None or tr.zone is not z: tr.still_since, tr.zone = t - win_s, z
                if reid is not None and tr.emb is None:
                    t0 = time.perf_counter(); tr.emb = reid.embed(frame, tr.box, tr.mask); timers["reid"] += time.perf_counter() - t0
            elif not st:
                tr.still_since, tr.zone, tr.alerted = None, None, False
        if dump:
            for tr in seen:
                d0 = next((d for d in dets if d["id"] == tr.id), {})
                dump.writerow([fi, round(t, 2), d0.get("raw_id", tr.id), tr.id, *tr.box, None if d0.get("score") is None else round(d0["score"], 3),
                               int(tr.is_still), round(t - tr.still_since, 1) if tr.still_since is not None else 0])
        n_still = sum(tr.is_still for tr in seen)
        jam = bool(len(seen) >= jam_min and n_still / max(len(seen), 1) >= jam_ratio); jam_frames += jam
        for tid in [k for k, v in tracks.items() if t - v.last_seen > 0 and v not in seen]:
            v = tracks[tid]
            if v.still_since is not None: lost[tid] = v
            if t - v.last_seen > grace_s: del tracks[tid]
        for k in [k for k, v in lost.items() if t - v.last_seen > reid_keep_s]: del lost[k]
        vis = frame.copy()
        for z in zones: cv2.polylines(vis, [z["poly"]], True, (0, 0, 255), 2)
        for tr in seen:
            dwell = (t - tr.still_since) if tr.still_since is not None else 0
            x1, y1, x2, y2 = tr.box
            dup = any(iou(e["bbox"], tr.box) >= a.dedup_iou for e in alerts) if a.dedup_iou > 0 else False
            small = (x2 - x1) * (y2 - y1) < a.min_area
            if tr.zone and dwell >= tr.zone["max_dwell_s"] and not tr.alerted and (dup or small) and not jam:
                tr.alerted = True  # cung vi tri voi canh bao truoc (cung su co) hoac xe qua xa -> khong canh bao lai
            if tr.zone and dwell >= tr.zone["max_dwell_s"] and not tr.alerted and not jam:
                tr.alerted = True
                ev = {"video": os.path.basename(a.video), "backend": a.backend, "track_id": tr.id, "class": tr.cls, "zone": tr.zone["name"],
                      "stop_start_s": round(tr.still_since, 2), "alert_time_s": round(t, 2), "dwell_s": round(dwell, 2), "bbox": list(tr.box), "frame": fi}
                im = vis.copy(); cv2.rectangle(im, (x1, y1), (x2, y2), (0, 0, 255), 3)
                ev["snapshot"] = f"{a.out}/evidence/alert_{tr.id}_{fi}.jpg"; cv2.imwrite(ev["snapshot"], im)
                ev["clip"] = f"{a.out}/evidence/alert_{tr.id}_{fi}.mp4"
                cw = cv2.VideoWriter(ev["clip"], cv2.VideoWriter_fourcc(*"mp4v"), fps / a.stride, (W, H))
                for f in ring: cw.write(f)
                cw.write(im); cw.release()
                alerts.append(ev); print("ALERT", json.dumps(ev, ensure_ascii=False), flush=True)
            col = (0, 0, 255) if tr.alerted else (0, 200, 255) if tr.still_since is not None else (0, 255, 0)
            if tr.mask is not None and tr.mask.shape[:2] == vis.shape[:2]:
                vis[tr.mask.astype(bool)] = (0.6 * vis[tr.mask.astype(bool)] + 0.4 * np.array(col)).astype(np.uint8)
            cv2.rectangle(vis, (x1, y1), (x2, y2), col, 2); cv2.putText(vis, f"{tr.id % 100000} {dwell:.0f}s", (x1, y1 - 4), 0, 0.5, col, 1)
        if jam: cv2.putText(vis, "TRAFFIC JAM - alerts suppressed", (10, 30), 0, 0.8, (0, 0, 255), 2)
        ring.append(vis)
        if vw: vw.write(vis)
    wall = time.perf_counter() - t_start
    if dump: dump_f.close()
    if stitcher: timers["reid"] += stitcher.time
    if vw: vw.release()
    metrics = {"video": a.video, "backend": a.backend, "model": a.model if a.backend == "yolo" else "sam3.1_multiplex", "tracker": a.tracker if a.backend == "yolo" else "sam3.1",
               "reid": a.reid, "device": torch.cuda.get_device_name(0) if cuda else "cpu", "amp": a.amp if cuda else "none", "stride": a.stride,
               "frames_processed": n_proc, "fps_model": round(n_proc / max(timers["model"], 1e-9), 2), "reid_time_s": round(timers["reid"], 2),
               "fps_end2end": round(n_proc / max(wall, 1e-9), 2), "wall_s": round(wall, 1), "n_alerts": len(alerts), "jam_frames": int(jam_frames), "reid_merges": n_reid, "box_prompts_per_chunk": timers.get("box_prompts"), "stitches": stitcher.n_stitch if stitcher else 0, "n_ids_stitched": (stitcher.next - 1) if stitcher else None,
               "vram_peak_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1) if cuda else None}
    json.dump(alerts, open(a.out + "/alerts.json", "w"), indent=2, ensure_ascii=False)
    with open(a.out + "/alerts.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["video", "backend", "track_id", "class", "zone", "stop_start_s", "alert_time_s", "dwell_s", "bbox", "frame", "snapshot", "clip"])
        wr.writeheader(); [wr.writerow(e) for e in alerts]
    json.dump(metrics, open(a.out + "/metrics.json", "w"), indent=2)
    print("METRICS", json.dumps(metrics), flush=True)

if __name__ == "__main__":
    main()
