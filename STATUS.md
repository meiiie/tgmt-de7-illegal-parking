# STATUS — Đề 7 (cập nhật 2026-10-23 ~20:50 UTC+7)

## Xong
- Phase 1: `research.md`, `plan.md` (có link nguồn, license dữ liệu, phân tích Colab/Kaggle).
- `src/pipeline.py`: backend `yolo` (baseline YOLO26+ByteTrack/BoT-SORT) và `sam3` (SAM 3.1 multiplex, chunk video, text prompt); re-ID DINOv3 tuỳ chọn; ROI polygon JSON, dwell timer, chặn cảnh báo khi kẹt xe, alerts CSV/JSON + snapshot JPG + clip MP4; metrics.json (FPS, VRAM). `src/evaluate.py`: P/R/F1 mức sự kiện, MAE thời điểm.
- Notebook `notebooks/de7_sam31_dinov3.ipynb` (Kaggle/Colab, token đọc từ Secrets/userdata).
- Token: HF_TOKEN có quyền SAM 3.1 + DINOv3 (đã tải về cache box); Kaggle API hoạt động (user holilihu).
- Dataset Kaggle private: `holilihu/de7-code` (ready); `holilihu/de7-weights` (đang upload).

## Số đo thật (box CPU 8 nhân dùng chung, tải 30–50)
| Run | Video | Frames | FPS model | FPS e2e | Alerts | Ghi chú |
|---|---|---|---|---|---|---|
| YOLO26n+ByteTrack, CPU, stride 2 | Gaithersburg 480p (66 s) | 987 | 17.07 | 16.52 | 0 | đúng: video không có xe dừng trong ROI ngã tư (true negative) |
| YOLO26n, CPU | intel car-detection (toy) | 377 | 28.95 | 26.98 | 0 | xe mô hình, detector chỉ bắt 3/38 frame mẫu → bỏ |
Các run CPU dài hơn (yolo26s, +DINOv3) bị timeout do box quá tải → chuyển sang Kaggle GPU.

## Kaggle T4 (Tesla T4 15 GB, torch 2.11.0+cu128) — Gaithersburg 480p, stride 3 (10 fps), 658 frame
| Config | FPS model | FPS e2e | VRAM peak MB | Alerts |
|---|---|---|---|---|
| YOLO26n + ByteTrack | 34.62 | 27.47 | 63.1 | 0 |
| YOLO26s + BoT-SORT | 33.17 | 26.45 | 103.9 | 0 |
| YOLO26s + ByteTrack + DINOv3-S re-ID | 63.19 | 46.26 | 177.4 | 0 |
| SAM 3.1 (chunk 150, 16 obj, frames trên GPU) | — | — | **OOM** (>14.3 GB) | — |
(0 alert = đúng: video không có xe dừng trong ROI; FPS chênh do warm-up/GPU dùng chung — chưa lặp lại)
v6 (det_batch 2/1, bf16 autocast, offload frames): qua detector OK, nhưng tracker lỗi `RuntimeError: No available kernel` trong `scaled_dot_product_attention` (bf16 trên T4 sm75 không có flash/mem-efficient kernel) → fix: ép SDPA backend MATH quanh propagate.
Baseline v6: YOLO26n 34.28/27.04 FPS 63 MB; YOLO26s+BoT-SORT 31.03/24.91 103 MB; YOLO26s+DINOv3 54.25/39.54 176 MB.
Fix SAM 3.1 trước đó: offload frames ra CPU + chunk 60→16 frame + max_objects 16→8 (kernel v5 đang chạy). Bug upstream sam3@7f473cf `offload_state_to_cpu` đã vá bằng wrapper.

## Đang làm / tiếp theo
1. Kaggle T4: chạy 5 cấu hình (yolo26n, yolo26s+BoT-SORT, yolo26s+DINOv3, SAM3.1 fp16, SAM3.1+DINOv3) → bảng FPS/VRAM.
2. Dữ liệu có sự kiện dương: AI City 2021 Track 4 (14 GB, Google Drive, tải thẳng trong kernel Kaggle); i-LIDS AVSS2007: link gốc/FTP/AODsurvey **không truy cập được** từ box.
