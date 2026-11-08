# Curb 1.1.0 · kế hoạch phát hành

Mục tiêu: tải một bộ cài Windows, mở để cài với một màn hình tiến độ, mở Curb và thực hiện được luồng nguồn → vùng → xử lý → duyệt → xuất hồ sơ. Phát hành công khai mã nguồn, bộ cài, checksum và hướng dẫn trên GitHub theo yêu cầu ngày 08/11/2026.

Tự thực hiện tuần tự theo pstack, không giao việc. Đã đọc nguyên tắc Model the Domain và Prove It Works. Không thay detector theo quảng cáo SOTA; giữ YOLO26s/ByteTrack để so sánh được.

## Các chặng và điều kiện qua

1. **Vòng đời cảnh báo.** Tái hiện ca che khuất StreetScene Test006 60 giây (cũ: 6 cảnh báo cho 3 xe). Thêm xác nhận chuyển động cho sự kiện đã cảnh báo; kiểm tra cả xe thực sự rời/chuyển vị trí, mất dấu dài và xe mới. Chạy lại video thực, lưu manifest và kết quả riêng. Đây là hồi quy phát triển, không phải test độc lập.
2. **Sản phẩm.** Một nguồn phiên bản, bộ nhận diện vector nhất quán, trang giới thiệu có phiên bản/giấy phép/hỗ trợ, trạng thái khởi động rõ ràng. Giao diện tổng quan sử dụng được ở 1360×880 và màn hình laptop, không phải giảm zoom để xem camera.
3. **Bộ cài.** Per-user, không hỏi thư mục/thành phần/Next nhiều lần, tiến độ có tên và phiên bản, tự mở sau cài. Giữ AppId cho nâng cấp; giữ dữ liệu khi gỡ. Chuẩn bị lỗi WebView2/.NET có hướng dẫn. Không che hoặc vượt cảnh báo bảo mật Windows.
4. **Phân phối.** Mã ứng dụng AGPL-3.0, nguồn và giấy phép dependency đi cùng, video CC BY-SA 4.0 giữ attribution. Có CHANGELOG, SECURITY, SUPPORT, hướng dẫn backup/restore, SHA-256 và workflow CI. Chưa có chứng thư ký mã trên máy; không gọi bộ cài là đã ký.
5. **Dùng thử thật.** Build và cài, kiểm tra cửa sổ installer, khởi động lần đầu, dữ liệu cũ sau nâng cấp, nhập mẫu/video, vùng, cảnh báo, duyệt, xuất, sao lưu và khởi động lại. Kiểm tra API camera bằng HTTP replay; chưa có camera RTSP hiện trường để chứng nhận. Ghi rõ mục nào chưa kiểm tra.
6. **Phát hành.** Tự review mã, kiểm tra bí mật không in giá trị, commit/push thường, CI xanh, tag đúng commit, GitHub Release có bộ cài/source/checksum, đối chiếu checksum asset công khai.

## Quyết định

- Giữ tên Curb và màu cam #ed592e, nền #f3f3f0, chữ #22241f theo định hướng người dùng đã đưa. Nhà phát hành mã nguồn: Meiiie. Tên hiển thị hệ thống: Curb · Giám sát dừng đỗ.
- Giữ WinForms/WebView2 và Inno Setup vì đã chạy thật, có nâng cấp/gỡ cài ổn định; chuyển Rust/Tauri lúc này không giải quyết lỗi vận hành được quan sát.
- Dữ liệu `Stop` giữ một lần dừng, thêm thời điểm bắt đầu nghi ngờ chuyển động. Chỉ kết thúc cảnh báo đang tồn tại khi chuyển động được xác nhận liên tục; không tăng thời gian mất dấu để gộp bừa xe mới.
- Phiên bản công khai đầu tiên là 1.1.0. Mô tả rõ đây là công cụ hỗ trợ người vận hành, chưa được đánh giá độc lập trên camera triển khai.

## Bằng chứng

Ghi kết quả mới ở `outputs/release-1.1.0/`; tóm tắt có thể công khai ở `docs/release-verification-1.1.0.md`. Không thay báo cáo lịch sử.

Tài liệu chính thức đã đối chiếu: [Inno Setup](https://jrsoftware.org/ishelp/), [WebView2 distribution](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution), [Windows code signing](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options), [Ultralytics license](https://www.ultralytics.com/license), [FFmpeg legal](https://ffmpeg.org/legal.html).

Ngoại lệ hạ tầng được ghi nhận khi thực hiện: GitHub Actions không khởi chạy do tài khoản bị khóa vì billing. Không thay đổi thanh toán hoặc chuyển sang tài khoản khác. Giữ kết quả kiểm tra cục bộ và công bố rõ CI chưa được thực thi trong báo cáo/Release; không đánh dấu CI xanh.
