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

## 22:15 UTC+7 — Kaggle
- Đang chạy (push 22:08–22:09, trước quy tắc 1 kernel): `holilihu/de7-sam31-dinov3` v7 (fix SDPA FLASH→EFFICIENT/MATH) và `holilihu/de7-aic21-eval` v1 (AIC21 T4: 6 video dương + 3 âm, YOLO26s, YOLO26s+DINOv3, SAM3.1+DINOv3).
- Kaggle CLI 2.2.5 không có lệnh cancel; SDK có `cancel_kernel_session` nhưng cần kernel_session_id mà API status/get_kernel không trả về → không tự dừng được kernel.
- Quy tắc: tối đa 1 kernel de7 GPU; không push mới cho đến khi Đề 14/12 chạy xong; dừng kernel de7 >2h. Trọng số chỉ từ dataset `holilihu/de7-weights` (dùng chung Đề 12/14 — không xoá/sửa). Không dùng HF/Secrets trong kernel.

## 22:25 UTC+7
- v7 `de7-sam31-dinov3` COMPLETE: SDPA hết lỗi kernel nhưng cross-attention rơi về MATH → OOM (cần 4.82 GiB). Baseline v7: YOLO26n 27.87/23.67 FPS 63 MB; YOLO26s+BoT-SORT 33.91/27.70 103 MB; YOLO26s+DINOv3 62.33/45.87 176 MB.
- Fix kế tiếp (đã code, chưa chạy): ép q,k,v bf16→fp16 trong attention của decoder SAM3 trên GPU sm<80 để dùng kernel EFFICIENT.
- `de7-aic21-eval` v1 ERROR: đọc nhầm ReadMe thay vì train-anomaly-results.txt (đã sửa). Tải 15.1 GB zip trên Kaggle mất ~3 phút; 100 video train.
- Kernel tiếp theo (gộp): `holilihu/de7-aic21-eval` — SAM3.1 FPS/VRAM trên Gaithersburg + AIC21 (baseline 9 video, SAM 4 video), budget 100 phút. CHỜ Đề 14/12 chạy xong mới push.
- 22:48 UTC+7: push `holilihu/de7-aic21-eval` v2 (Đề 12 đã COMPLETE, Đề 14 đang chạy → de7 dùng 1 slot). Hạn dừng nếu >2h: 00:48.

## 23:28 UTC+7 — `de7-aic21-eval` v2 COMPLETE (≈40 phút)
AIC21 Track 4 train: 6 video dương (2, 9, 11, 14, 33, 35) + 3 âm (58, 62, 7), 15 phút/video, stride 15 (2 fps), ROI toàn khung, dwell ≥ 20 s, tol 30 s. Kết quả: `results/aic21_table.csv`.
| Config | Video | Frames | FPS model | FPS e2e | VRAM MB | TP | FP | FN | P | R | F1 | MAE bắt đầu (s) | Độ trễ cảnh báo (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| YOLO26s + ByteTrack | 9 | 15079 | 55.50 | 34.22 | 100.0 | 4 | 16 | 3 | 0.200 | 0.571 | 0.296 | 19.38 | 36.88 |
| YOLO26s + ByteTrack + DINOv3-S | 9 | 15079 | 57.73 | 33.61 | 174.9 | 5 | 35 | 2 | 0.125 | 0.714 | 0.213 | 32.40 | 45.10 |
| SAM 3.1 + DINOv3 | 4 | — | — | — | OOM | — | — | — | — | — | — | — | — |
Nhận xét: FP chủ yếu do xe đứng yên hợp lệ/xa (ROI toàn khung) và re-ID nối timer quá dễ (DINOv3 tăng recall nhưng tăng FP). Cần ROI theo làn/lề và ngưỡng re-ID chặt hơn.
SAM 3.1: load OK (3734 MB VRAM sau load), nhưng propagate vẫn OOM trên T4: cross-attention cần 4.82 GiB (shim fp16 chưa có tác dụng → vẫn rơi về MATH) và chỗ khác 1.01 GiB khi đã dùng 13.4 GB. **Blocker: SAM 3.1 video multiplex chưa chạy được trong 15 GB T4.**
- 23:29 UTC+7: SAM-only kernel v3 đã chuẩn bị (attention chia block + fp16, max_objects 8, det_batch 1) nhưng CHƯA push: Đề 14 vừa ERROR và có thể đang chờ slot → chờ coordinator xác nhận.

## 23:35 UTC+7 — Re-score offline AIC21 (từ alerts v2, không chạy GPU)
Không lưu track từng frame → chỉ lọc lại được trên alerts. Phát hiện: phần lớn FP là **cảnh báo lặp** cùng một xe/vị trí (ID tracker đổi sau che khuất). Gộp theo bbox IoU≥0.3 trong cùng video (= 1 sự cố) + bỏ bbox < 200 px² (xe quá xa):
| Config | Raw P/R/F1 | Dedup IoU0.3 | Dedup + min_area 200 | Dedup + min_area 400 |
|---|---|---|---|---|
| YOLO26s+ByteTrack | 0.200/0.571/0.296 (FP 16) | 0.400/0.571/0.471 (FP 6) | 0.444/0.571/0.500 (FP 5) | 0.571/0.571/0.571 (FP 3) |
| +DINOv3 (thr 0.6) | 0.125/0.714/0.213 (FP 35) | 0.312/0.714/0.435 (FP 11) | 0.385/0.714/0.500 (FP 8) | 0.417/0.714/0.526 (FP 7) |
Lưu ý: ngưỡng min_area chọn trên chính tập test (7 sự kiện) → có thiên lệch; chỉ dedup là quy tắc không tinh chỉnh. Mặc định mới trong pipeline: dedup_iou 0.3, min_area 200, reid_thr 0.75 (chặt hơn 0.6). ROI làn/lề theo từng video: cần ảnh khung hình AIC (chỉ có trên Kaggle) → chưa vẽ được.
- 00:09 UTC+7: Darren duyệt → push `de7-aic21-eval` v3 (SAM-only + thumbnails). Hạn dừng 02:09.

## 00:15 UTC+7 — Gradio app (`app.py`) chạy end-to-end trên CPU box
- Video: Gaithersburg clip 20 s (giây 40–60, CC BY 4.0), YOLO26n + ByteTrack, stride 2 → 300 frame, **13.5 s**, FPS model 30.91 / e2e 26.96, 1 cảnh báo (track 5, car, dừng từ 0 s, cảnh báo 5 s, ngưỡng 5 s).
- Trung thực: vùng vẽ ở làn chờ đèn đỏ phía xa; xe trigger là xe **dừng đèn đỏ** (không phải đỗ trái phép) — chỉ để chứng minh luồng alert/snapshot/clip. Chưa có clip license rõ có xe đỗ trái phép thật.
- Screenshot thật (Playwright + Chrome headless): `docs/screenshots/01_zone_drawn.png`, `docs/screenshots/02_results.png`.
- 02:10 UTC+7 (24/10): `de7-aic21-eval` v3 vẫn RUNNING quá hạn 02:09 (~2h kể từ 00:09) → cần dừng thủ công trên Kaggle web UI (CLI không có lệnh cancel). Chưa có kết quả SAM 3.1.
