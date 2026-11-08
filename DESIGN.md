# Curb — giao diện vận hành

Mode: Operate. Bản dựng bằng code, dùng ảnh người dùng và `docs/design/curb-concept.png` làm tham khảo, không yêu cầu khớp từng pixel.

Theo bộ màu người dùng gửi ngày 08/11/2026: nền Silver Mist #E4E4E4, bề mặt trắng, chữ Void Eclipse #0B0B0B, hành động chính và lựa chọn Abyss Blue #2B3B79. Chữ phụ #5C5C5C; màu trạng thái luôn đi cùng nhãn. Be Vietnam Pro đóng gói cục bộ, Lucide. Panel 16 px, chữ nội dung 14 px, tiêu đề trang 24 px. Một thanh điều hướng; bỏ rail lặp lại và hồ sơ người dùng giả. Ảnh concept cũ chỉ còn là tham khảo bố cục.

Chữ phục vụ quyết định hoặc thao tác: tiêu đề gọi đúng nội dung, nút bắt đầu bằng động từ, hướng dẫn xuất hiện khi có điều kiện cần giải thích. Không dùng khẩu hiệu, lời chào, mô tả hiển nhiên của thống kê hoặc tuyên bố hệ thống ở trang vận hành. Xem [quy tắc nội dung](docs/ux-writing.md).

Trang đầu cho thấy video thực và hàng đợi duyệt, thống kê chỉ đọc từ SQLite. Luồng chính: thêm nguồn → xem khung hình → vẽ vùng → chạy → mở bằng chứng → xác nhận/bỏ qua/giải quyết. Khi chưa có dữ liệu, hướng dẫn người dùng thêm video hoặc nạp mẫu có ghi nguồn; không chèn số giả.

Vùng vẽ dùng tọa độ chuẩn hóa, hiển thị ảnh đúng tỉ lệ; thêm/hoàn tác/đóng polygon, sửa điểm và xóa vùng có xác nhận. Drawer bằng chứng giữ ngữ cảnh danh sách, focus được quản lý. Bảng có tìm kiếm, lọc, phân trang, trạng thái rỗng/lỗi/đang tải. Layout desktop hai cột, mobile một cột và điều hướng cuộn; hành động chính vẫn có nhãn rõ.

Chất lượng cần kiểm tra: tương phản, focus bàn phím, không tràn ngang ở 390 px, modal đóng bằng Escape, API lỗi có thao tác thử lại, không hiển thị thông tin bí mật của camera.
