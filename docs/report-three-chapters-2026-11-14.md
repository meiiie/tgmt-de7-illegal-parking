# Báo cáo Curb ba chương và sơ đồ mới

Ngày 14/11/2026, người dùng yêu cầu còn ba chương, sơ đồ chuyên nghiệp theo
figures4papers, đồng thời giữ định dạng của báo cáo mẫu đã cung cấp.

Bản giao: `E:/Downloads/de7-Curb-3-chuong-so-do-2026-11-14.docx`, 36 trang.

## Cấu trúc

1. Tổng quan bài toán và phương pháp: gộp bài toán/yêu cầu và phương pháp vào
   hai nhóm mục. Giữ phần giải thích YOLO26s, ByteTrack và vai trò DINOv3.
2. Thiết kế và xây dựng ứng dụng Curb: kiến trúc, cấu hình nguồn/vùng, xử lý
   camera, bằng chứng, giao diện, cài đặt, quy trình vận hành và lưu trữ.
3. Thực nghiệm và đánh giá: dữ liệu, cấu hình, giao thức, lựa chọn mô hình,
   AI City, camera, FPS, kiểm tra chức năng và hướng hoàn thiện.

Giữ Mở đầu, Kết luận, Tài liệu tham khảo và các phần đầu báo cáo. Không phụ lục.
Đổi số mục, hình, bảng, công thức và dẫn chiếu theo vị trí mới; cập nhật mục lục
và danh mục bằng trường Word. Giữ tất cả số đo, kết quả bất lợi và giới hạn đánh
giá. Không huấn luyện hoặc chạy thêm thực nghiệm GPU trong lượt này.

## Hình và định dạng

Áp dụng skill Scientific Figure Making của figures4papers; đã đọc hướng dẫn
thiết kế, mẫu bố cục, API và danh mục ví dụ. Dùng Matplotlib 3.11.2 với Python
đóng gói, thư viện hình vẽ tạm đã có ngoài môi trường suy luận.

- Vẽ lại sơ đồ kiến trúc, đối chiếu mã engine, worker và capture.
- Bổ sung sơ đồ vòng đời một lần dừng, nêu điều kiện cảnh báo và đặt lại mốc.
- Bổ sung quy trình giám sát, duyệt và xuất hồ sơ, có phản hồi về cấu hình.
- Vẽ lại biểu đồ FPS từ `outputs/report-review-2026-11-14/camera-api-results.json`.

Hình xuất PNG 300 dpi, PDF vector và SVG giữ chữ; dùng bộ màu #2B3B79,
#0B0B0B, #E4E4E4 theo yêu cầu người dùng. DOCX nhúng PNG ở kích thước in rõ.
Mọi số trên biểu đồ lấy từ JSON cũ; không tạo số đo mới. Giữ nguyên bảy ảnh
chụp thật cùng hai biểu trưng trường.

Mẫu định dạng: `E:/Downloads/BaoCao_XayDungHeThongPhatHienNguoiDeoKhauTrangVaGioiTinh.docx`.
Giữ hình học A4, lề trái 3 cm/phải 2 cm/trên dưới 2,5 cm, Times New Roman 14,
giãn dòng 1,5, thụt dòng 1,27 cm; các kiểu tiêu đề, bìa, bảng, chú thích và tài
liệu tham khảo của bản đã theo mẫu. Không chuyển nội dung của báo cáo mẫu vào Curb.

## Kiểm tra

Đã tự kiểm tra tuần tự nội dung, dẫn chiếu và bản kết xuất:

- Tệp nguồn và mẫu giữ nguyên hash; mọi bản giao trước còn nguyên.
- Đối chiếu nguyên văn còn lại sau đổi dẫn chiếu và đoạn giới thiệu ba chương.
- Bảy bảng nội dung cùng bảng từ viết tắt giữ nguyên từng ô.
- Bảy ảnh chụp và hai biểu trưng giữ nguyên dữ liệu nhị phân.
- Bốn section khớp hình học mẫu; bảy kiểu chữ/cấp mục/TOC được giữ nguyên XML.
- 39 mục lục, 11 hình và bảy bảng có số trang khớp PDF cuối.
- Đã xem toàn bộ 37 trang bản đầu; chỉnh sơ đồ và đoạn dẫn để bỏ trang gần trống
  cuối Chương 1. Bản cuối 36 trang: 26 thân trang khớp pixel với trang đã xem;
  mười trang khác được xem lại. Không thấy chữ cắt, bảng tràn hoặc chú thích rời.

Trình kết xuất đóng gói thiếu `soffice.exe`; đã lưu lỗi và dùng Word COM để
cập nhật trường, xuất PDF, rồi Poppler đóng gói để tạo ảnh kiểm tra. Bằng chứng,
nguồn hình SVG/PDF và mã tái hiện ở `outputs/report-three-chapters-2026-11-14/`.
PDF và ảnh là tệp kiểm tra nội bộ; tài liệu giao là DOCX.

SHA-256 bản giao:
`853bddc7a784d3075ecd1ee46b8acdda324e0228916a778514053f0a4e7bf3cd`.
