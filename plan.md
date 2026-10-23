# Đề 7 — Plan: hệ thống phát hiện & cảnh báo xe dừng/đỗ trái phép (2026-10-23)

## 1. Công nghệ đã chọn
| Thành phần | Lựa chọn (phiên bản) | Lý do | Nguồn |
|---|---|---|---|
| Lõi detect+seg+track | **SAM 3.1** (`facebook/sam3.1`, file `sam3.1_multiplex.pt` 3.5 GB, repo `facebookresearch/sam3`) | Chỉ thị Darren; prompt "car"/"truck"/"bus" zero-shot, mask + ID nhất quán, Object Multiplex nhanh ~2× SAM 3 | https://github.com/facebookresearch/sam3/blob/main/RELEASE_SAM3p1.md |
| Re-ID sau che khuất | **DINOv3 ViT-S/16 hoặc B/16** (`facebook/dinov3-vit{s,b}16-pretrain-lvd1689m`, `transformers` ≥4.56) | Chỉ thị Darren; embedding mạnh không cần fine-tune để nối lại track của xe đứng yên | https://github.com/facebookresearch/dinov3 |
| Baseline so sánh | **YOLO26n/s** + **ByteTrack** (Ultralytics 8.4.184), biến thể BoT-SORT | Nhẹ, pretrained COCO, chạy được CPU | https://docs.ultralytics.com/models/yolo26 , https://github.com/mikel-brostrom/boxmot/ |
| Tín hiệu đứng yên phụ | OpenCV dual-background (MOG2 2 learning rate) | Kế thừa lit. abandoned-object, độc lập tracker | https://pmc.ncbi.nlm.nih.gov/articles/PMC6308643/ |
| Môi trường | Python 3.12, PyTorch 2.11, CUDA 13.2, OpenCV (theo đề); box hiện chạy Py 3.13/PT 2.14 CPU chỉ để smoke test | Đề bài | /workspace/tgmt/de_bai.pdf |
| Dữ liệu test | i-LIDS AVSS2007 PV (GT sự kiện), AI City 2021 Track 4 (stalled vehicle), UA-DETRAC (đèn đỏ/kẹt = âm tính), Wikimedia Gaithersburg CC BY 4.0 (smoke) | License xem research.md §7 | research.md |

**Thay đổi công nghệ so với đề xuất ban đầu (flag):** lõi chuyển từ YOLO+tracker → SAM 3.1 + DINOv3 (theo chỉ thị); YOLO26 hạ xuống baseline. Bỏ video intel car-detection (xe mô hình, YOLO gần như không phát hiện).

## 2. Kiến trúc
```
video (batch/thư mục) → chia chunk (vd 60 s, overlap 5 s) → lấy mẫu khung (vd 5 fps)
  ├─ Baseline: YOLO26 → ByteTrack → ID+box
  └─ Lõi:    SAM 3.1 video predictor (text prompt "car", re-detect mỗi chunk) → ID+mask
          → DINOv3 embedding mỗi track (crop theo mask, cập nhật EMA)
→ Logic chung (src/pipeline.py):
   - ROI cấm dừng/đỗ: polygon JSON (configs/*.json), điểm neo = đáy giữa box/mask, tỉ lệ mask nằm trong ROI ≥ 50% (lõi)
   - Đứng yên: dịch chuyển tâm trong cửa sổ 2 s < 0.15 × chiều cao xe (chuẩn hóa theo phối cảnh)
   - Dwell timer per zone; mất track ≤ grace s hoặc DINOv3 cosine ≥ τ tại vị trí cũ (IoU ≥ 0.5) → giữ timer
   - Phân biệt KẸT XE vs ĐỖ (mục 3)
   - Cảnh báo khi dwell ≥ max_dwell_s (theo zone) → alerts.csv/json + snapshot JPG + clip MP4 (ring buffer 6 s trước cảnh báo)
→ evaluate.py: P/R/F1 mức sự kiện, sai số thời điểm bắt đầu dừng, độ trễ cảnh báo; metrics.json: FPS, VRAM peak
```

## 3. Phân biệt kẹt xe với dừng/đỗ trái phép
1. **Tỉ lệ đứng yên toàn cảnh**: nếu ≥ 60% xe trong khung (≥ 4 xe) cùng đứng yên → trạng thái "jam", tạm hoãn cảnh báo (đã cài).
2. **Hàng đợi**: xe dừng có xe khác dừng ngay trước nó cùng làn → xếp hàng (đề xuất, chưa cài).
3. **Thoát kẹt**: khi luồng xung quanh chạy lại (tốc độ trung vị > ngưỡng) mà xe vẫn đứng → bắt đầu tính/cảnh báo (timer không reset trong jam, chỉ hoãn alert).
4. **Pha đèn**: ROI vạch dừng đèn đỏ đặt max_dwell lớn (vd 120 s) hoặc loại khỏi zone.
5. **Vị trí**: zone lề đường/vỉa hè (không phải làn chạy) ít chịu kẹt → ngưỡng thấp hơn.

## 4. Chạy trên Colab/Kaggle (phân tích)
| Vấn đề | Thực tế | Cách xử lý |
|---|---|---|
| VRAM | SAM 3.1 compiled H100, 5 object: ~17.7 GB, ~31 FPS (nguồn PR #503). Colab free/Kaggle: T4 16 GB (Kaggle có 2×T4 hoặc P100 16 GB) | Có nguy cơ OOM trên T4 → giảm số object (lọc trong ROI), frame sampling, chunk ngắn, offload video frames ra CPU (tùy chọn của predictor — chưa kiểm chứng) |
| fp16/bf16 | T4 (Turing) **không hỗ trợ bf16 native**; flash-attn-3 chỉ Hopper | Dùng fp16 autocast trên T4; bf16 chỉ khi có A100/L4 (Colab Pro, không free). Không dùng torch.compile ở lần đầu (thời gian compile dài) |
| Frame sampling | Dwell tính bằng giây → 2–5 fps là đủ (sai số ≤ 0.5 s) | `--stride`; SAM 3.1 chạy trên khung đã lấy mẫu |
| Video chunking | Bộ nhớ của SAM video tăng theo số frame trong session | Chunk 30–60 s, overlap 5 s; nối ID giữa chunk bằng IoU + DINOv3 cosine |
| Thời lượng phiên | Kaggle 30 h GPU/tuần, phiên ≤ 12 h; Colab free không đảm bảo | Batch video, lưu kết quả theo chunk để resume |
| Token | Checkpoint gated | Notebook đọc `HF_TOKEN` từ Kaggle Secrets / Colab `userdata`, không hardcode |

## 5. Đánh giá
- **Event-level**: TP nếu cảnh báo cùng video+zone, thời điểm nằm trong [GT start, GT end + 5 s]. Báo cáo P, R, F1, số FP do kẹt xe riêng.
- **Dwell/timing error**: |pred stop_start − GT start| (MAE, s) và độ trễ cảnh báo; so với bảng kết quả i-LIDS của Lee et al. 2007.
- **Tốc độ**: FPS model và FPS end-to-end (gồm I/O); **VRAM** peak `torch.cuda.max_memory_allocated`.
- **Detector/tracker** (UA-DETRAC): mAP50, HOTA/IDF1 (TrackEval) — tùy thời gian.
- Ma trận thí nghiệm: {YOLO26n+ByteTrack, YOLO26s+BoT-SORT, SAM 3.1, SAM 3.1+DINOv3} × {i-LIDS PV, AI City T4 subset, Gaithersburg}.

## 6. Kết quả đã chạy (box CPU, 8 nhân, máy dùng chung tải cao)
Xem bảng cập nhật cuối file.

## 7. Milestones
1. (xong) Research + plan + skeleton baseline CPU.
2. Tải i-LIDS PV + AI City 2021 T4 subset, viết GT JSON; chạy baseline có số liệu.
3. Notebook Kaggle: SAM 3.1 + DINOv3 trên T4, đo FPS/VRAM, so baseline.
4. Tinh chỉnh logic kẹt xe, ablation; báo cáo 20 trang + 20 slide.

## 8. Cần Darren/ người dùng quyết
1. **DINOv3 gated: token hiện CHƯA được duyệt** (GatedRepoError cho mọi repo dinov3) → cần vào https://huggingface.co/facebook/dinov3-vitb16-pretrain-lvd1689m bấm request access bằng tài khoản HF của token. SAM 3.1: token **đã có quyền**, checkpoint đã tải về cache box.
2. Kaggle (T4×2/P100) hay Colab? Kaggle cần **Kaggle API key** chỉ nếu muốn đẩy/chạy notebook tự động từ box; chạy tay trên web thì không cần.
3. Chấp nhận định nghĩa sự kiện + ngưỡng: đứng yên ≥ 2 s, cảnh báo khi dwell ≥ 8–60 s tùy zone?
4. Chấp nhận dùng i-LIDS (research/education only) và AI City 2021 T4 làm test chính?
5. Nếu SAM 3.1 OOM trên T4: cho phép giảm độ phân giải/lấy mẫu khung, hay dùng SAM 3.1 chỉ ở chế độ "xác minh" (chạy khi baseline nghi ngờ)?
