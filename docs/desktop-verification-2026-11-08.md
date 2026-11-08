# Curb Desktop — kiểm chứng Windows ngày 08/11/2026

Người dùng yêu cầu ảnh chụp ứng dụng thật và bộ cài có thể mở bằng biểu tượng. Tự thực hiện theo pstack, kiểm tra tuần tự; không dùng subagent. Commit gốc `10f94e8a3c93a4b4654653b246ae9875c91250d1`; thay đổi cục bộ chưa commit.

## Kiến trúc và cách mở

- WinForms .NET Framework 4.8 + WebView2 SDK 1.0.4314.35; runtime WebView2 157.0.4341.42 trên máy kiểm tra.
- CPython embeddable 3.12.10 x64, torch 2.11.0+cpu, torchvision 0.26.0+cpu, Ultralytics 8.4.184, OpenCV 4.12.0.88; 52 dependency Python được khóa.
- React/FastAPI/SQLite và quy trình duyệt giữ nguyên. Cài kèm hai mô hình YOLO26, FFmpeg, video mẫu và mã nguồn ứng dụng.
- Inno Setup tạo bộ cài per-user, shortcut Desktop/Start menu và trình gỡ. Kiểm tra .NET 4.8; WebView2 bootstrapper chính thức chạy khi thiếu runtime.
- Trên máy này: ứng dụng tại `C:/Users/Admin/Curb/app/Curb.exe`; dữ liệu mặc định `C:/Users/Admin/Curb/data`. Dữ liệu kiểm thử nằm riêng ở `C:/Users/Admin/Curb/verification`.
- Dịch vụ bind 127.0.0.1 trên cổng tự chọn. Host quản lý stdin, chờ worker đóng và dùng Windows Job Object quản lý cây tiến trình. Không cần chạy terminal.

## Bằng chứng thực tế

Ảnh cửa sổ native sau khi cài cập nhật: [tổng quan](screenshots/desktop-overview.jpg) và [hồ sơ bằng chứng](screenshots/desktop-evidence.jpg). Đây là ảnh chụp ứng dụng chạy thật, không phải mockup imagegen.

- Build TypeScript/Vite và C# thành công. 28 kiểm tra logic/API/media đạt.
- Bộ cài đã cài thành công, mã thoát 0, không yêu cầu khởi động Windows. Có shortcut `Curb.lnk` trên Desktop và bản ghi gỡ cài đặt v1.0.0.
- Bản đã cài được khởi động với PATH chỉ gồm `C:/Windows/System32;C:/Windows`, bỏ PYTHONHOME/PYTHONPATH. Backend dùng `app/runtime/python.exe`, không dùng `.venv` của repo.
- 24/24 phép thử tích hợp đạt: nhập video, ROI, xử lý CPU thật, ảnh/thumbnail/clip, byte range, giải mã H.264, duyệt/lịch sử/xung đột, CSV/JSON/ZIP, từ chối video hỏng, camera HTTP phát lại, hủy, mất kết nối và sao lưu.
- Job CPU `24c644155eb5406a86b036d9befcc5ee`: 100 frame lấy mẫu, 770 quan sát phương tiện, một cảnh báo; 19,953 giây nguồn; 32,254 giây toàn lượt, 22,715 giây suy luận. Lượt thử stage trước đó mất 23,434 giây; tải nền khiến thời gian thay đổi, không dùng lượt nhanh nhất làm cam kết hiệu năng.
- Camera HTTP `e437241e239e453bb101ea6f6244ade6`: 40 frame, một cảnh báo; 10,094 giây nguồn; 21,118 giây toàn lượt kể cả khởi tạo. Đạt phép đo thời gian clip.
- Job hủy dừng ở 8 frame. Job ngắt camera chủ động báo lỗi sau retry; đây là ca kiểm thử có chủ đích.
- Đã thao tác UI thật: mở ứng dụng, nạp mẫu, chạy phân tích, xem clip, xuất JSON bằng hộp thoại Windows, ghi lý do bỏ qua và kiểm tra lịch sử. Đóng cửa sổ kết thúc host/backend, log ghi shutdown hoàn tất.

Artifact máy này: `outputs/rebuild-2026-11-08/desktop-integration.json`, `desktop-stage-smoke.json`, `desktop-unit-tests.log`, `desktop-ui-export.json`, `desktop-install.log`. Mỗi lượt suy luận giữ manifest phiên bản, seed 0 và hash mã/model/dữ liệu trong thư mục job.

Bộ cài cuối: `C:/Users/Admin/Curb/Curb-Setup-1.0.0-x64.exe`, 307.352.972 byte; SHA-256 `4f392703ca6549dbda54cc95e333c66eddf912acf14fa6ec071529f44daf69f1`. Đã cài cập nhật lại từ đúng bộ cài này, mã thoát 0; log `desktop-upgrade.log`. Bản cuối được mở ở thư mục dữ liệu mặc định, nạp mẫu và chạy lại; kết quả tại `desktop-final-smoke.json`. Lịch sử kiểm thử riêng vẫn còn sau cập nhật.

## Hai lỗi đóng gói đã sửa

1. Worker kế thừa stdin mà desktop host đang theo dõi, làm chậm khởi động console con. Worker và lệnh không tương tác được gắn stdin DEVNULL; camera probe vẫn dùng pipe riêng.
2. Lần suy luận camera đầu có chi phí khởi tạo, tạo khoảng trống trong đồng hồ nguồn. Khởi tạo detector/tracker bằng ảnh rỗng trước khi mở camera và bắt đầu đồng hồ live. Giữ nguyên ngưỡng test 10 giây, hơn 20 frame, có cảnh báo và clip đúng thời gian. Kết quả trước sửa (11 frame, chưa cảnh báo) được giữ trong `desktop-integration-before-warmup.json`.

## Giới hạn của lần kiểm tra

Bản đóng gói dùng CPU, không kèm CUDA. Bản phát triển GPU trước đây vẫn riêng. Camera HTTP là fixture phát lại, chưa kiểm tra camera RTSP ngoài hiện trường. Không suy ra chất lượng nhận biết vi phạm từ video mẫu có xe chờ đèn. Bộ cài chưa ký chứng thư và chưa được kiểm tra trên máy Windows sạch khác. WebView2 và .NET đã có trên máy này, nên nhánh tự cài WebView2 còn chưa được thử trên máy thiếu runtime. Giao diện được kiểm tra trên desktop Windows; chưa nghiệm thu mobile.
