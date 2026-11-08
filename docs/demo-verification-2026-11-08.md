# Thay video mẫu Curb ngày 08/11/2026

Yêu cầu: tự tìm video phù hợp hơn cho giám sát dừng đỗ đường phố, thay mẫu chờ đèn của bản desktop. Tự thực hiện theo pstack adapter, không dùng subagent. Commit gốc `10f94e8a3c93a4b4654653b246ae9875c91250d1`; thay đổi cục bộ chưa commit.

## Lựa chọn và phạm vi

Mẫu mới là 30 giây đầu của **MERL Street Scene Test006**, camera cố định nhìn xuống đường phố. Ba ô tô đỗ sát lề phải, phương tiện khác di chuyển trên làn đường. Video có giấy phép CC BY-SA 4.0 và được phân phối lại cùng ghi nguồn, giấy phép, mô tả biến đổi. [Nguồn và tái tạo](demo-video-source.md).

Đã xem các nguồn Wikimedia: nhiều clip là timelapse, camera lia hoặc xe chờ đèn. Clip Stritarjeva có xe đỗ nhưng camera lia nên bị loại. VIRAT ground có điều kiện hạn chế phân phối nên không chọn làm tài nguyên bộ cài. Street Scene được lấy từ bản phát hành chính thức trên Zenodo, không từ video detector có box dựng sẵn.

Đã xem mẫu frame các sequence Test001–Test006 để chọn cảnh. Đây là công việc phát triển/demo; không xem các sequence đã khảo sát là tập kiểm tra độc lập cho Curb. Không huấn luyện, không đo precision/recall. Vùng mẫu không đại diện quy định cấm đỗ tại địa điểm gốc.

## Thay đổi

- Cấu hình mẫu tập trung tại `curb/demo.json`; nhận diện bằng `demo_id`. Nạp mẫu mới không trả nhầm mẫu cũ, không xóa nguồn hoặc lịch sử trước đây. Nạp lại khôi phục đúng phiên bản và không tạo bản sao.
- Vùng theo dõi bám mép lề phải, dwell 20 giây, mức theo dõi. Các thông số detector/engine giữ mặc định.
- UI hiện nguồn, giấy phép và mô tả đúng từng mẫu; hồ sơ ZIP có `SOURCE-LICENSE.txt`. Mẫu Gaithersburg cũ vẫn hiện chú thích cũ.
- Mẫu mới được đóng gói trong Curb 1.0.1. Runtime CPU và kiến trúc desktop giữ nguyên. Fixture Gaithersburg vẫn được giữ cho bộ tích hợp cũ.
- Downloader chỉ tải frame cần dùng bằng HTTP Range, kiểm tra từng frame theo ZIP CRC, tên và kích thước. Không tải archive 49 GB. Giữ tốc độ thời gian của nguồn khi lấy mẫu 15 xuống 5 FPS.

## Kiểm chứng

- `python -m unittest discover -s tests -v`: 29/29 đạt. Bao gồm ca đổi phiên bản mẫu khi dữ liệu cũ tồn tại, khôi phục/idempotence và ghi nguồn trong ZIP.
- `npm --prefix web run build`: TypeScript/Vite thành công.
- Video đầu vào: 1280 × 720, H.264, 5 FPS, 150 frame, 30 giây; 12.676.290 byte; SHA-256 `218ec991f1cf3133244736c35a02ddd69a6708753c903354331ea7a42a00d99e`.
- Suy luận GPU thật, YOLO26s + ByteTrack, float32, seed 0: job `02eca224bf38492e9d0e1358fa44427b`, 150 frame, 929 quan sát phương tiện, 3 cảnh báo cho ba xe ở giây 20. Toàn lượt 15,572 giây, suy luận 7,380 giây, GTX 1650. Không dùng phép đo này để cam kết tốc độ bản CPU.
- Artifact: `outputs/demo-2026-11-08/gpu-30s-smoke.json`, `gpu-30s-manifest.json`, `video-provenance.json`, `unit-tests-final.log`, `desktop-build.log`. Manifest chứa hash mã/model/nguồn và phiên bản thực tế.

## Bản desktop đã cài

- Build bằng `build-desktop.ps1 -BuildRoot "$env:LOCALAPPDATA/CurbBuild/1.0.0" -SkipDependencies`, tái dùng runtime CPU đã khóa để tránh tải lại. Bộ cài có phiên bản 1.0.1.
- Bộ cài `C:/Users/Admin/Curb/Curb-Setup-1.0.1-x64.exe`, 320.128.805 byte, SHA-256 `a72b211cfda47c4f356f98044e1fbf36d4557ce07b6cec2375ff2208720ebe91`. Cài cập nhật thành công, exit 0, log `outputs/demo-2026-11-08/desktop-upgrade.log`.
- Đã mở `C:/Users/Admin/Curb/app/Curb.exe`, nạp mẫu và bấm chạy bằng giao diện native. Health báo 1.0.1, Desktop CPU, model/FFmpeg sẵn sàng.
- Job `bed0997dbb7649fe8506e8e9526f3b4f`: 150 frame, 929 quan sát phương tiện, 3 cảnh báo ở giây 20; toàn lượt 41,032 giây, suy luận 28,350 giây trên CPU. Mốc cuối nguồn 29,8 giây, file dài 30 giây.
- Đã mở ảnh và phát clip trong WebView2, sau đó để cửa sổ ở hồ sơ mẫu mới. Không ghi quyết định thay người dùng. Lịch sử mẫu cũ còn nguyên; tổng quan 4 hồ sơ = 3 mới + 1 cũ.
- Ảnh chụp thật: [tổng quan](screenshots/desktop-streetscene-overview.jpg) ở zoom 80% để thấy trọn khung video và [hồ sơ](screenshots/desktop-streetscene-evidence.jpg) ở zoom mặc định 100%. Không phải ảnh dựng.
- Kết quả và manifest bản đã cài: `desktop-smoke.json`, `desktop-manifest.json`, `release.json` trong `outputs/demo-2026-11-08/`. Gói ZIP có giấy phép và ba sự kiện; ba clip CPU đã giải mã bằng FFmpeg. Mã runtime, giao diện và hash video đã đối chiếu với bản cài.

Bộ cài vẫn chưa ký chứng thư và chưa thử trên máy Windows sạch khác, như giới hạn của bản 1.0.0. Mẫu này chưa xác nhận quy định cấm đỗ tại địa điểm.

## Giới hạn phát hiện qua thử đoạn dài

Đã thử riêng 60 giây trước khi chọn mẫu hướng dẫn. Ở giây 35–38, xe tải che khuất từng xe đỗ làm box co lại/dịch chuyển; engine đặt lại lần dừng và sau đó báo lại. Với vùng phủ đủ ba xe, kết quả là **6 cảnh báo cho 3 xe đứng yên**, không phải 6 xe. Ca này chưa được sửa trong lần thay video. Cần cải thiện xử lý che khuất và kiểm tra nguy cơ gộp nhầm hai lần dừng trước khi dùng ngoài hiện trường.

Giữ kết quả và chẩn đoán tại `outputs/demo-2026-11-08/roi-smoke.json`, job `7739800592b14d5fa84ca8681c5039ec` trong `C:/Users/Admin/Curb/demo-verification`. Bản 60 giây vẫn tại `data/streetscene_test006_60s.mp4`. Không suy từ mẫu hướng dẫn 30 giây ít che khuất thành chất lượng trên video dài.

## Tự review theo pstack

Gates: xem hình thật và quyền sử dụng trước khi chọn; chạy suy luận trước khi đóng gói. Luồng phụ thuộc là nguồn → video → ROI → API/UI → kiểm tra → bộ cài → desktop. Cùng một người thực hiện tuần tự theo quy tắc người dùng; chỉ các lệnh đọc/kiểm tra độc lập chạy song song. Cân nhắc hardcode trong API và tệp cấu hình mẫu; chọn tệp JSON để tên, phiên bản, ghi nguồn và ROI cùng một chỗ. Không thêm hệ thống danh mục video hay thay engine để tối ưu cho một mẫu. Không commit, rebase hoặc mở PR vì chưa có chỉ thị.
