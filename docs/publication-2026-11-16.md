# Công bố mã nguồn và báo cáo ngày 16/11/2026

Phạm vi: đưa bản vá tiếp nhận camera, công cụ tái hiện thực nghiệm, hồ sơ kết
quả ngày 14/11 và báo cáo Curb ba chương lên kho GitHub hiện có.

- `curb/capture.py` giữ khung mới nhất trên luồng nhận riêng; worker lập lịch
  camera và ghi số timeout, nối lại, khung bỏ qua, tuổi khung sau giải mã.
- Các script tải/kiểm tra dữ liệu AI City, đánh giá tập con, thử YouTube và
  đo truyền tải được kèm trong `scripts/`.
- Báo cáo Word ở [docs/report](report/README.md), 36 trang; kèm bốn hình SVG
  và SHA-256. README chính dẫn tới báo cáo và các kết quả có ghi phạm vi.

Kiểm tra cục bộ ngày công bố:

| Kiểm tra | Kết quả |
|---|---|
| Unittest từ mã nguồn hiện tại | 35/35 đạt; gồm hai ca bộ đệm camera |
| Frontend TypeScript và Vite | Build thành công |
| Đồng nhất phiên bản | Curb 1.1.0 khớp các khai báo |
| Đối chiếu kết quả lịch sử | 14 hàng; JSON v5 và CSV khớp số đếm |
| Quét tệp nguồn | Không phát hiện token/khóa riêng hoặc tệp quá 10 MB |
| Báo cáo công bố | 36 trang, ba chương; 39 mục lục và 18 tham chiếu khớp trang |
| Bố cục báo cáo | 36/36 ảnh trang giống từng pixel với bản đã duyệt ngày 14/11 |

Unittest dùng CPython 3.12.10 và các dependency trong runtime desktop đã cài,
nhưng import mã `curb/` hiện tại của kho. Môi trường `.venv` cục bộ thiếu
executable tại thời điểm kiểm tra; không sửa hoặc thay runtime của người dùng.
Lượt này không chạy lại suy luận GPU, camera trực tuyến hoặc 24 ca tích hợp.

Bản Word được dựng lại từ nguồn biên tập đã giữ và cập nhật trường bằng Word;
nội dung, bảng, ảnh và từng pixel trang khớp bản đã duyệt. Hash của gói DOCX
công bố khác do metadata lưu tệp; checksum thực nằm trong
[SHA256SUMS.txt](report/SHA256SUMS.txt).

Giữ nguyên bộ cài và tag 1.1.0. Bản vá camera trong commit mới chưa được đóng
vào bộ cài CPU cũ. Không gắn số đo GTX 1650 cho tốc độ của bộ cài đó. Dataset,
trọng số, cơ sở dữ liệu, URI camera vận hành và log riêng không được công bố.
