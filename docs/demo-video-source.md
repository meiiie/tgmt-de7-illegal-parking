# Video mẫu đường phố

Từ Curb 1.0.1, mẫu mặc định là **MERL Street Scene, Test006**, đoạn 30 giây đầu. Camera cố định trên cao nhìn xuống đường hai chiều, thấy ba ô tô đỗ dọc lề phải và phương tiện khác đi qua. Không có khung nhận diện dựng sẵn trong đầu vào.

- Tác giả dữ liệu: Mitsubishi Electric Research Laboratories (MERL), 2023; Michael Jones và Bharathkumar Ramachandra.
- [Bản phát hành v1, 25/03/2024 trên Zenodo](https://zenodo.org/records/10870472), DOI `10.5281/zenodo.10870472`.
- [Giới thiệu của MERL](https://www.merl.com/demos/video-anomaly-detection).
- Giấy phép dữ liệu và video mẫu chuyển đổi: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Giữ ghi nguồn, liên kết giấy phép, thông tin biến đổi và cùng giấy phép cho video/ảnh phái sinh được chia sẻ. MERL không bảo chứng ứng dụng này.
- Trích dẫn nghiên cứu: Ramachandra, B.; Jones, M., “Street Scene: A new dataset and evaluation protocol for video anomaly detection”, WACV 2020, trang 2569–2578.

## Biến đổi và tái tạo

Nguồn cung cấp frame 1280 × 720 ở 15 FPS. Lấy frame `00001, 00004, …, 00448` của `Test006`, ghép thành 150 frame ở 5 FPS, 30 giây, H.264 yuv420p, không âm thanh. Giữ nguyên tốc độ thời gian, không lặp frame để kéo dài thời gian dừng. Các clip/ảnh kết quả của Curb có thêm polygon, box, ID và thời gian cảnh báo.

Chạy `scripts/download-demo.ps1`. Script `download_demo.py` dùng HTTP Range để tải riêng 150 frame được liệt kê trong `scripts/demo-frames.json`, kiểm tra Content-Range, tên file, kích thước và CRC của từng mục ZIP. Không tải toàn bộ archive 49 GB. Cache có thể tiếp tục khi chạy lại. Video nằm tại `data/streetscene_test006_30s.mp4`; danh sách SHA-256 frame nguồn và hash video được ghi vào `.provenance.json` bên cạnh. Toàn bộ MD5 archive trong manifest chỉ là giá trị do nhà phát hành công bố, không phải hash đã kiểm tra toàn bộ archive.

## Phạm vi minh họa

Vùng mẫu bám mép lề phải, ngưỡng 20 giây, nhãn **theo dõi**. Vùng này minh họa phép đo dừng lâu; không có căn cứ để kết luận các ô tô đỗ hợp pháp hay trái phép ở địa điểm gốc. Cảnh báo cần người duyệt và quy định của địa điểm.

Tên `Test006` thuộc cách chia của MERL. Vì đoạn này đã được xem và chọn để cấu hình demo, nó **không còn là tập kiểm tra độc lập cho Curb**. Không huấn luyện mô hình hoặc công bố precision/recall từ mẫu này.

Mẫu Gaithersburg cũ và các kết quả kiểm chứng trước đây được giữ nguyên. [Ghi nguồn mẫu cũ](legacy-demo-video-source.md); `scripts/download-legacy-demo.ps1` tái tạo fixture cho `scripts/verify_curb.py`.
