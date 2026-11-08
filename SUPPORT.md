# Hỗ trợ Curb

Mở **Về Curb → Tải chẩn đoán** để lấy phiên bản và tình trạng thành phần. Báo lỗi tại [GitHub Issues](https://github.com/meiiie/tgmt-de7-illegal-parking/issues), ghi bước tái hiện, điều mong đợi, kết quả và phiên bản Windows. Không gửi mật khẩu camera, video nhạy cảm hoặc bản sao lưu đầy đủ lên issue công khai.

## Cài, cập nhật, gỡ

Tải `Curb-Setup-<version>-x64.exe` trong [Releases](https://github.com/meiiie/tgmt-de7-illegal-parking/releases/latest), mở tệp và chờ cửa sổ tiến độ. Curb tự mở sau khi cài. Dùng Desktop hoặc Start để mở các lần sau. Không cần cài Python hoặc Node.js.

Đóng Curb trước khi nâng cấp rồi mở bộ cài mới. Nếu ứng dụng còn mở, bộ cài có thể yêu cầu đóng ứng dụng để thay tệp an toàn. Dữ liệu và lịch sử được giữ. Gỡ trong **Windows Settings → Apps → Curb**; thư mục dữ liệu vẫn còn.

Bộ cài đầu tiên chưa ký mã. Không tắt tính năng bảo vệ Windows để cài phần mềm. Đối chiếu nguồn tải và `SHA256SUMS.txt`; nếu chính sách của máy yêu cầu ứng dụng đã ký, dùng quy trình của quản trị viên hoặc chờ bản có chữ ký.

## Sao lưu và khôi phục

Trong **Cài đặt trạm**, dừng lượt xử lý rồi chọn **Tải bản sao lưu**. Chọn **Khôi phục bản sao lưu…**, chọn ZIP, xác nhận khôi phục. Curb tạo thư mục mới, kiểm tra SQLite, chuyển sang dữ liệu khôi phục và mở lại. Dữ liệu trước đó không bị ghi đè. Camera cần nhập lại địa chỉ và mật khẩu.

**Về Curb → Mở thư mục dữ liệu** cho biết vị trí hiện dùng. Mặc định là `%USERPROFILE%\Curb\data`; sau khôi phục là thư mục `restored-*` bên cạnh. Tệp `%USERPROFILE%\Curb\desktop-data-path.txt` lưu lựa chọn này. Với bản phát triển, tham số `--data-dir` chỉ định thư mục riêng và không thay lựa chọn desktop.

## Sự cố thường gặp

| Triệu chứng | Xử lý |
|---|---|
| Thiếu WebView2 | Kết nối Internet và chạy lại bộ cài; runtime được tải trực tiếp từ Microsoft. Máy đã có runtime dùng được ngoại tuyến. |
| Thiếu Visual C++ x64 | Bộ cài tải runtime chính thức và kiểm tra SHA-256; Windows có thể yêu cầu quyền quản trị. Nếu Microsoft yêu cầu khởi động lại, lưu công việc và khởi động lại trước khi cài Curb tiếp. |
| Thiếu .NET Framework 4.8 | Cập nhật Windows hoặc cài .NET Framework 4.8 từ Microsoft rồi chạy lại. |
| Không kết nối camera | Kiểm tra mạng, tài khoản và địa chỉ luồng; dùng **Kiểm tra kết nối**. Mật khẩu không xuất hiện trong API trả về hoặc bản sao lưu. |
| Chạy chậm | Thử YOLO26n, ảnh 480 px hoặc giảm FPS. Đo lại cảnh báo trên video phát triển sau khi đổi cấu hình. |
| Cảnh báo lặp/sai | Kiểm tra che khuất, rung camera, ROI, xe chờ đèn và ngưỡng; lưu trường hợp để hiệu chỉnh. |
| Ứng dụng dừng ngoài dự kiến | Mở lại; lượt bị gián đoạn được ghi nhận, bằng chứng đã lưu vẫn còn. Nhật ký `desktop.log` nằm trong thư mục dữ liệu. |

Yêu cầu tối thiểu: Windows 10 x64 1809+ hoặc Windows 11, .NET 4.8, WebView2, Visual C++ x64 v14.44 trở lên. Khuyến nghị RAM 8 GB, SSD và ít nhất 3 GB trống để cài, cộng dung lượng cho video/bằng chứng. Đây là cấu hình hướng dẫn, không phải cam kết tốc độ nhiều camera.
