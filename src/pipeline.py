"""De 7 - phat hien & canh bao xe dung/do trai phep.
Backend: 'yolo' (baseline: YOLO26 + ByteTrack/BoT-SORT) | 'sam3' (loi: SAM 3.1 multiplex video, text prompt).
Re-ID: DINOv3 (tuy chon) noi lai timer dwell khi track mat/doi ID (che khuat, ranh gioi chunk).
Logic: ROI polygon -> dung yen -> dwell timer -> phan biet ket xe -> alert CSV/JSON + snapshot + clip.
"""
import argparse, collections, csv, json, os, shutil, tempfile, time
import cv2, numpy as np

VEH = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}  # COCO ids

# ---------------- backends: yield (frame_idx, frame_bgr, dets[{id,box,cls,mask}]) ----------------
def frames(video, stride, max_frames):
    cap = cv2.VideoCapture(video); fi = -1
    while True:
        ok, f = cap.read(); fi += 1
        if not ok or (max_frames and fi >= max_frames): break
        if fi % stride == 0: yield fi, f

def yolo_backend(a, timers):
    from ultralytics import YOLO
    model = YOLO(a.model)
    for fi, f in frames(a.video, a.stride, a.max_frames):
        t0 = time.perf_counter()
        r = model.track(f, persist=True, tracker=a.tracker, imgsz=a.imgsz, conf=a.conf,
                        classes=list(VEH), device=a.device, verbose=False, half=a.half)[0]
        timers["model"] += time.perf_counter() - t0
        dets = []
        if r.boxes.id is not None:
            for b, tid, c in zip(r.boxes.xyxy.cpu().numpy(), r.boxes.id.int().cpu().tolist(), r.boxes.cls.int().cpu().tolist()):
                dets.append({"id": tid, "box": b, "cls": VEH.get(c, str(c)), "mask": None})
        yield fi, f, dets

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
    print("SAM3 loaded, VRAM MB", round(torch.cuda.memory_allocated() / 2**20), flush=True)
    buf, chunk_id = [], 0
    def run_chunk(buf, chunk_id):
        tmp = tempfile.mkdtemp(prefix="sam3chunk_")
        for i, (fi, f) in enumerate(buf): cv2.imwrite(f"{tmp}/{i:05d}.jpg", f, [cv2.IMWRITE_JPEG_QUALITY, 95])
        H, W = buf[0][1].shape[:2]
        t0 = time.perf_counter()
        with torch.autocast("cuda", dtype=a.amp_dtype, enabled=a.amp_dtype is not None):
            sid = pred.handle_request(dict(type="start_session", resource_path=tmp, offload_video_to_cpu=a.offload_video))["session_id"]
            pred.handle_request(dict(type="add_prompt", session_id=sid, frame_index=0, text=a.prompt))
            outs = {r["frame_index"]: r["outputs"] for r in pred.handle_stream_request(dict(type="propagate_in_video", session_id=sid))}
            pred.handle_request(dict(type="close_session", session_id=sid))
        timers["model"] += time.perf_counter() - t0
        shutil.rmtree(tmp, ignore_errors=True)
        for i, (fi, f) in enumerate(buf):
            o = outs.get(i, {}); dets = []
            ids = o.get("out_obj_ids", np.zeros(0)); bx = o.get("out_boxes_xywh", np.zeros((0, 4))); ms = o.get("out_binary_masks")
            for k, oid in enumerate(np.asarray(ids).tolist()):
                x, y, w, h = [float(v) for v in bx[k]]
                if max(x, y, w, h) <= 1.5: x, y, w, h = x * W, y * H, w * W, h * H
                if w < 2 or h < 2: continue
                dets.append({"id": chunk_id * 100000 + int(oid), "box": np.array([x, y, x + w, y + h]), "cls": a.prompt,
                             "mask": ms[k] if ms is not None else None})
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
    ap.add_argument("--reid_thr", type=float, default=0.6)
    ap.add_argument("--stride", type=int, default=1); ap.add_argument("--max_frames", type=int, default=0)
    ap.add_argument("--out", default="outputs/run"); ap.add_argument("--save_video", action="store_true")
    a = ap.parse_args()
    import torch; torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "4")))
    cuda = torch.cuda.is_available() and a.device != "cpu"
    a.amp_dtype = None if (a.amp == "none" or not cuda) else (torch.float16 if a.amp == "fp16" else torch.bfloat16)
    if cuda: torch.cuda.reset_peak_memory_stats()
    os.makedirs(a.out + "/evidence", exist_ok=True)
    cap = cv2.VideoCapture(a.video); fps = cap.get(cv2.CAP_PROP_FPS) or 25; W, H = int(cap.get(3)), int(cap.get(4)); cap.release()
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
    t_start = time.perf_counter()
    for fi, frame, dets in backend(a, timers):
        t = fi / fps; n_proc += 1; seen = []
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
    if vw: vw.release()
    metrics = {"video": a.video, "backend": a.backend, "model": a.model if a.backend == "yolo" else "sam3.1_multiplex", "tracker": a.tracker if a.backend == "yolo" else "sam3.1",
               "reid": a.reid, "device": torch.cuda.get_device_name(0) if cuda else "cpu", "amp": a.amp if cuda else "none", "stride": a.stride,
               "frames_processed": n_proc, "fps_model": round(n_proc / max(timers["model"], 1e-9), 2), "reid_time_s": round(timers["reid"], 2),
               "fps_end2end": round(n_proc / max(wall, 1e-9), 2), "wall_s": round(wall, 1), "n_alerts": len(alerts), "jam_frames": int(jam_frames), "reid_merges": n_reid,
               "vram_peak_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1) if cuda else None}
    json.dump(alerts, open(a.out + "/alerts.json", "w"), indent=2, ensure_ascii=False)
    with open(a.out + "/alerts.csv", "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["video", "backend", "track_id", "class", "zone", "stop_start_s", "alert_time_s", "dwell_s", "bbox", "frame", "snapshot", "clip"])
        wr.writeheader(); [wr.writerow(e) for e in alerts]
    json.dump(metrics, open(a.out + "/metrics.json", "w"), indent=2)
    print("METRICS", json.dumps(metrics), flush=True)

if __name__ == "__main__":
    main()
