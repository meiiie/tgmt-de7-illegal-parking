# Chạy thử cục bộ ngày 06/11/2026

YOLO26s + ByteTrack đã chạy được trên GTX 1650 và trên giao diện Gradio. Luồng upload video, chọn model, vẽ vùng, xử lý, xem video, xem bảng cảnh báo, ảnh và clip bằng chứng đã hoạt động.

Bản đang mở tại [http://127.0.0.1:7867/](http://127.0.0.1:7867/). Dịch vụ chỉ nghe trên loopback. Tab Chrome được giữ mở để dùng tiếp.

## Kết quả quan sát

Video mẫu dài khoảng 20 giây, 854 × 480, 599 frame nguồn. Lấy một frame mỗi hai frame nên mỗi lượt xử lý 300 frame.

| Lượt | Vùng và ngưỡng | Kết quả |
|---|---|---|
| CLI | Polygon giao lộ từ cấu hình gốc, ngưỡng 8 giây | 300 frame, 2.861 dòng track, 88 ID, 0 cảnh báo |
| Giao diện | Polygon 8 đỉnh đang hiển thị, ngưỡng 5 giây | 300 frame, 1 cảnh báo cho track 7 tại giây 5 |

Giao diện báo hoàn tất trong 22,8 giây cho lượt thứ hai. Đây là một lượt chạy thử, không phải benchmark lặp lại hoặc phép so sánh tốc độ. Đồng hồ này bao gồm subprocess và chuyển H.264; không bao gồm thời gian chuẩn bị môi trường, tải dữ liệu và thao tác của người dùng.

Đã giải mã đủ 300 frame của video H.264 đầu ra và 76 frame của clip cảnh báo. Ảnh bằng chứng mở được. Video kết quả phát được trong trình duyệt, đã quan sát tiến trình tới giây 19.

Cảnh báo nằm trên xe đang chờ đèn trong vùng thử. Nó chứng minh timer và xuất bằng chứng hoạt động, chưa chứng minh phân biệt được đỗ trái phép với dừng hợp lệ. [Nguồn video, tác giả và giấy phép](demo-video-source.md).

## Các tệp bằng chứng

- [Bản ghi tổng hợp với lệnh, phiên bản, cấu hình và SHA-256](../outputs/local-smoke-2026-11-06/run-summary.json).
- [Ảnh giao diện sau khi chạy](../outputs/local-smoke-2026-11-06/browser-result.jpg).
- [Video kết quả](../outputs/app_runs/20261106_100541_f977/annotated_h264.mp4).
- [Clip cảnh báo](../outputs/app_runs/20261106_100541_f977/evidence/alert_7_150_h264.mp4).
- [Ảnh cảnh báo](../outputs/app_runs/20261106_100541_f977/evidence/alert_7_150.jpg).
- [Danh sách cảnh báo](../outputs/app_runs/20261106_100541_f977/alerts.json).
- [Polygon thực tế của lượt giao diện](../outputs/app_runs/20261106_100541_f977/zones.json).
- [Các package đã cài](../outputs/local-smoke-2026-11-06/requirements-resolved.txt).

Thư mục `outputs/`, video và trọng số được Git bỏ qua. Các liên kết bằng chứng này dùng cho bản trên máy hiện tại.

## Môi trường đã chạy

Commit mã sản phẩm là `10f94e8a3c93a4b4654653b246ae9875c91250d1`. Ba tệp `app.py`, `src/pipeline.py` và `src/evaluate.py` vẫn nguyên trạng.

| Thành phần | Phiên bản |
|---|---|
| Python | 3.12.2 |
| PyTorch | 2.11.0+cu126 |
| Torchvision | 0.26.0+cu126 |
| Ultralytics | 8.4.184 |
| Gradio | 5.49.1 |
| NumPy | 2.1.3 |
| opencv-python | 4.12.0.88 |
| lap | 0.5.12 |
| GPU | NVIDIA GeForce GTX 1650, 4 GB |

Kiểm tra phép toán CUDA đạt. `uv pip check` xác nhận 77 package không có xung đột dependency được khai báo.

PyTorch và Torchvision được sao chép sang `.venv` từ bộ cài Python 3.12 có sẵn trên máy để tránh tải lại 2,4 GB. Không sửa môi trường nguồn. [Chi tiết bootstrap](../outputs/local-smoke-2026-11-06/local-gpu-bootstrap.json). Console launcher của hai package này không được sao chép; demo dùng import Python và không cần chúng.

Trọng số YOLO26s tải từ release `v8.4.0` của `ultralytics/assets`. SHA-256 là `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`. Không fine-tune. Không đặt seed riêng cho lượt smoke này và không chia dữ liệu train, validation, test.

## Mở lại trên máy hiện tại

Nếu dịch vụ còn chạy, mở địa chỉ ở đầu tài liệu. Nếu đã dừng, chạy trong PowerShell.

```powershell
cd E:\Sach\Sua\ThayTuan\tgmt-de7-illegal-parking
.\run.ps1
```

Chọn video `data/gaithersburg_20s.mp4`, backend `yolo` và model `yolo26s.pt`. Vẽ polygon theo thứ tự quanh biên, tránh các cạnh cắt nhau. Giữ DINOv3 và SAM checkpoint trống khi thử baseline. Nhấn **4) Chạy**.

Để dựng môi trường mới hoàn toàn, cài CUDA PyTorch trước các gói demo.

```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu126
uv pip install --python .venv/Scripts/python.exe -r requirements-demo.txt
uv pip check --python .venv/Scripts/python.exe
```

Các lệnh dựng lại cần mạng. Lượt hiện tại dùng bản sao cục bộ cho hai package CUDA như đã ghi ở trên. Manifest `requirements-demo.txt` pin các package trực tiếp; file resolved trong bằng chứng ghi đủ phiên bản của lượt đã chạy.

## Các giới hạn còn nguyên

- Những lỗi timer và gộp sự kiện của [hồ sơ phân tích](preparation-2026-11-06.md) chưa được sửa trong lượt chạy thử.
- Polygon của lượt giao diện có cạnh cắt chéo. App vẫn chấp nhận; cần thêm kiểm tra polygon trước khi đánh giá độ chính xác.
- App hiển thị `amp=fp16` trong metrics nhưng không truyền `--half` cho YOLO. Không dùng trường này làm bằng chứng đã chạy FP16.
- Có cảnh báo deprecation của tham số `half`. Có một traceback Windows `ConnectionResetError` không chặn kết quả; giao diện vẫn hoàn tất và phát video.
- Chưa thử SAM 3.1, DINOv3, TensorRT, TTA hoặc ensemble.
- Chưa đánh giá test độc lập, camera trực tiếp hoặc độ chính xác trên tình huống đỗ trái phép thật.
- Cơ chế duyệt tự động chặn xóa hai thư mục uv tải dở `E:/DevCache/uv/.tmpE9iRF6` và `.tmpweSqmr`, chỉ trả `blocked by policy`. Hai thư mục được giữ nguyên. Việc này không cản trở demo.
