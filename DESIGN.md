# Curb — giao diện vận hành

Mode: Operate. Bản dựng bằng code, dùng ảnh người dùng và `docs/design/curb-concept.png` làm tham khảo, không yêu cầu khớp từng pixel.

Màu nền #f3f3f0, panel #ffffff, chữ #22241f, chữ phụ #66695f, cam #ed592e; màu trạng thái luôn đi cùng chữ. Be Vietnam Pro tự lưu trong bundle, icon Lucide. Panel 16 px; nút chính tối; cam dành cho chú ý và vùng giám sát. Điều hướng chính dạng pill, rail bên trái cho công việc/cài đặt/trợ giúp.

Trang đầu cho thấy video thực và hàng đợi duyệt, thống kê chỉ đọc từ SQLite. Luồng chính: thêm nguồn → xem khung hình → vẽ vùng → chạy → mở bằng chứng → xác nhận/bỏ qua/giải quyết. Khi chưa có dữ liệu, hướng dẫn người dùng thêm video hoặc nạp mẫu có ghi nguồn; không chèn số giả.

Vùng vẽ dùng tọa độ chuẩn hóa, hiển thị ảnh đúng tỉ lệ; thêm/hoàn tác/đóng polygon, sửa điểm và xóa vùng có xác nhận. Drawer bằng chứng giữ ngữ cảnh danh sách, focus được quản lý. Bảng có tìm kiếm, lọc, phân trang, trạng thái rỗng/lỗi/đang tải. Layout desktop hai cột, mobile một cột và điều hướng cuộn; hành động chính vẫn có nhãn rõ.

Chất lượng cần kiểm tra: tương phản, focus bàn phím, không tràn ngang ở 390 px, modal đóng bằng Escape, API lỗi có thao tác thử lại, không hiển thị thông tin bí mật của camera.
