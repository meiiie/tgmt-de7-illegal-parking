# Bàn giao Curb — 08/11/2026

**Cập nhật sau yêu cầu đóng gói:** đã có bản cài Windows và kiểm tra cửa sổ desktop thật; xem [báo cáo desktop](desktop-verification-2026-11-08.md). Nội dung dưới đây giữ mốc kiểm tra web/GPU trước khi đóng gói.

Đã xây và chạy ứng dụng cục bộ cho giám sát dừng đỗ đường phố. Backend, suy luận và media đã chạy thật. Frontend đã build và được phục vụ, nhưng chưa kiểm tra tương tác/ảnh render do quyền trình duyệt bị tắt. Chưa gọi đây là bản đã nghiệm thu ngoài hiện trường.

Địa chỉ tại máy này: **http://127.0.0.1:8765/**. Launcher: `Start-Curb.cmd` hoặc `run-curb.ps1`. Mở lại launcher sẽ dùng phiên đang hoạt động nếu cùng cổng và thư mục dữ liệu. Bản Gradio và tài liệu nghiên cứu gốc vẫn có trong repo.

## Phạm vi đã hoàn thành

- Nhập video, khai báo camera RTSP/HTTP, kiểm tra hình ảnh, quản lý nguồn và lưu trữ/khôi phục nguồn.
- Nhiều vùng polygon có kiểm tra hình học, sửa điểm, ngưỡng dừng, loại xe, bật/tắt, mức theo dõi, lọc dấu hiệu ùn xe theo từng vùng.
- Quy tắc theo giờ/ngày, kể cả qua nửa đêm. Video cần timestamp gốc trước khi chạy quy tắc theo giờ.
- Hàng đợi một worker, tiến độ và preview, hủy khi đang chạy, lỗi nguồn, thử lại kết nối camera có giới hạn, đánh dấu gián đoạn khi khởi động lại.
- Ảnh toàn cảnh và crop phương tiện, clip H.264 trước/sau, video H.264 toàn lượt đối với tệp nhập. Clip camera giữ đúng thang thời gian nguồn khi nhịp frame không đều.
- Duyệt có ghi chú/lịch sử, kiểm tra phiên bản hồ sơ để tránh ghi đè, tìm/lọc/phân trang, báo cáo, CSV/JSON và ZIP bằng chứng.
- Cài đặt, chẩn đoán, sao lưu/khôi phục sang thư mục mới, dọn thủ công dữ liệu hết hạn, chặn hai phiên dùng chung dữ liệu.
- Hướng dẫn cài/chạy, script kiểm tra lặp lại và workflow CI. Chưa đẩy Git nên CI từ xa chưa chạy.

Chọn React/TypeScript + FastAPI/SQLite + Python GPU. Tauri không được đưa vào bản này vì chưa mang lại chức năng vận hành cần thiết so với nền Python đã kiểm chứng; Rust compiler trên máy hiện cũng không hoạt động. Dịch vụ chỉ bind loopback.

## Phiên bản và dữ liệu

Commit nền: `10f94e8a3c93a4b4654653b246ae9875c91250d1`, chưa tạo commit mới.

Python 3.12.2, torch 2.11.0+cu126, ultralytics 8.4.184, OpenCV 4.12.0.88, FastAPI 0.162.0, Pydantic 2.11.10, React 19.3.1, TypeScript 5.9.3, Vite 8.3.6. GPU: NVIDIA GeForce GTX 1650 4 GB. Phiên bản frontend đầy đủ trong `web/package-lock.json`, Python đã cài trong `outputs/rebuild-2026-11-08/requirements-resolved.txt`.

Video nguồn là đoạn 20 giây từ Wikimedia, 854×480, khoảng 29,97 FPS; nguồn/giấy phép tại [demo-video-source.md](demo-video-source.md). SHA-256 đầu vào: `513586ea1ee18969967ebb5bdf62c3d8e472be1e191ef8e816c7df4ba6809ac0`. YOLO26s SHA-256: `646f8bc3fe0a656803d95c294f7852321748cb29d13466a1af8862e2db384a1b`.

Seed 0, YOLO26s + ByteTrack, float32, confidence 0,30, kích thước suy luận 640, lấy mẫu 5 FPS; cửa sổ đứng yên 2 giây, dung sai 0,18 chiều cao box, diện tích tối thiểu 200 px². Vùng thử normalized `[[0.132,0.43],[0.235,0.43],[0.235,0.62],[0.132,0.62]]`, ngưỡng 5 giây. Đây là dữ liệu kiểm thử phát triển, không phải test độc lập.

## Kết quả đã quan sát

| Kiểm tra | Kết quả |
|---|---|
| Unit/domain/API/media | **27/27 đạt**; polygon, vòng đời dừng, mất/đổi ID, vùng chồng nhau, lớp xe, ùn xe, giờ qua đêm, snapshot, queue/cancel, conflict khi duyệt, sao lưu/khôi phục, path/origin, singleton và prerequisites |
| Tích hợp thật | **24/24 đạt** qua `scripts/verify_curb.py`; không mock detector |
| Build frontend | TypeScript strict, kiểm tra import/parameter không dùng, Vite production: đạt |
| Dependencies Python | `uv pip check`: 77 gói tương thích |
| Phục vụ web | HTML, JavaScript và CSS trả HTTP 200 |
| Launcher | `powershell.exe -NoProfile -File run-curb.ps1 -NoBrowser` nhận lại phiên hiện có, trả mã 0 |
| Detector thiết kế Impeccable | Trả `[]`, không có finding cơ học; không thay thế kiểm tra render |
| Git diff | `git diff --check` đạt; có thông báo chuyển LF/CRLF trên Windows |
| Tương tác/render UI desktop và mobile | **Chưa chạy** — Work settings tắt quyền trình duyệt cục bộ |
| RTSP hiện trường, nhiều giờ liên tục, fresh install trên máy khác, CI từ xa | **Chưa chạy** |

Lượt video cuối `bfb671170e1a41d1842b19561ae94175`: 100 frame lấy mẫu, 770 quan sát detection, 1 cảnh báo ở khoảng giây 5,005; thời gian worker toàn lượt **10,315 giây**, đo ngoài từ gửi request đến nhận hoàn tất **10,638 giây**, tốc độ frame lấy mẫu **9,695 FPS**, VRAM tensor đỉnh **93,98 MB**. Đây là một smoke test, không phải benchmark hay độ trễ camera được bảo đảm. VRAM này không phải tổng bộ nhớ GPU tiến trình/driver.

Video toàn lượt được giải mã đủ **100/100 frame**, H.264/yuv420p, 854×480, 20,00 giây. Clip video mẫu giải mã **41/41 frame**, dài 8,20 giây. Yêu cầu `Range: bytes=0-127` trả 206 và đúng 128 byte.

Camera kiểm thử là HTTP MJPEG phát lại chính video mẫu trên loopback: lượt 10 giây nguồn xử lý 31 frame và tạo 1 sự kiện. Clip dài **7,20 giây**, khoảng thời gian nguồn tương ứng **7,171 giây**. Hủy khi đang chạy kết thúc ở trạng thái `cancelled`. Ngắt luồng dẫn tới `failed` với thông báo sau 3 lần kết nối lại, không báo hoàn tất giả.

Đã kiểm tra ảnh bằng chứng thật: xe trong vùng thử đang chờ đèn đỏ. Nhãn trên ảnh được giới hạn cho phương tiện trong vùng và có nền tối để giảm chồng chữ. Các cảnh báo thử được ghi chú/bỏ qua; để lại một cảnh báo mẫu mới cho người dùng mở và thử quy trình duyệt. Nguồn `[Kiểm thử]` được lưu trữ, lịch sử vẫn giữ để truy vết. Số liệu hiện trong ứng dụng là dữ liệu thử thật, không phải số liệu vận hành đường phố của người dùng.

## Artifact

- `outputs/rebuild-2026-11-08/verification.json`: 24 kết quả tích hợp, job/config/metrics và kiểm tra giải mã.
- `outputs/rebuild-2026-11-08/final-visual-smoke.json`: lượt video sau thay đổi nhãn trên bằng chứng.
- `outputs/rebuild-2026-11-08/unit-tests.log`: kết quả 27 tests.
- `outputs/rebuild-2026-11-08/final-summary.json`: môi trường, frontend, sức khỏe, trạng thái kiểm chứng và đối chiếu hash mã cuối.
- `outputs/curb/jobs/<id>/manifest.json`: hash/phiên bản/cấu hình từng lần chạy; media và metrics cùng thư mục.
- `docs/design/curb-concept.png`: **mockup imagegen**, không phải ảnh chụp ứng dụng chạy thật.

Lệnh lặp lại đầy đủ ở [README](../README.md). Chạy kiểm thử tích hợp sẽ tạo thêm dữ liệu có nhãn kiểm thử.

## Tự review và phần chưa nghiệm thu

Thực hiện toàn bộ trong một agent theo yêu cầu; các lượt đọc, xây và tự review được làm tuần tự. Không phải review độc lập bởi agent khác. Pstack giúp tách Source/Job/Stop/Event và kiểm chứng từng đơn vị. Impeccable dùng cho cấu trúc Operate, kiểm tra cơ học và tiêu chí UI. Ảnh imagegen đã được lưu vào dự án; frontend được triển khai bằng component thật.

Trạng thái review hình ảnh: **`disposition: recapture`**. Chưa có ảnh desktop/mobile để chấm render. Cả Chrome và in-app browser đều trả đúng lỗi `Local browser use is disabled in Work settings`. Không dùng trình duyệt khác hay automation ngoài công cụ để đi vòng thiết lập này. Cần bật quyền rồi kiểm tra thực các luồng upload, vẽ/kéo vùng, lưu, chạy/hủy, phát clip, duyệt, lọc/xuất và layout ở 1440/390 px.

Chưa có camera RTSP thật hoặc dữ liệu đường phố Việt Nam độc lập. Chưa đo theo lớp/tình huống ngày–đêm/mưa/che khuất, false alarm theo giờ hoặc độ trễ capture-to-alert thực. Những phần này cần hoàn tất trước khi chấp nhận vận hành hiện trường. Bản này không có OCR biển số, xác thực nhiều người hoặc triển khai mạng. Không tự động xử phạt.

Mô hình Ultralytics có lựa chọn giấy phép AGPL-3.0/Enterprise; xem [trang chính thức](https://www.ultralytics.com/license) trước khi chọn cách phát hành thương mại. Không sửa giấy phép repo trong lượt này.

Không commit, push, deploy công khai hoặc huấn luyện mô hình trong lượt xây dựng.
