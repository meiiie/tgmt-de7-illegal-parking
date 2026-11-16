# Viết lại báo cáo theo sản phẩm Curb

Theo yêu cầu người dùng ngày 14/11/2026, báo cáo được viết lại toàn bộ.
Curb là sản phẩm của đề tài từ phần mở đầu đến phương pháp, thiết kế,
thực nghiệm, triển khai và kết luận. Bỏ cấu trúc bổ sung Curb sau một báo cáo
Gradio; không đổi tên phần mềm hoặc gán các kết quả nghiên cứu cũ cho worker mới.

Bản Word mới: `E:/Downloads/de7-Curb-bao-cao-hoan-chinh-2026-11-14.docx`.
Mọi bản báo cáo cũ được giữ nguyên và kiểm tra SHA-256.

## Thay đổi nội dung

- Năm chương theo mạch bài toán, phương pháp, xây dựng sản phẩm, đánh giá,
  triển khai. Phụ lục giữ cấu hình, dấu vết và lệnh tái hiện.
- Mô tả bộ quy tắc theo `curb/engine.py`: neo và lịch sử vị trí, kiểm tra vùng,
  quản lý một lần dừng, kế thừa mã có giới hạn, xác nhận chuyển động sau cảnh
  báo và chặn dấu hiệu ùn xe theo vùng. Bỏ các mô tả thuật toán cũ không còn
  đúng với sản phẩm hiện tại.
- Đối chiếu T4 được dùng để giải thích lựa chọn mô hình. Giữ kết quả DINOv3
  tăng FP và kết quả SAM chưa tạo cảnh báo; không kể lại từng vòng thử như nhật ký.
- Thực nghiệm chính trình bày lượt Curb 9 × 240 giây trên GTX 1650, từng video,
  số bỏ sót, sai số thời điểm và các lượt camera công khai. Giữ cả HTTPS/HLS thấp.
- CPU và CUDA là hai cấu hình triển khai của cùng sản phẩm. Không gộp số GPU
  vào cam kết tốc độ bộ cài CPU.
- Dùng ảnh bằng chứng tại đúng lúc cảnh báo video 35, khung cuối camera YouTube,
  ảnh thư mục train cùng ba ảnh nghiệp vụ Curb và ảnh bộ cài đã có.
- Bỏ ảnh Gradio, sơ đồ lặp, bảng giả lập và bảng nhật ký chi tiết trùng lập luận.
  Bản mới còn 9 hình và 10 bảng, trong đó một bảng từ viết tắt.

## Cách biên tập và kiểm tra

Áp dụng Việt ngữ toàn thư 3.0.0, Scientific Figure Making từ figures4papers,
các nguyên tắc tổ chức và viết gọn phù hợp của Anti-Defensive Writing,
pstack technical-writing và unslop. Giữ đầy đủ phạm vi và số đo bất lợi;
không áp dụng lời khuyên che giới hạn hoặc đổi nhiệm vụ để tạo kết quả có lợi.

Nguồn dựng, nội dung và kiểm chứng nằm trong
`outputs/report-rewrite-curb-2026-11-14/`. Bảng số được đọc từ JSON đã lưu,
kiểm lại TP/FP/FN, số khung và F1. Hash mã Curb hiện tại được đối chiếu với
manifest của lượt AI City; không thay mã hoặc chạy thêm suy luận trong lượt viết lại.

Renderer DOCX mặc định thiếu `soffice.exe` trong môi trường Windows này.
Dùng Microsoft Word để cập nhật trường, xuất PDF và Poppler để render từng
trang. Rà trang, công thức, bảng, ảnh và tham chiếu trước khi giao.

Bản cuối có 35 trang, gồm sáu trang đầu và 29 trang nội dung, phụ lục,
tài liệu tham khảo. Đã kiểm tra toàn bộ bố cục qua các vòng render; ở vòng
cuối, 31 trang có nội dung ảnh trùng chính xác với trang đã rà, bốn trang
thay đổi được xem lại, và kiểm tra thêm số trang ở phần cuối. Mục lục cùng
18 tham chiếu hình/bảng đã cập nhật. Hồ sơ Việt Guard hợp lệ ở chế độ compose;
năm dấu hiệu khoảng trắng thuộc bìa và công thức đã được rà, giải thích.
Đây là kiểm tra của trợ lý AI, chưa thay tác giả duyệt nội dung.

## Yêu cầu chụp lượt YouTube và AI City

Người dùng yêu cầu ảnh của chính lượt thử. Đã thử mở Edge bằng Computer Use.
Công cụ dừng vì không xác định được URL hiện tại đủ chắc chắn để áp dụng
chính sách. Đã dừng mọi thao tác màn hình trong lượt, không dùng công cụ
trình duyệt khác để vượt chặn.

Hai ảnh thực nghiệm trong báo cáo là đầu ra Curb đã lưu, không phải ảnh chụp
trang kết quả mới: video 35 tại mốc cảnh báo 20 giây với nhãn dự đoán truck
số 953 ở mép trái; khung cuối lượt camera YouTube Đà Nẵng. Các ảnh nghiệp vụ
Curb là ảnh chụp ngày 14/11/2026 ở lượt trước. Chú thích phân biệt đúng loại ảnh.
