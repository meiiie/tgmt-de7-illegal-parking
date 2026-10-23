# Đề 7 - Phát hiện và cảnh báo ô tô dừng đỗ trái phép (SAM 3.1 + DINOv3)

Học phần Thị giác máy tính nâng cao.

## Demo Gradio (`app.py`)
Tải video → click các đỉnh polygon vùng cấm dừng/đỗ trên khung hình đầu → chọn backend → Chạy. Kết quả: video có track/vùng/cảnh báo, bảng cảnh báo (thời điểm bắt đầu dừng, thời điểm cảnh báo, dwell), ảnh và clip bằng chứng.

### Chạy local (CPU, baseline YOLO26 + ByteTrack)
```bash
python3.12 -m venv .venv && . .venv/bin/activate
pip install ultralytics lap gradio opencv-python "transformers>=4.56"   # ffmpeg cần có trong PATH
python app.py            # mở http://127.0.0.1:7860
```
### Colab
```python
!git clone https://github.com/meiiie/tgmt-de7-illegal-parking.git && %cd tgmt-de7-illegal-parking
!pip -q install ultralytics lap gradio "transformers>=4.56"
!pip -q install "git+https://github.com/facebookresearch/sam3.git@7f473cf"   # chỉ khi dùng backend sam3 (GPU)
!python app.py --share    # in ra link *.gradio.live
```
### Kaggle (GPU T4, Internet ON)
Thêm dataset `holilihu/de7-weights` (SAM 3.1 + DINOv3), ghép checkpoint: `cat /kaggle/input/**/sam31_part_* > weights/sam3.1_multiplex.pt`, rồi `python app.py --share` và điền đường dẫn checkpoint ở ô "SAM 3.1 checkpoint". Không cần HF token.

Ảnh chụp thật: `docs/screenshots/01_zone_drawn.png`, `docs/screenshots/02_results.png`.
