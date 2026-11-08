import collections
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

os.environ["YOLO_OFFLINE"] = "true"
os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp")

from . import __version__
from .engine import Detection, DwellEngine
from .media import NO_WINDOW, ROOT, TimedVideoEncoder, VideoEncoder, sha256
from .models import Settings, Zone
from .store import Store, new_id, now


VEHICLES = {2:"car",3:"motorcycle",5:"bus",7:"truck"}


def atomic_bytes(path, data):
    temp = path.with_suffix(".part")
    temp.write_bytes(data)
    for attempt in range(6):
        try:
            os.replace(temp,path)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.01*2**attempt)


def run(store: Store, jid: str):
    bootstrap_start = time.perf_counter()
    import cv2
    import numpy as np
    import torch
    from ultralytics import YOLO

    torch.set_num_threads(4)
    torch.manual_seed(0)
    np.random.seed(0)
    job = store.job(jid)
    source = store.source(job["source_id"])
    config = job["config"]
    cfg = Settings.model_validate(config["settings"])
    zones = [Zone.model_validate(z) for z in config["zones"]]
    directory = store.root/"jobs"/jid
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"evidence").mkdir(exist_ok=True)
    started = bootstrap_start
    if job["started_at"]:
        started = time.perf_counter()-max(0,time.time()-datetime.fromisoformat(job["started_at"]).timestamp())
    store.update_job(jid,status="running")
    model_path = ROOT/cfg.model
    if not model_path.is_file():
        raise RuntimeError("Thiếu trọng số mô hình. Xem hướng dẫn cài đặt trong README.")
    cuda = cfg.device != "cpu" and torch.cuda.is_available()
    if cfg.device == "cuda" and not cuda:
        raise RuntimeError("CUDA không khả dụng. Chọn CPU hoặc tự động trong Cài đặt.")
    if cuda:
        torch.cuda.reset_peak_memory_stats()
    model = YOLO(str(model_path))
    engine = DwellEngine(zones,cfg)
    is_live = source["kind"] == "camera"
    if is_live:
        model.track(np.zeros((cfg.image_size,cfg.image_size,3),dtype=np.uint8),persist=True,tracker="bytetrack.yaml",imgsz=cfg.image_size,conf=cfg.confidence,classes=list(VEHICLES),device=0 if cuda else "cpu",verbose=False)
    recorded_at = config["source"]["metadata"].get("recorded_at")
    recording_clock = datetime.fromisoformat(recorded_at) if recorded_at else None
    manifest = {"application":f"Curb {__version__}","created_at":now(),"job_id":jid,"source":store.public_source(source),"config":config,"seed":0,"model_sha256":sha256(model_path),"source_sha256":source["metadata"].get("sha256"),"python":sys.version,"platform":platform.platform(),"packages":{p:importlib.metadata.version(p) for p in ("torch","ultralytics","numpy","opencv-python")},"code_sha256":{str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/"curb").glob("*.py"))},"device":torch.cuda.get_device_name(0) if cuda else "CPU","precision":"float32","tracker":"bytetrack.yaml","evaluation":"inference only; no independent accuracy evaluation"}
    try:
        manifest["git_commit"] = subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True,stdin=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=NO_WINDOW).strip()
    except (OSError,subprocess.CalledProcessError):
        manifest["git_commit"] = None
    (directory/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    cap, annotated, clips = None, None, []
    processed, event_count, detected_count, retries, jam_frames = 0,0,0,0,0
    model_seconds, next_sample, source_t, last_update = 0.0,0.0,0.0,0.0
    ring = collections.deque(maxlen=max(2,round(cfg.evidence_before*cfg.sample_fps)+2))
    live_start = time.monotonic()
    frame_index = -1
    duration = source["metadata"].get("duration") or 0
    limit = config.get("max_seconds",0)
    total = min(duration,limit) if duration and limit else duration or limit
    cancelled = False

    def open_source():
        return cv2.VideoCapture(source["uri"],cv2.CAP_FFMPEG,[cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,8000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,5000])

    def finish_clip(clip):
        clip["writer"].close()
        payload = clip["payload"]
        payload["clip_ready"] = True
        payload["clip_end_s"] = round(min(source_t,clip["end"]),3)
        store.execute("UPDATE events SET payload=? WHERE id=?",(json.dumps(payload),payload["id"]))

    try:
        cap = open_source()
        if not cap.isOpened():
            raise RuntimeError("Không mở được nguồn. Kiểm tra kết nối camera hoặc tệp video.")
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        source_fps = source_fps if 0 < source_fps < 241 else 25
        effective_fps = min(cfg.sample_fps,source_fps)
        while True:
            if (directory/"cancel").exists():
                cancelled = True
                break
            if processed % 25 == 0 and shutil.disk_usage(store.root).free < 200*1024**2:
                raise RuntimeError("Ổ lưu trữ còn dưới 200 MB. Dọn dữ liệu cũ hoặc chuyển thư mục dữ liệu rồi chạy lại.")
            ok, frame = cap.read()
            if not ok:
                if not is_live:
                    expected = source["metadata"].get("frames",0)
                    if expected and frame_index < expected-3 and not limit:
                        raise RuntimeError("Video kết thúc sớm hoặc bị hỏng. Bằng chứng đã ghi vẫn được giữ lại.")
                    break
                retries += 1
                if retries > 3:
                    raise RuntimeError("Mất kết nối camera sau 3 lần thử lại. Kiểm tra nguồn rồi tạo lượt chạy mới.")
                store.update_job(jid,error=f"Mất hình ảnh, đang kết nối lại ({retries}/3)…")
                cap.release()
                if (directory/"cancel").exists():
                    cancelled = True
                    break
                time.sleep(1)
                cap = open_source()
                engine = DwellEngine(zones,cfg)
                for tracker in getattr(model.predictor,"trackers",[]):
                    tracker.reset()
                continue
            frame_index += 1
            source_t = time.monotonic()-live_start if is_live else frame_index/source_fps
            if limit and source_t >= limit:
                break
            if source_t+1e-6 < next_sample:
                continue
            next_sample = source_t+1/effective_fps if is_live else next_sample+1/effective_fps
            if is_live:
                retries = 0
            h,w = frame.shape[:2]
            if max(h,w) > 1280:
                ratio = 1280/max(h,w)
                frame = cv2.resize(frame,(round(w*ratio),round(h*ratio)))
                h,w = frame.shape[:2]
            if processed == 0 and cfg.save_annotated and not is_live:
                annotated = VideoEncoder(directory/"annotated.mp4",w,h,effective_fps)
            before = time.perf_counter()
            result = model.track(frame,persist=True,tracker="bytetrack.yaml",imgsz=cfg.image_size,conf=cfg.confidence,classes=list(VEHICLES),device=0 if cuda else "cpu",verbose=False)[0]
            model_seconds += time.perf_counter()-before
            detections = []
            if result.boxes.id is not None:
                for box,tid,label,score in zip(result.boxes.xyxy.cpu().tolist(),result.boxes.id.int().cpu().tolist(),result.boxes.cls.int().cpu().tolist(),result.boxes.conf.cpu().tolist()):
                    detections.append(Detection(tid,VEHICLES[label],tuple(box),float(score)))
            detected_count += len(detections)
            wall_time = datetime.now().astimezone() if is_live else recording_clock+timedelta(seconds=source_t) if recording_clock else None
            events = engine.update(source_t,detections,w,h,wall_time)
            jam_frames += bool(engine.congested)
            visual = frame.copy()
            overlay = visual.copy()
            for zone in zones:
                if zone.enabled:
                    pts = (np.array(zone.polygon)*[w,h]).astype(np.int32)
                    cv2.fillPoly(overlay,[pts],(45,102,237))
                    cv2.polylines(visual,[pts],True,(45,102,237),2,cv2.LINE_AA)
            visual = cv2.addWeighted(visual,.9,overlay,.1,0)
            label_rectangles = []
            for det in detections:
                states = [s for s in engine.stops.values() if s.track_id == det.track_id and s.last_seen == source_t]
                alert = any(s.alerted for s in states)
                dwell = max((source_t-s.since for s in states),default=0)
                colour = (45,102,237) if alert else (80,180,90)
                x1,y1,x2,y2 = (int(v) for v in det.box)
                cv2.rectangle(visual,(x1,y1),(x2,y2),colour,2)
                if states:
                    label=f"{det.label} #{det.track_id} | {dwell:.1f}s"
                    (label_w,label_h),baseline=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,.48,1)
                    label_x=max(0,min(x1,w-label_w-8))
                    label_y=max(label_h+10,y1-6)
                    for _ in range(len(label_rectangles)+1):
                        rectangle=(label_x,label_y-label_h-5,label_x+label_w+8,label_y+baseline+3)
                        overlap=any(rectangle[0]<r[2] and rectangle[2]>r[0] and rectangle[1]<r[3] and rectangle[3]>r[1] for r in label_rectangles)
                        if not overlap:
                            break
                        label_y=label_y-label_h-baseline-12 if label_y>2*label_h+baseline+22 else min(h-baseline-4,y2+label_h+12)
                    label_rectangles.append((label_x,label_y-label_h-5,label_x+label_w+8,label_y+baseline+3))
                    cv2.rectangle(visual,(label_x,label_y-label_h-5),(label_x+label_w+8,label_y+baseline+3),(30,36,28),-1)
                    cv2.putText(visual,label,(label_x+4,label_y),cv2.FONT_HERSHEY_SIMPLEX,.48,(255,255,255),1,cv2.LINE_AA)
            if engine.congested:
                cv2.putText(visual,"CONGESTION - REVIEW REQUIRED",(12,26),cv2.FONT_HERSHEY_SIMPLEX,.55,(45,102,237),2,cv2.LINE_AA)
            encoded = cv2.imencode(".jpg",visual,[cv2.IMWRITE_JPEG_QUALITY,83])[1].tobytes()
            while len(ring)>1 and ring[1][0] < source_t-cfg.evidence_before:
                ring.popleft()
            for clip in list(clips):
                clip["writer"].write_at(visual,min(source_t,clip["end"]))
                if source_t >= clip["end"]:
                    finish_clip(clip)
                    clips.remove(clip)
            for event in events:
                media_id = new_id()
                snapshot = f"evidence/{media_id}.jpg"
                thumbnail = f"evidence/{media_id}-thumb.jpg"
                clip_path = f"evidence/{media_id}.mp4"
                (directory/snapshot).write_bytes(encoded)
                x1,y1,x2,y2 = event["bbox"]
                pad_x,pad_y = max(20,(x2-x1)*.5),max(12,(y2-y1)*.5)
                crop = frame[max(0,int(y1-pad_y)):min(h,int(y2+pad_y)),max(0,int(x1-pad_x)):min(w,int(x2+pad_x))]
                if not cv2.imwrite(str(directory/thumbnail),crop if crop.size else frame):
                    raise RuntimeError("Không lưu được ảnh phương tiện. Kiểm tra dung lượng ổ đĩa.")
                event.update({"snapshot":snapshot,"thumbnail":thumbnail,"clip":clip_path,"clip_ready":False,"frame":frame_index,"clip_start_s":round(ring[0][0] if ring else source_t,3)})
                payload = store.add_event(job,event)
                writer = TimedVideoEncoder(directory/clip_path,w,h,effective_fps)
                for old_t,old_frame in ring:
                    writer.write_at(cv2.imdecode(np.frombuffer(old_frame,np.uint8),cv2.IMREAD_COLOR),old_t)
                writer.write_at(visual,source_t)
                clips.append({"writer":writer,"end":source_t+cfg.evidence_after,"payload":payload})
                event_count += 1
            ring.append((source_t,encoded))
            if annotated:
                annotated.write(visual)
            processed += 1
            elapsed = time.perf_counter()-started
            if elapsed-last_update >= .5 or processed == 1:
                atomic_bytes(directory/"preview.jpg",encoded)
                store.update_job(jid,progress=min(99.5,source_t/total*100) if total else 0,frames=processed,source_seconds=round(source_t,2),fps=round(processed/max(elapsed,.001),2),event_count=event_count,error="")
                last_update=elapsed
        if processed == 0 and not cancelled:
            raise RuntimeError("Không có khung hình hợp lệ để phân tích.")
        store.update_job(jid,status="finalizing")
    finally:
        if cap:
            cap.release()
        if annotated:
            annotated.close()
        for clip in clips:
            finish_clip(clip)
    elapsed = time.perf_counter()-started
    metrics = {"wall_seconds":round(elapsed,3),"model_seconds":round(model_seconds,3),"frames":processed,"detection_observations":detected_count,"event_count":event_count,"sampled_fps":round(processed/max(elapsed,.001),3),"source_seconds":round(source_t,3),"configured_sample_fps":cfg.sample_fps,"congested_frames":jam_frames,"device":manifest["device"],"peak_vram_mb":round(torch.cuda.max_memory_allocated()/1024**2,2) if cuda else None,"precision":"float32","cancelled":cancelled}
    (directory/"metrics.json").write_text(json.dumps(metrics,indent=2),encoding="utf-8")
    store.update_job(jid,status="cancelled" if cancelled else "completed",progress=store.job(jid)["progress"] if cancelled else 100,frames=processed,source_seconds=source_t,fps=round(processed/max(elapsed,.001),2),event_count=event_count,metrics=metrics,finished_at=now(),error="")


if __name__ == "__main__":
    data = Store(Path(sys.argv[1]))
    job_id = sys.argv[2]
    try:
        run(data,job_id)
    except Exception as exc:
        message = str(exc) if isinstance(exc,RuntimeError) and not any(x in str(exc).lower() for x in ("rtsp", "http", "password")) else f"Xử lý không thành công ({type(exc).__name__}). Kiểm tra nguồn, mô hình và tài nguyên rồi chạy lại."
        data.update_job(job_id,status="failed",error=message[:500],finished_at=now())
        sys.exit(1)
