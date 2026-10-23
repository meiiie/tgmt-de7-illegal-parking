# Đề 7 — Research: phát hiện & cảnh báo xe ô tô dừng/đỗ trái phép (cập nhật 2026-10-23)

Quy ước: mọi khẳng định có link nguồn thật; **(chưa kiểm chứng)** = chưa tự xác minh/đo lại. Số liệu benchmark là số do tác giả công bố, không phải ta đo (trừ mục 8).

## 0. Yêu cầu đề bài (de_bai.pdf)
- Đề 7: "Xây dựng hệ thống phát hiện và cảnh báo xe ô tô dừng đỗ trái phép". Báo cáo ≥20 trang + ≥20 slide/20 phút; chương trình phải chạy đúng.
- Môi trường: CUDA 13.2, PyTorch 2.11, Python 3.12; công cụ OpenCV/Python. Ghi chú đề: "Ultralytics chưa hỗ trợ attention tốt", "smaller is better".
- Chỉ thị Darren (qua coordinator): lõi Phase 2 **bắt buộc SAM 3.1 + DINOv3**; detector+tracker nhẹ chỉ làm baseline so sánh.

## 1. Detection / segmentation / tracking hợp nhất (open-vocabulary)
| Công nghệ | Điểm chính (nguồn) | Đánh giá cho đề 7 |
|---|---|---|
| **SAM 3** (Meta, 11/2025) | Detect+segment+track bằng text/exemplar prompt; video: masklet kiểu SAM 2, chi phí tăng tuyến tính theo số object, ~gần real-time với ~5 object trên H200 — https://ai.meta.com/blog/segment-anything-model-3/ ; paper arXiv:2511.16719 | Prompt "car" zero-shot, có mask → biết chính xác diện tích chiếm làn/vỉa hè |
| **SAM 3.1** (27/03/2026) | Object Multiplex (16 object/bucket), ~7× nhanh hơn ở 128 object, 16→32 FPS H100; H100 5 object compiled ~31 FPS, **~17.7 GB** — https://github.com/facebookresearch/sam3/blob/main/RELEASE_SAM3p1.md , https://github.com/facebookresearch/sam3/pull/503 | **Chọn làm lõi** (chỉ thị Darren). Rủi ro: VRAM trên T4 16 GB |
| Yêu cầu SAM 3 repo | Python ≥3.12, PyTorch ≥2.7, CUDA ≥12.6; flash-attn-3 tùy chọn; cần `hf auth login` — https://github.com/facebookresearch/sam3 | Khớp môi trường đề (Py3.12/PT2.11/CUDA13.2) |
| YOLOE-26 | Open-vocab YOLO26 + seg — https://docs.ultralytics.com/models/yoloe , https://arxiv.org/html/2602.00168v1 | Phương án dự phòng open-vocab nhẹ |
| Grounding DINO 1.5 / OWLv2 / LLMDet | Tổng hợp so sánh — https://zenn.dev/straydog/articles/d5a8713b8f59c7?locale=en (chưa kiểm chứng số liệu) | Không chọn: chậm hơn/không kèm tracker |

## 2. Detector real-time (baseline)
| Model | COCO AP50:95 | T4 TRT latency | Nguồn |
|---|---|---|---|
| YOLO26n / s / m / x | 40.9 / 48.6 / 53.1 / 57.5 | 1.7 / 2.5 / 4.7 / 11.8 ms | https://docs.ultralytics.com/models/yolo26 |
| RF-DETR N / M / 2XL (ICLR 2026) | 48.4 / 54.7 / 60.1 | 2.3 / 4.4 / 17.2 ms | https://github.com/roboflow/rf-detr/blob/develop/docs/learn/benchmarks.md , https://proceedings.iclr.cc/paper_files/paper/2026/file/5bed8703db85ab27dc32f6a42f8fbdb6-Paper-Conference.pdf |
| D-FINE-X | 59.3 | 11.5 ms | như trên (bảng RF-DETR) |
| DEIMv2-X (DINOv3 backbone) | 57.8 | 13.75 ms | https://arxiv.org/pdf/2509.20787 |
→ Baseline: **YOLO26n/s (Ultralytics 8.4.x)** vì pretrained COCO có class car/bus/truck/motorcycle, có sẵn tracker, chạy được CPU. RF-DETR là ứng viên baseline mạnh thứ hai.

## 3. Multi-object tracking
BoxMOT (MOT17 ablation HOTA): OccluBoost 71.10, BoT-SORT 69.68, BoostTrack 69.25, StrongSORT 68.05, Deep OC-SORT 67.95, ByteTrack 67.68, OC-SORT 66.44 — https://github.com/mikel-brostrom/boxmot/ ; hướng dẫn chọn tracker: https://mikel-brostrom.github.io/boxmot/trackers/
→ Baseline: ByteTrack (motion-only, nhanh); biến thể: BoT-SORT + ReID. Với xe đứng yên, lỗi chính là **mất ID khi bị che khuất** → đây là chỗ DINOv3 re-ID có giá trị.

## 4. DINOv3 (re-ID / embedding)
- Backbone ViT-S/16, S+/16, B/16, L, 7B; hỗ trợ trong `transformers` ≥4.56.0 — https://github.com/facebookresearch/dinov3 , https://huggingface.co/docs/transformers/model_doc/dinov3
- Dùng: embedding crop (theo mask SAM 3.1) của xe đang dừng → khi track mất rồi xuất hiện lại cùng vị trí, so cosine để **nối lại timer dwell** thay vì reset. (Ứng dụng này là đề xuất của ta, chưa có paper đo trên bài toán đỗ xe — chưa kiểm chứng hiệu quả.)

## 5. Phát hiện vật thể đứng yên / bỏ quên (stationary / abandoned object)
- Survey AOD (Luna et al., Sensors 2018, CC BY): khung chuẩn foreground → stationary detection → xác thực; dual-background (2 mô hình nền tốc độ học khác nhau) — https://pmc.ncbi.nlm.nih.gov/articles/PMC6308643/ ; code: http://www-vpu.eps.uam.es/publications/AODsurvey/
- Dual background + FSM (Heras Evangelio et al., 2011) — https://link.springer.com/article/10.1155/2011/858502
- Illegally parked vehicle bằng 1-D transformation trên i-LIDS, có bảng start/duration — http://michaelryoo.com/papers/AVSS2007_JongTaekLee.pdf
→ Dùng dual-background (OpenCV MOG2 2 learning-rate) như **tín hiệu phụ** xác nhận "đứng yên" độc lập với tracker.

## 6. Hệ thống dừng/đỗ trái phép gần đây
| Công trình | Phương pháp | Nguồn |
|---|---|---|
| Parking Time Violation (Sensors 2023) | YOLOv8 + DeepSORT/OC-SORT + timer; dữ liệu KMITL không công khai | https://pmc.ncbi.nlm.nih.gov/articles/PMC10346361/ |
| Event-level illegal parking (IJEECS 2026) | YOLOv8s vs SSD, ROI + ngưỡng đứng yên 30 s, không MOT; Recall 1.00/F1 0.89 trên **12 sự kiện**, 97 FPS | https://doi.org/10.11591/ijeecs.v43.i3.pp898-907 |
| Bogor thesis 2026 | YOLOv8 + tracking + thời gian dừng; mAP50 0.793; data không công khai | https://repository.ipb.ac.id/handle/123456789/175374 |
| ATG-PVD (drone, 2020) | 9,322 ảnh, nhãn IPC/moving/legal | https://ar5iv.labs.arxiv.org/html/2008.09305 , https://sites.google.com/view/atg-pvd/dataset |
Nhận xét: lĩnh vực chưa có benchmark chuẩn lớn; đánh giá thường ở **mức sự kiện** trên tập nhỏ → ta làm event-level P/R/F1 + sai số thời điểm.

## 7. Dữ liệu (kèm license)
| Nguồn | Nội dung | License / truy cập | Dùng |
|---|---|---|---|
| i-LIDS AVSS 2007 (PV Easy/Medium/Hard/Night) | 4 clip đỗ xe trái phép có GT, 720×576 25 Hz | "free for research and educational purposes", trích dẫn bắt buộc — https://eecs.qmul.ac.uk/~andrea/avss2007_d.html ; link gốc hỏng, mirror qua AODsurvey/FTP — https://opendata.stackexchange.com/questions/15334 (chưa kiểm chứng tải được) | **Test chính** (có GT sự kiện) |
| AI City 2021 Track 4 (Traffic Anomaly: crash/**stalled vehicle**) | video cao tốc, nhãn start/end anomaly | Tải tự do không cần form — https://www.aicitychallenge.org/ai-city-challenge-dataset-access/ ; điều khoản dùng: theo trang AI City (chưa kiểm chứng điều khoản cụ thể) | Test phụ: xe dừng trên làn; tắc thường **không** tính là anomaly (định nghĩa 2019: https://www.aicitychallenge.org/2019-data-sets/) → hữu ích để thử phân biệt kẹt xe |
| UA-DETRAC | 100 video, 140k frame, 1.21M box — https://arxiv.org/pdf/1511.04136v4.pdf | CC BY 3.0 theo VisionKG https://vision.semkg.org/licences.html ; mirror Kaggle ghi "Unknown" https://www.kaggle.com/datasets/bratjay/ua-detrac-orig (chưa kiểm chứng license gốc) | Đánh giá detector/tracker (xe dừng đèn đỏ = ca "kẹt" âm tính) |
| VisDrone | drone, 288 clip — https://github.com/visdrone/visdrone-Dataset | "academic use only" (https://fmi-data-index.github.io/visdrone2019.html); HF mirror ghi CC BY-SA 3.0 | Không ưu tiên (góc drone, khác camera cố định) |
| PKLot / CNRPark+EXT | ảnh bãi đỗ, nhãn chỗ trống/có xe — https://web.inf.ufpr.br/luizoliveira/research-interests/pklot/ , https://cnrpark.it/ | PKLot CC BY 4.0 (chưa kiểm chứng); CNRPark: xem trang | Chỉ để thử occupancy; không có sự kiện thời gian |
| Wikimedia: "MD-355 and MD-124 Gaithersburg MD 2022-07-30" | ngã tư thật, 66 s, 8K (dùng bản 480p) | **CC BY 4.0**, tác giả G. Edward Johnson — https://commons.wikimedia.org/wiki/File:MD-355_and_MD-124_Gaithersburg_MD_2022-07-30_11-07-03_1.webm | Smoke test CPU + tự gán nhãn sự kiện |
| intel-iot-devkit sample-videos car-detection.mp4 | 30 s, xe mô hình nhìn từ trên | CC BY 4.0 — https://github.com/intel-iot-devkit/sample-videos | Bỏ: YOLO26n chỉ phát hiện xe ở 3/38 frame mẫu |

## 8. Kết quả đo thực tế (box CPU 8 nhân, không GPU)
Xem plan.md §6 — số đo do ta chạy.
