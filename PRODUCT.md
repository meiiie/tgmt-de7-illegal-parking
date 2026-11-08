# Curb

## Platform

Desktop Windows và web cục bộ, giao diện tiếng Việt.

## Stack

Người dùng giao quyền chọn stack. React + TypeScript, FastAPI + SQLite, tiến trình Python riêng chạy YOLO26s/ByteTrack. Giữ demo Gradio và các kết quả nghiên cứu để đối chiếu. Vỏ desktop dùng WinForms + Microsoft WebView2, bộ cài Inno Setup và CPython embeddable với PyTorch CPU. Bản phát triển Python tiếp tục hỗ trợ CUDA.

## Purpose and users

Biến dự án nghiên cứu phát hiện dừng đỗ thành công cụ nhập video/camera, cấu hình vùng, chạy phân tích, duyệt bằng chứng và xuất hồ sơ.

Giả định triển khai ban đầu: một người vận hành trên một máy Windows, một luồng suy luận GPU tại một thời điểm. Người dùng đã xác nhận ưu tiên giám sát dừng đỗ trên đường phố (08/11/2026).

## Product truth

- Cảnh báo là xe dừng quá ngưỡng trong vùng, không tự kết luận vi phạm pháp luật.
- Chưa có OCR biển số, nhận dạng danh tính hoặc bằng chứng chất lượng trên camera triển khai độc lập.
- Video và camera RTSP/HTTP do người vận hành cung cấp. Mẫu mặc định MERL Street Scene CC BY-SA 4.0 có camera cố định và xe đỗ dọc lề; ghi nguồn và biến đổi rõ ràng. Mẫu Wikimedia cũ được giữ cho kiểm tra hồi quy.
- Cấu hình, công việc, sự kiện và lịch sử duyệt lưu bền vững cục bộ. Không có dữ liệu thống kê dựng sẵn.
- Mỗi lần chạy giữ cấu hình, phiên bản, hash mã/model/dữ liệu, thông số và kết quả thực tế.
- Bản đầu phục vụ loopback; triển khai mạng nhiều người cần thiết kế xác thực và vận hành riêng.

## Visual commitment

Tham chiếu ảnh người dùng: sáng, trắng/xám dịu, nút đen, điểm nhấn cam, panel bo góc, thanh điều hướng gọn. Mockup imagegen là định hướng bố cục; dữ liệu minh họa và khả năng OCR trong ảnh không phải tính năng hoặc kết quả sản phẩm.
