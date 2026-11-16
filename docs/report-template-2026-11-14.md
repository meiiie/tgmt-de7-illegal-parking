# Định dạng báo cáo Curb theo mẫu người dùng cung cấp

Ngày thực hiện: 14/11/2026.

## Tệp và phạm vi

- Mẫu trình bày: `E:/Downloads/BaoCao_XayDungHeThongPhatHienNguoiDeoKhauTrangVaGioiTinh.docx`.
- Nội dung đầu vào: `E:/Downloads/de7-Curb-muc-luc-chuan-2026-11-14.docx`.
- Bản giao: `E:/Downloads/de7-Curb-theo-mau-bao-cao-2026-11-14.docx`.
- Bản giao có 38 trang, bốn section, mục lục hai trang.

Tệp mẫu quyết định cách trình bày. Nội dung về khẩu trang, giới tính và kết quả
thực nghiệm của mẫu không được đưa vào báo cáo Curb. Hai tệp đầu vào và các bản
báo cáo cũ được giữ nguyên. Lượt này không thay đổi mã suy luận hoặc chạy lại
thực nghiệm.

## Định dạng đã áp dụng

- A4, lề trái 3 cm, phải 2 cm, trên và dưới 2,5 cm theo thông số thực của mẫu.
- Times New Roman 14, giãn dòng 1,5, căn đều; dòng đầu thụt 1,27 cm.
- Hai bìa, biểu trưng trường, khung bìa và thông tin tác giả của báo cáo Curb.
- Kiểu tiêu đề chương, đề mục, chú thích hình/bảng và tài liệu tham khảo theo mẫu.
- Mục lục tự động của Word; danh mục bảng và hình ba cột, số trang bằng PAGEREF.
- Bảng nền trắng, đường kẻ đen, tiêu đề in đậm; điều chỉnh độ rộng theo nội dung.
- Giữ nguyên chín ảnh Curb. Ảnh bộ cài thu về rộng 10,5 cm, giữ đúng tỉ lệ.
- Ngắt dòng các mã SHA-256 sau 32 ký tự để không tràn ô; không đổi giá trị mã.
- Giữ việc bỏ các dòng ghi nguồn dưới ảnh theo yêu cầu trước đó của người dùng.

Không thay đổi số liệu, phát biểu thực nghiệm hoặc nội dung của mười bảng gốc.
Chỉ chuẩn hóa dấu chấm sau số chương, đề mục, hình và bảng theo mẫu.

## Kiểm tra

Đã xem toàn bộ 73 trang mẫu và 38 trang bản giao. Bản đầu 39 trang được xem
từng trang; bản cuối được so ảnh thân trang: 29 trang giống hệt bản đã xem,
chín trang thay đổi được xem lại. Các trang cuối còn được đối chiếu số trang.
Không thấy chữ/hình bị cắt, bảng tràn lề, chú thích tách khỏi ảnh hoặc trang trắng.

Kiểm tra tự động xác nhận:

- Toàn bộ đoạn văn thân bài và các giá trị bảng giữ nguyên, ngoài chuẩn hóa số mục.
- Mười bảng nội dung gốc còn đủ; thêm hai bảng danh mục theo mẫu.
- Chín ảnh Curb giữ nguyên dữ liệu nhị phân; hai bìa dùng đúng biểu trưng của mẫu.
- Bốn section có hình học trang khớp mẫu; không còn ảnh nội dung của báo cáo mẫu.
- 42 mục trong mục lục và 18 tham chiếu hình/bảng khớp trang của bản xuất cuối.
- Hash hai tệp đầu vào không đổi.

SHA-256 của bản giao:

`a4b53a71072c12a8f5504797d1c817a000c168f86f6eab59a60e230f86537538`

Bằng chứng và công cụ tái hiện ở `outputs/report-template-2026-11-14/`, gồm
`artifact.md`, `build_from_template.py`, `export_word.ps1`, `verify_report.py`,
`verification.json` và ảnh kiểm tra. Đây là tệp nội bộ, không phải tài liệu giao.

Trình kết xuất đóng gói thiếu LibreOffice trên Windows. Đã dùng Microsoft Word
COM để cập nhật trường, phân trang và xuất PDF, sau đó dùng Poppler đóng gói để
kết xuất ảnh kiểm tra. PDF và ảnh chỉ phục vụ kiểm tra; tệp giao là DOCX.

Word khi lưu đã đổi một số mã style sang tên bản địa hóa và cập nhật metadata
tương thích. Đã kiểm tra các footer, numbering, footnote/endnote, font và theme;
không có thay đổi nội dung ngoài phạm vi nêu trên.
