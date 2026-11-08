# Nội dung và thao tác trong Curb

Cập nhật 08/11/2026. Phạm vi: người vận hành giám sát dừng đỗ tại một máy Windows. Đây là nguyên tắc thiết kế và kết quả rà soát nội bộ, không thay thế thử nghiệm với người dùng độc lập.

## Cơ sở

- Apple, [Writing for interfaces, WWDC22](https://developer.apple.com/videos/play/wwdc2022/10037/): đọc riêng tiêu đề và nút vẫn phải hiểu việc cần làm; giữ nội dung đúng mục đích, ngữ cảnh và điều người dùng cần biết tiếp theo. Không đổ lỗi hoặc dùng giọng dạy bảo.
- Apple, [Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons): dùng biểu tượng quen thuộc cho thao tác quen thuộc; dùng nhãn khi biểu tượng không đủ rõ. Phân biệt mức ưu tiên hành động.
- Google Material 3, [Content design style guide](https://m3.material.io/foundations/content-design/style-guide): nội dung ngắn, trực tiếp, dễ quét; giải thích hệ quả tại nơi quyết định.
- Google Material 3, [Buttons](https://m3.material.io/components/buttons/guidelines) và [Icon buttons](https://m3.material.io/components/icon-buttons/guidelines): nhãn động từ ngắn; biểu tượng phải có tên truy cập và gợi ý khi cần. Không thu nhỏ chữ để nhét nhãn vào nút.
- Microsoft, [Vietnamese Style Guide](https://aka.ms/vietnamese-styleguide), bản PDF 60 trang truy cập ngày 08/11/2026: tiếng Việt tự nhiên, thuật ngữ nhất quán, viết hoa đầu câu, tránh dịch từng từ và diễn đạt lỗi máy móc. Không áp nguyên xi quy tắc ngữ pháp tiếng Anh của Material cho tiếng Việt.

## Quy tắc áp dụng

1. Tiêu đề nói màn hình chứa gì: “Video và camera”, “Phân tích”, “Cảnh báo”. Bỏ lời chào và câu lặp lại tiêu đề.
2. Nút nói hành động: “Thêm nguồn”, “Lưu vùng”, “Chạy phân tích”, “Lưu và duyệt tiếp”. Biểu tượng riêng chỉ dùng cho đóng, trợ giúp, thông tin và hành động quen thuộc có tên truy cập.
3. Chỉ giải thích khi giúp chọn đúng: đơn vị giây, ý nghĩa giới hạn bằng 0, lý do chưa chạy được, hệ quả xóa/khôi phục, yêu cầu duyệt bằng chứng. Không bỏ cảnh báo mất dữ liệu để giao diện trông gọn hơn.
4. Tên nguồn/địa điểm do người dùng nhập được giữ nguyên. Văn bản hệ thống dùng câu ngắn, đủ dấu tiếng Việt; ngày, giờ và số theo `vi-VN`. Nhãn không viết hoa từng từ.
5. Lỗi nói điều đã xảy ra và bước khắc phục; không dùng “Oops”, “thất bại” đơn độc hay lời xin lỗi dài. Thông báo lưu thành công chỉ hiện tạm thời.
6. Mỗi vùng công việc có một hành động chính. Không dùng thêm rail để lặp lại thanh điều hướng. Thông tin giấy phép video mẫu nằm trong mục mở rộng, vẫn truy cập được.
7. Màu xanh thể hiện lựa chọn/hành động; trạng thái có cả chữ. Chữ chính đen, chữ phụ đủ tương phản; không dùng màu để thay thế nội dung.

Tương phản tính từ mã màu sRGB: trắng trên Abyss Blue **10,48:1**; đen trên trắng **19,68:1**; chữ phụ #5C5C5C trên trắng **6,69:1**, trên Silver Mist **5,26:1**. Đây là kiểm tra các cặp màu chính; không phải chứng nhận toàn giao diện đạt WCAG.

## Thuật ngữ

| Khái niệm | Nhãn tiếng Việt | Lưu ý |
|---|---|---|
| Source | Video và camera / Nguồn | “Nguồn” dùng trong thao tác gộp hai loại |
| Job | Lượt phân tích | Không đổi qua lại giữa công việc, tác vụ và xử lý |
| Event | Cảnh báo | Chưa phải kết luận vi phạm |
| Pending | Chờ duyệt | Việc tiếp theo của người vận hành |
| Confirmed | Đã xác nhận | Người vận hành đã đối chiếu bằng chứng |
| Dismissed | Đã bỏ qua | Lưu lý do trong lịch sử |
| Resolved | Đã xử lý | Giữ lịch sử, không xóa bằng chứng |
| Zone | Vùng giám sát | Nút “Vẽ vùng mới”, “Lưu vùng” |

## Thay đổi luồng

Trước đây, nút chạy có thể bị khóa mà thiếu giải thích gần hành động. Nay chỉ hiện điều kiện còn thiếu: lưu vùng, bật vùng, khôi phục nguồn hoặc lấy khung hình camera. Sau khi duyệt, “Lưu và duyệt tiếp” mở cảnh báo chờ duyệt kế tiếp trong phạm vi danh sách đang xem; “Lưu và ở lại” giữ hồ sơ hiện tại. Chỉ chuyển hồ sơ sau khi máy chủ xác nhận lưu thành công. Không tự xác nhận cảnh báo.

Khi phân tích xong và có cảnh báo, hành động chính là “Duyệt cảnh báo”. Ứng dụng tìm hồ sơ chờ duyệt của lượt đó trước; vẫn mở được hồ sơ đã duyệt khi không còn hồ sơ chờ. Thẻ Chờ duyệt ở Tổng quan mở danh sách đã lọc, còn mục Cảnh báo trên thanh điều hướng mở toàn bộ danh sách.

Giữ lời nhắc đối chiếu quy định tại vị trí giám sát trong hồ sơ; bỏ các đoạn giải thích trùng nhau. Chi tiết mô hình và giới hạn triển khai nằm ở Cài đặt, Hướng dẫn và tài liệu phát hành.
