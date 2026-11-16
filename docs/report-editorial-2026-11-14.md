# Biên tập báo cáo và hình vẽ — 14/11/2026

Bản mới: `E:/Downloads/de7-bien-tap-tieng-viet-va-hinh-ve-2026-11-14.docx`.
Giữ nguyên `de7.docx` và bản thực nghiệm đã giao trước đó. Cả 19 bảng được
đối chiếu từng ô với bản trước; không sửa kết quả v4/v5/v6 hoặc các lượt GTX 1650.

## Nguồn hướng dẫn đã áp dụng

- [Việt ngữ toàn thư](https://github.com/meiiie/meiiie_skillls/tree/main/viet-ngu-toan-thu),
  bản 3.0.0: đọc hướng dẫn thể loại, ngữ vực, nhân quả, chính tả và kiểm tra;
  làm rõ chủ thể, điều kiện và phạm vi câu. Rà sáu bất biến và chạy
  `viet_guard.py check/verify` với nhận xét từng dấu hiệu thay đổi. Công cụ
  kiểm chuỗi và hash; không chứng nhận tính đúng về nghĩa hoặc thay tác giả duyệt bài.
- [Scientific Figure Making](https://github.com/ChenLiu-1996/figures4papers/tree/main/scientific-figure-making):
  dùng Matplotlib, trục rõ, số liệu trực tiếp, màu và nét gạch phân biệt khi in
  xám. Xuất PNG 300 dpi, PDF và SVG. Bộ màu theo người dùng: `#2B3B79`,
  `#0B0B0B`, `#E4E4E4`.
- [Anti-Defensive Writing](https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill):
  nêu kết quả trước, bỏ lời rào đón lặp; giữ đầy đủ số đo bất lợi và giới hạn
  thực nghiệm. Không dùng hướng dẫn viết để che kết quả hoặc mở rộng kết luận.

Ba skill đã được cài vào thư mục skill của người dùng. Mã và dữ liệu skill
không được đưa vào dự án Curb.

## Hình mới

1. Hình 4.1: đối chiếu TP/FP/FN của v5 trên Tesla T4, đọc từ
   `results/de7_v5_results.json`. Thêm DINOv3 tăng FP từ 5 lên 8; TP và FN giữ nguyên.
2. Hình 4.11: FPS nhận và FPS toàn lượt của ba nguồn camera, đọc từ
   `outputs/report-review-2026-11-14/camera-api-results.json`. Mỗi nguồn một lượt;
   đây không phải phép đo tốc độ tối đa hoặc so giao thức có kiểm soát.
3. Hình 3.7: luồng Curb có bản vá nhận khung mới nhất, đối chiếu mã nguồn.
   DINOv3 thuộc nhánh nghiên cứu, không có trong worker Curb đã chạy.

Mã tạo hình, hash đầu vào/đầu ra, bản biên tập và hồ sơ kiểm tra nằm trong
`outputs/report-polish-2026-11-14/`. Matplotlib 3.11.2 chạy từ thư viện tạm
ngoài dự án; không thay môi trường suy luận đã dùng cho các số đo GPU.

## Ảnh giao diện mới

Đã mở Curb desktop 1.1.0 trên Windows qua Computer Use; chọn nguồn Street
Scene bằng bộ chọn nguồn, xem vùng giám sát và mở hồ sơ đã lưu. Ba ảnh JPG
1536 × 816 được lưu trực tiếp từ ảnh cửa sổ; không dựng lại giao diện.

Các ảnh chụp bộ cài **CPU** đang mở dữ liệu minh họa có trước. Chúng không
ghi nhận lượt suy luận GPU mới. Số đo GTX 1650 và ảnh camera trước đó thuộc
bản nguồn CUDA, dùng dữ liệu riêng ở cổng 18770. Yêu cầu mở trang lượt
YouTube đã hoàn tất được gửi tới khung bên phải của Codex; công cụ trả về
`queued`, không cung cấp xác nhận hình ảnh của chính khung Codex.

Nguồn video: Jones và Ramachandra, MERL, Street Scene, [Zenodo v1](https://zenodo.org/records/10870472).
Dữ liệu MERL 2023, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Ảnh phái sinh có thêm vùng, hộp và mã xe; giữ giấy phép và ghi nguồn. Đoạn
Test006 đã dùng làm demo/phát triển, không phải tập kiểm tra độc lập cho Curb.

## Kiểm chứng bản giao

- Microsoft Word cập nhật mục lục, danh mục hình/bảng và xuất PDF để kiểm bố cục.
- Render toàn bộ trang bằng Poppler; so pixel phần thân trang với bản trước,
  xem trực tiếp các trang thay đổi và các hình mới.
- Kiểm hash tệp gốc, bản giao trước, ba hình xuất đủ chín tệp và ảnh giao diện.
- Giữ bảng 4.10 cùng trang để tránh tách ba nguồn camera qua hai trang.
- Bản Word mới và ZIP minh chứng được tạo riêng; không commit, push hoặc phát hành.

Lượt này chỉ biên tập, vẽ hình từ kết quả đã lưu và thao tác xem giao diện.
Không huấn luyện hoặc chạy thêm thí nghiệm GPU; các kết quả mới nhất vẫn là
các lượt đã ghi trong [hồ sơ camera](curb-camera-and-report-2026-11-14.md).
