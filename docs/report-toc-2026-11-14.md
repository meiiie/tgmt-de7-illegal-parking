# Chỉnh ghi chú ảnh và mục lục báo cáo Curb

Theo yêu cầu người dùng ngày 14/11/2026, xóa chín đoạn ghi nguồn dưới hình
và làm lại mục lục. Bản bàn giao:
`E:/Downloads/de7-Curb-muc-luc-chuan-2026-11-14.docx`.
Bản báo cáo 35 trang trước đó được giữ nguyên.

## Căn cứ trình bày

Tham khảo Hướng dẫn trình bày Đề án tốt nghiệp thạc sĩ của Viện Đào tạo
Sau đại học, Trường Đại học Hàng hải Việt Nam, phần mục lục và đánh số trang:
https://sdh.vimaru.edu.vn/sites/sdh.vimaru.edu.vn/files/Huong_dan_trinh_bay_De_an_tot_nghiep_thac_si.pdf

Tài liệu được tải và đọc ngày 14/11/2026, lưu cùng SHA-256 tại
`outputs/report-toc-2026-11-14/changes.json`. Áp dụng cách trình bày mục lục
cho báo cáo học phần hiện có; không biến báo cáo thành đề án tốt nghiệp hoặc
tự thêm lời cam đoan, chữ ký, công trình hay nội dung khác.

## Kết quả

- Mục lục Word tự động, hai trang, 42 đề mục lấy nguyên văn từ tiêu đề.
- Chương và mục phân cấp; Times New Roman 14, chương in đậm, số trang căn
  phải với dấu chấm dẫn. Các phần đầu dùng i–vi; nội dung bắt đầu từ 1.
- Danh mục từ viết tắt, bảng và hình được đặt riêng theo thứ tự mẫu.
- Tài liệu tham khảo đặt trước phụ lục; thông tin tác giả/giấy phép của dữ
  liệu vẫn có ở tài liệu tham khảo [6].
- Giữ nguyên nội dung còn lại, cả mười bảng và chín ảnh. Không đổi số đo.

## Kiểm tra

Microsoft Word cập nhật mục lục và các trường, xuất PDF cho QA; Poppler
bundled render đủ 36 trang. Renderer mặc định không có soffice.exe nên không
dùng được. Đã xem toàn bộ trang, sửa trường hợp chú thích bảng bị sang trang
khác, kiểm tra lại bản render cuối.

Script kiểm chứng so đa tập nguyên văn phần nội dung, từng ô bảng, hash ảnh
và hash bản nguồn. Cả 42 dòng mục lục và 18 tham chiếu hình/bảng khớp số trang
trong PDF mới. Mã dựng, kiểm chứng và ảnh QA nằm ở
`outputs/report-toc-2026-11-14/`; chỉ giao Word.
