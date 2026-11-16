# Bỏ phụ lục theo báo cáo mẫu

Ngày 14/11/2026, người dùng yêu cầu bỏ phụ lục nếu báo cáo mẫu không có phần này.
Đã kiểm tra trực tiếp toàn bộ văn bản trong DOCX mẫu: không có phụ lục; phần cuối
là Tài liệu tham khảo.

Bản mới: `E:/Downloads/de7-Curb-theo-mau-khong-phu-luc-2026-11-14.docx`.
Giữ nguyên mẫu và bản Curb 38 trang đã giao trước đó.

- Xóa Phụ lục A gồm 22 phần tử nội dung, trong đó có hai bảng và các lệnh chạy.
- Xóa hai hàng Bảng A.1 và Bảng A.2 trong danh mục bảng.
- Xóa hai câu dẫn tới phụ lục trong Mở đầu và mục 4.2.
- Cập nhật trường Word, mục lục và các số trang. Bản cuối có 36 trang.

Đã đối chiếu nguyên văn, giá trị của các bảng còn lại, 11 ảnh (chín ảnh Curb và
hai biểu trưng bìa), hình học của bốn section và hash hai tệp đầu vào. Ngoài các
thay đổi nêu trên, nội dung được giữ nguyên. Không chạy lại thực nghiệm.

Đã kiểm tra 39 mục lục và 16 tham chiếu hình/bảng với PDF xuất bằng Word. Không
còn dẫn chiếu phụ lục. Kết xuất 36 trang: 12 trang giống từng pixel với bản đã
duyệt; 24 trang khác được xem lại, không thấy lỗi bố cục. Trình kết xuất đóng gói
thiếu soffice.exe; dùng Word COM và Poppler đóng gói để kiểm tra.

SHA-256 bản giao:
`eeeb6ec2d962359ef737c4b06f6a66d20b039b72d3d5d7037633ae7d240507cf`.

Bằng chứng nội bộ: `outputs/report-no-appendix-2026-11-14/verification.json`.
