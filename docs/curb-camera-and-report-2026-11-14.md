# Curb qua dịch vụ thật và cập nhật báo cáo ngày 14/11/2026

Các lượt dưới đây tạo nguồn, kiểm tra kết nối và tạo job qua API của Curb đang chạy, dùng thư mục dữ liệu riêng. Không dùng mock detector hoặc số thống kê dựng sẵn. Bản nguồn CUDA dựa trên commit `06f38bc6bff630c8b3dcd3a4c8892fd70a3715fe`, có bản vá chưa commit; bộ cài CPU 1.1.0 chưa được thay thế.

[Bằng chứng cấu hình và kết quả mới](curb-camera-evidence-2026-11-14.json). Việc tải bộ dữ liệu và lượt chín video được ghi ở [thực nghiệm trước trong cùng ngày](realtime-and-aicity-2026-11-14.md). Driver NVIDIA đã kiểm tra là 610.91, GPU 4.096 MiB.

## Kết quả camera mới

YOLO26s + ByteTrack, GTX 1650, float32, seed 0, ảnh 640, confidence 0,30; mục tiêu 5 FPS, dwell 20 giây, still-window 2 giây, dung sai 0,18, lost grace 1,5 giây, min-area 200 px²; không lưu video toàn lượt. Một worker chạy tuần tự từng nguồn.

| Nguồn | Khung | Giây nhận nguồn | FPS nhận | FPS toàn worker | Timeout / nối lại | Kết thúc |
|---|---:|---:|---:|---:|---:|---|
| VDOT I-66 RTSP trực tiếp | 454 | 120,031 | 3,782 | 3,488 | 0 / 0 | completed |
| Cùng kênh VDOT, HTTPS/HLS trực tiếp | 73 | 124,641 | 0,586 | 0,552 | 0 / 0 | completed |
| YouTube Đà Nẵng qua cầu nối HTTP | 883 | 180,172 | 4,901 | 4,745 | 0 / 0 | completed |

FPS nhận dùng thời gian từ khi mở nguồn; FPS toàn worker gồm khởi động và kết thúc. Các số gần 5 FPS chịu giới hạn lấy mẫu đặt trước, không phải phép đo công suất tối đa của GTX 1650. Lượt ngoại tuyến chín video trước đó đạt 12,520 khung lấy mẫu/giây; không đồng nhất với FPS camera.

Nguồn VDOT mang logo VDOT/511, kênh `NROCCTVI66E00501`, 320×240, mở được cả hai giao thức. Cảnh thử tối và mờ; cả hai lượt không có detection hoặc cảnh báo. Đây là kiểm tra vận hành truyền tải, không phải kết quả độ chính xác. Cổng chính thức: [511 Virginia](https://www.511virginia.org/). Việc bỏ YouTube không tự bảo đảm HLS chạy mượt: phải giữ cả số thấp của HTTPS/HLS trong báo cáo.

YouTube dùng [camera cổng trường Nguyễn Huệ, Đà Nẵng](https://www.youtube.com/watch?v=sJvEFrG0wq0), yt-dlp 2026.10.26, video-only 854×480, FFmpeg `fps=10,realtime=limit=60`, `http_persistent=0`, cầu nối MJPEG trên loopback và bộ nhận ảnh mới nhất của Curb. Hai lần mở trước gặp lỗi TLS; lần thứ hai chỉ xuất khoảng 10 giây hình rồi dừng. Sau khi tắt HTTP persistent, lượt 180 giây qua Curb hoàn tất; các lượt khác thời điểm nên chưa đủ để quy mọi thay đổi cho riêng tùy chọn này. Cầu nối chưa có tự làm mới URL/restart bảo đảm 24/7.

Đồng hồ trên ảnh cầu nối đầu là 13:40:45, preview cuối 13:46:03, tiến 318 giây trong 318,122 giây giữa thời điểm ghi hai tệp. Khoảng đó có cả thời gian chờ các job trước, không chỉ 180 giây suy luận. Không thấy tăng trễ ở hai đầu; chưa đo độ trễ camera gốc tới cảnh báo vì chưa biết sai lệch đồng hồ nguồn. Tuổi ảnh trong tiến trình lớn nhất ở lượt YouTube là 0,203 giây, loại trừ độ trễ phía camera/mạng/HLS.

YouTube tạo 6 cảnh báo và có 795/883 khung bị đánh dấu ùn xe. Preview cho thấy nhiều xe đỗ và vẫn có xe lưu thông; quy tắc này cần được đối chiếu bằng nhãn trước khi dùng để quyết định cảnh báo tại địa điểm. Chưa có nhãn độc lập để chấm precision/recall/F1, FP/giờ hoặc độ trễ sự kiện live.

## Video AI City qua Curb và hồ sơ xuất

Đã nhập lại `35.mp4` bằng API upload, kiểm tra metadata/hash, lưu vùng, tạo job 240 giây, lấy mẫu 1 FPS, confidence 0,25, bật video có chú thích. Kết quả 240 khung, 1 cảnh báo, 15,291 giây worker, 15,696 khung lấy mẫu/giây, trạng thái completed. Bộ tham số còn lại giống lượt chín cửa sổ train trước đó. Không gộp tốc độ lượt bật ghi video này vào tổng chín lượt cũ.

Đã kiểm tra:

- Video có chú thích giải mã đủ 240 khung; clip cảnh báo giải mã 10 khung.
- API trả ảnh, clip, video, JSON, CSV và ZIP bằng chứng; ZIP có 9 mục, CRC hợp lệ.
- Cập nhật một hồ sơ thử nghiệm sang bỏ qua, có lý do, lịch sử và version tăng; không xác nhận vi phạm thực tế.
- Manifest lưu cấu hình, seed, phiên bản gói, hash mã, model và video. Bộ kiểm tra đã đạt 35 unit test và 24 ca tích hợp ở lượt trước với cùng worker; thay đổi sau đó chỉ thuộc harness nhận YouTube.

Thử qua API kiểm chứng xử lý và nghiệp vụ phía dịch vụ. Nó không thay thế kiểm tra thao tác giao diện.

## Báo cáo và ảnh

Giữ nguyên bản gốc `E:/Downloads/de7.docx`. Bản sửa nằm tại `E:/Downloads/de7-cap-nhat-thuc-nghiem-2026-11-14.docx`; phần mới gồm mục 3.10, 4.10–4.13 và 5.7, sửa phạm vi phương pháp và kết luận. Giữ các bảng v4/v5/v6, không đổi chúng thành số đo GTX 1650. Đã sửa danh mục hình/bảng để tách đúng hai nhóm và cập nhật mục lục bằng Word.

Thư mục minh chứng cục bộ: `E:/Downloads/de7-minh-chung-2026-11-14/`. Có ảnh File Explorer của train, ảnh đầu/cuối từ engine Curb, video/clip xuất, manifest và JSON/CSV. Ảnh engine là kết quả xử lý, không được gọi là ảnh chụp giao diện Curb.

Computer Use chụp được File Explorer, sau đó dừng khi không xác định chắc chắn URL của cửa sổ Chrome để áp dụng chính sách. Không có ảnh GUI Curb mới trong lượt này; không dùng công cụ khác để vượt chặn. Ảnh GUI Gradio lịch sử trong báo cáo vẫn giữ đúng nguồn và thời điểm.

Renderer LibreOffice của skill không có executable trong runtime Windows. Đã xuất PDF bằng Word cài trên máy để kiểm tra bố cục, sau đó raster bằng Poppler của runtime Codex; không dùng LibreOffice ngoài runtime. File gốc không bị thay đổi.

## Tái hiện

Chạy Curb bản nguồn CUDA với dữ liệu tách riêng:

```powershell
.venv/Scripts/python.exe -X utf8 -m curb --port 18770 --data-dir outputs/report-review-2026-11-14/curb-data
```

Cấp nguồn YouTube cho Curb; mỗi lần chọn thư mục output mới:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_public_live.py --url 'https://www.youtube.com/watch?v=sJvEFrG0wq0' --serve-only --seconds 0 --port 18768 --out outputs/youtube-operator-new
```

Thêm camera HTTP theo địa chỉ mà script in ra. Với RTSP/HTTPS được chủ camera công bố hoặc cấp quyền, thêm URL tương ứng trực tiếp vào Curb, kiểm tra có hình rồi đặt vùng. Không dùng danh sách camera cá nhân thiếu bảo vệ hoặc thử thông tin đăng nhập.

Các giới hạn còn lại: chưa kiểm tra RTSP tại một điểm lắp đặt do người dùng quản lý, nhiều camera, vận hành dài giờ, độ chính xác live độc lập hoặc bản cài CUDA mới. Kết quả hiện đủ mô tả các lượt chạy hữu hạn đã hoàn tất và các lỗi đã gặp.
