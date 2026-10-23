"""Gradio demo - De 7: phat hien & canh bao xe dung/do trai phep.
Chay: python app.py  (local)  |  Colab/Kaggle: python app.py --share
1) Tai video  2) Click cac dinh polygon vung cam dung/do tren khung hinh dau  3) Chon backend  4) Chay.
"""
import argparse, json, os, subprocess, sys, time, uuid
import cv2, numpy as np, gradio as gr

ROOT = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(ROOT, "outputs", "app_runs")

def first_frame(video):
    if not video: return None, [], "Chưa có video"
    c = cv2.VideoCapture(video); ok, f = c.read(); c.release()
    if not ok: return None, [], "Không đọc được video"
    return cv2.cvtColor(f, cv2.COLOR_BGR2RGB), [], "Click lên ảnh để thêm đỉnh polygon (≥3 điểm)"

def draw(base, pts):
    im = base.copy()
    if pts:
        p = np.array(pts, np.int32)
        if len(pts) >= 3:
            ov = im.copy(); cv2.fillPoly(ov, [p], (255, 0, 0)); im = cv2.addWeighted(ov, 0.3, im, 0.7, 0)
        cv2.polylines(im, [p], len(pts) >= 3, (255, 0, 0), 2)
        for x, y in pts: cv2.circle(im, (x, y), 4, (255, 255, 0), -1)
    return im

def add_point(base, pts, evt: gr.SelectData):
    if base is None: return None, pts, "Tải video trước"
    pts = pts + [[int(evt.index[0]), int(evt.index[1])]]
    return draw(base, pts), pts, f"{len(pts)} điểm: {pts}"

def clear_pts(base): return (None if base is None else base), [], "Đã xoá polygon"

def to_h264(src, dst):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", dst], check=True)
    return dst

def run(video, pts, backend, model, max_dwell, stride, max_frames, reid, sam3_ckpt):
    if not video or len(pts) < 3: raise gr.Error("Cần video và polygon ≥3 điểm")
    out = os.path.join(RUNS, time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:4]); os.makedirs(out, exist_ok=True)
    zones = {"still_window_s": 2.0, "still_tol": 0.15, "lost_grace_s": 3.0, "jam_ratio": 0.6, "jam_min_vehicles": 4, "clip_s": 6,
             "zones": [{"name": "no_parking_1", "polygon": pts, "max_dwell_s": float(max_dwell)}]}
    zp = os.path.join(out, "zones.json"); json.dump(zones, open(zp, "w"))
    cmd = [sys.executable, os.path.join(ROOT, "src", "pipeline.py"), "--video", video, "--zones", zp, "--backend", backend,
           "--stride", str(int(stride)), "--out", out, "--save_video"]
    if int(max_frames) > 0: cmd += ["--max_frames", str(int(max_frames))]
    if backend == "yolo": cmd += ["--model", model]
    else: cmd += ["--amp", "bf16", "--offload_video", "--det_batch", "1", "--max_objects", "8"] + (["--sam3_ckpt", sam3_ckpt] if sam3_ckpt else [])
    if reid: cmd += ["--reid", reid]
    t0 = time.time(); r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    if r.returncode: raise gr.Error("Pipeline lỗi: " + r.stderr[-800:])
    m = json.load(open(os.path.join(out, "metrics.json"))); alerts = json.load(open(os.path.join(out, "alerts.json")))
    vid = to_h264(os.path.join(out, "annotated.mp4"), os.path.join(out, "annotated_h264.mp4"))
    rows = [[a["track_id"] % 100000, a["class"], a["zone"], a["stop_start_s"], a["alert_time_s"], a["dwell_s"], str(a["bbox"])] for a in alerts]
    snaps = [a["snapshot"] for a in alerts]
    clips = [to_h264(a["clip"], a["clip"].replace(".mp4", "_h264.mp4")) for a in alerts]
    summary = (f"Xong trong {time.time()-t0:.1f}s · {m['frames_processed']} frame · FPS model {m['fps_model']} · FPS e2e {m['fps_end2end']} · "
               f"thiết bị {m['device']} · VRAM {m['vram_peak_mb']} MB · {m['n_alerts']} cảnh báo · {m['jam_frames']} frame kẹt xe")
    return vid, rows, snaps, clips, summary

def build():
    with gr.Blocks(title="Đề 7 — Cảnh báo xe dừng/đỗ trái phép") as demo:
        gr.Markdown("## Đề 7 — Phát hiện & cảnh báo xe ô tô dừng/đỗ trái phép\nBaseline YOLO26 + ByteTrack (CPU) · lõi SAM 3.1 + DINOv3 (cần GPU)")
        base, pts = gr.State(None), gr.State([])
        with gr.Row():
            with gr.Column():
                video = gr.Video(label="1) Video", sources=["upload"])
                img = gr.Image(label="2) Click để vẽ vùng cấm dừng/đỗ", interactive=False, type="numpy")
                info = gr.Markdown(); clr = gr.Button("Xoá polygon")
            with gr.Column():
                backend = gr.Radio(["yolo", "sam3"], value="yolo", label="3) Backend")
                model = gr.Dropdown(["yolo26n.pt", "yolo26s.pt"], value="yolo26n.pt", label="YOLO model")
                max_dwell = gr.Slider(2, 120, value=5, step=1, label="Ngưỡng dừng (giây)")
                stride = gr.Slider(1, 15, value=2, step=1, label="Lấy mẫu: 1 frame mỗi N frame")
                max_frames = gr.Number(value=0, label="Giới hạn frame (0 = cả video)")
                reid = gr.Textbox(value="", label="DINOv3 re-ID (đường dẫn/HF id, để trống = tắt)")
                sam3_ckpt = gr.Textbox(value="", label="SAM 3.1 checkpoint (khi chọn sam3)")
                go = gr.Button("4) Chạy", variant="primary")
        summary = gr.Markdown()
        out_vid = gr.Video(label="Video kết quả (track + vùng + cảnh báo)")
        table = gr.Dataframe(headers=["track", "lớp", "vùng", "bắt đầu dừng (s)", "cảnh báo lúc (s)", "dwell (s)", "bbox"], label="Bảng cảnh báo")
        with gr.Row():
            gallery = gr.Gallery(label="Ảnh bằng chứng", columns=3, height=300)
            clips = gr.File(label="Clip bằng chứng", file_count="multiple")
        video.change(first_frame, video, [img, pts, info]).then(lambda i: i, img, base)
        img.select(add_point, [base, pts], [img, pts, info])
        clr.click(clear_pts, base, [img, pts, info])
        go.click(run, [video, pts, backend, model, max_dwell, stride, max_frames, reid, sam3_ckpt], [out_vid, table, gallery, clips, summary])
    return demo

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--share", action="store_true"); ap.add_argument("--port", type=int, default=7860)
    a = ap.parse_args()
    build().queue().launch(server_name="0.0.0.0", server_port=a.port, share=a.share, allowed_paths=[RUNS])
