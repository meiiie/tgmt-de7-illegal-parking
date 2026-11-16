# Đối chiếu báo cáo sau bảo vệ: AI City Track 4 và vai trò DINOv3

Ngày đối chiếu: 14/11/2026. Người dùng đã xác nhận là **Track 4**. Tài liệu này cung cấp nội dung thay thế cho phần phương pháp, thực nghiệm và kết luận. Chưa tìm thấy tệp báo cáo Word hoặc LaTeX gốc trong thư mục dự án nên chưa sửa trực tiếp bản nộp.

**Cập nhật sau bước đối chiếu ban đầu:** đã tải archive đầy đủ, giải nén 100 train, chạy mới 9 video bằng engine Curb và sửa đường nhận camera. Xem [thực nghiệm mới và bản sửa realtime](realtime-and-aicity-2026-11-14.md). Các bảng lịch sử và lượt camera đầu bên dưới được giữ để đối chiếu; không phải trạng thái cuối của ngày.

## Phạm vi bài toán và dữ liệu

Bộ dữ liệu trong các artifact nghiên cứu là **AI City Challenge 2021 Track 4 – Traffic Anomaly Detection**. Trang chính thức mô tả 100 video huấn luyện và 150 video kiểm tra, mỗi video khoảng 15 phút, 30 FPS, độ phân giải 410p. Các bất thường thường gặp gồm tai nạn và xe bị dừng; ùn tắc thông thường và xe đỗ trong khu vực đỗ thông thường không được xem là bất thường. Nguồn: [dữ liệu và đánh giá 2021](https://www.aicitychallenge.org/2021-data-and-evaluation/), [FAQ Track 4](https://www.aicitychallenge.org/2021-faqs/).

Các thử nghiệm của dự án dùng **tập con của train**, chưa phải kết quả trên toàn bộ test hoặc điểm leaderboard. Tập con này đã được dùng để xem lỗi và chọn ngưỡng, vì vậy phải gọi là tập phát triển. Nó cũng không có đủ nhãn biển báo, thời gian cấm và quy định tại vị trí để tự kết luận đỗ xe trái phép.

Đoạn có thể đưa vào báo cáo:

> Hệ thống được thử nghiệm phát hiện phương tiện dừng lâu trên một tập con của AI City Challenge 2021 Track 4. Dữ liệu gốc đánh giá bất thường giao thông, gồm xe bị dừng và tai nạn, không phải nhãn chuyên biệt cho đỗ xe trái phép. Trong phạm vi nghiên cứu, vùng giám sát và ngưỡng thời gian được cấu hình trước; cảnh báo cần người vận hành kiểm tra theo điều kiện tại địa điểm. Các số liệu dưới đây là kết quả phát triển theo bộ chấm của dự án, không phải điểm đánh giá chính thức của cuộc thi.

## DINOv3 làm gì khi đã có YOLO26s?

| Thành phần | Đầu vào và đầu ra | Vai trò trong dự án |
|---|---|---|
| YOLO26s | Ảnh → hộp giới hạn, lớp xe và điểm phát hiện | Phát hiện phương tiện trên từng khung hình |
| ByteTrack | Detection theo thời gian → ID và quỹ đạo | Liên kết các quan sát liên tiếp |
| DINOv3, tùy chọn trong nhánh nghiên cứu | Ảnh cắt phương tiện → vector đặc trưng | So sánh ngoại hình khi nối lại track bị mất, hỗ trợ kế thừa thời gian dừng |
| Quy tắc sự kiện | Vùng, chuyển động, thời gian và lịch → cảnh báo | Xác định tình huống dừng vượt ngưỡng |

Theo [tài liệu Meta](https://ai.meta.com/research/publications/dinov3/) và [bài báo DINOv3](https://arxiv.org/abs/2508.10104), DINOv3 học biểu diễn thị giác dùng cho nhiều tác vụ. Bản backbone không tự tạo quyết định đỗ xe trái phép. Trong mã nghiên cứu `src/pipeline.py`, lớp `Reid` cắt ảnh trong bbox, lấy `pooler_output`, chuẩn hóa vector và so sánh cosine. Nhánh YOLO chỉ xét track mất dấu có IoU ít nhất 0,5; khi cosine vượt ngưỡng, track mới kế thừa lịch sử, vùng và timer của track cũ. Đây là giả thuyết kỹ thuật cần được kiểm chứng bằng thí nghiệm có/bỏ thành phần.

Ví dụ: một xe dừng bị xe tải che khuất rồi xuất hiện với ID mới. YOLO vẫn phát hiện được xe ở từng thời điểm, nhưng timer có thể bị tách theo ID. So sánh đặc trưng có thể giúp nối lại lần dừng. Nếu nối nhầm hai xe giống nhau thì timer lại bị cộng sai, làm tăng cảnh báo giả. DINOv3 không bắt buộc để hệ thống hoạt động và không bảo đảm giải quyết mọi trường hợp che khuất.

**Bản Curb 1.1.0 hiện dùng YOLO26s + ByteTrack và quy tắc sự kiện; không tích hợp DINOv3 trong worker sản phẩm.** Không nên vẽ DINOv3 như thành phần bắt buộc của sơ đồ ứng dụng đã phát hành.

Câu trả lời ngắn cho thầy:

> Em dùng YOLO26s để phát hiện phương tiện, ByteTrack để duy trì ID giữa các khung hình. DINOv3 là nhánh thử nghiệm bổ sung đặc trưng ngoại hình để nối lại track sau mất dấu, nhằm tránh làm gián đoạn thời gian dừng. Tuy nhiên, em phải kiểm tra lợi ích bằng thực nghiệm. Trên tập con 9 video, thêm DINOv3 làm F1 giảm từ 0,500 xuống 0,421 và tăng số cảnh báo giả từ 5 lên 8. Vì vậy em chọn YOLO26s + ByteTrack cho bản chính, còn DINOv3 được trình bày là nhánh khảo sát chưa chứng minh lợi ích ổn định.

## Số liệu nghiên cứu đã lưu và cách trình bày

Ở bước đối chiếu ban đầu ngày 14/11/2026 chỉ kiểm tra lại artifact, phép tính và mã cấu hình, **chưa chạy lại suy luận AI City**. Lượt suy luận Curb thực hiện sau đó được ghi riêng trong tài liệu cập nhật phía trên. Lệnh kiểm tra [script](../scripts/audit_research_results.py):

```powershell
.venv/Scripts/python.exe -X utf8 scripts/audit_research_results.py --output outputs/research-2026-11-14/history-audit.json
```

Kết quả: 14 dòng CSV có P/R/F1 khớp TP/FP/FN trong dung sai làm tròn; các trường v5 khớp JSON. Tại thời điểm đối chiếu ban đầu chưa có raw alerts v5 hoặc video AI City gốc trong các thư mục đã kiểm tra ở checkout này để ghép sự kiện và chấm lại từ đầu. Việc số học khớp không thay thế tái lập suy luận.

### So sánh v5 trên cùng 9 video

Nguồn: [JSON v5](../results/de7_v5_results.json), [CSV lịch sử](../results/aic21_table.csv), [notebook snapshot v5](../kaggle/kernel_v5/de7_v5_diag_aic9.ipynb).

| Cấu hình | TP | FP | FN | Precision | Recall | F1 | FPS pipeline đã lưu | VRAM đỉnh MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| YOLO26s + ByteTrack | 4 | 5 | 3 | 0,444 | 0,571 | 0,500 | 34,30 | 100,0 |
| Thêm DINOv3 ViT-S/16 | 4 | 8 | 3 | 0,333 | 0,571 | 0,421 | 33,08 | 174,9 |

- Video: 2, 9, 11, 14, 33, 35, 58, 62, 7. Có 7 sự kiện trong nhãn được chọn; 6 video dương và 3 video âm. Notebook chọn 6 video dương đầu tiên và lấy mẫu 3 video âm với `random.seed(0)`; không phải chia test ngẫu nhiên độc lập.
- Theo lệnh và mã nhúng v5: YOLO26s, `bytetrack.yaml`, `imgsz=640`, `conf=0.25`, `stride=15`, không giới hạn `max_frames`; tại 30 FPS nguồn tương ứng lấy mẫu khoảng 2 FPS. Tổng 15.079 khung được xử lý. Không truyền `--half`; không suy ra YOLO dùng FP16 từ trường AMP chung của pipeline.
- ROI toàn khung; dwell 20 giây; cửa sổ đứng yên 3 giây; `still_tol=0.1`, `lost_grace_s=4`, `reid_keep_s=60`; ngưỡng cosine DINO 0,75, min-area 200 px² và gộp IoU 0,3 theo snapshot v5. GPU Tesla T4.
- MAE bắt đầu dừng đều 19,38 giây; độ trễ cảnh báo trung bình đều 36,88 giây trên các TP ghép được. Không phải độ trễ truyền mạng.
- Artifact cũ chưa ghi đủ hash trọng số và toàn bộ phiên bản dependency để bảo đảm tái tạo nguyên trạng. Không gán hash trọng số của lượt live mới cho thí nghiệm lịch sử.

FPS ở bảng là số **khung lấy mẫu** chia thời gian pipeline theo cách đo cũ. Nó không chứng minh hệ thống xử lý mọi khung hình của camera 30 FPS; cũng không bao trọn thời gian nạp DINOv3 và xuất video của giao diện.

### Tránh chọn riêng kết quả thuận lợi

| Phạm vi khác | Cấu hình | TP/FP/FN | F1 | Ghi chú |
|---|---|---|---:|---|
| v4, 4 video, cửa sổ 240 giây, 1 FPS | YOLO26s + ByteTrack | 3/0/1 | 0,857 | Theo dòng CSV v4 |
| Cùng phạm vi v4 | Thêm DINOv3 | 4/1/0 | 0,889 | Recall tăng, nhưng MAE bắt đầu 60,50 giây và độ trễ 81,50 giây |
| v6, 9 video, cửa sổ 240 giây, 1 FPS | YOLO26s + ByteTrack | 3/0/2 | 0,750 | Chỉ 5 sự kiện trong cửa sổ; không so trực tiếp với 0,500 của v5 |

V4 cho thấy DINOv3 có thể hữu ích ở một phạm vi hẹp; v5 chưa chứng minh lợi ích trên phạm vi rộng hơn. Không kết luận DINOv3 luôn tốt hơn hoặc luôn vô ích. SAM 3.1 là một nhánh khác: v6 chạy 8 video, thiếu video 62, nên không coi là đối chứng cùng tập đầy đủ với YOLO v6.

## Bộ chấm cũ khác giao thức chính thức

`src/evaluate.py` ghép tham lam theo thời điểm cảnh báo tăng dần, cùng video và vùng, chấp nhận cảnh báo từ đầu sự kiện đến cuối sự kiện cộng 30 giây. Nó trả P/R/F1, MAE của thời điểm bắt đầu dừng và độ trễ cảnh báo trung bình.

Trang đánh giá AI City dùng F1 và RMSE thời điểm; FAQ minh họa vùng chấp nhận TP từ **10 giây trước đầu đến 10 giây sau cuối sự kiện**, ví dụ 454–567 giây tương ứng 444–577 giây. Mô tả chọn dự đoán có confidence cao nhất và yêu cầu ghép một-một. FAQ còn nêu gộp các bất thường kế tiếp trong vòng 2 phút; không được bỏ qua quy ước này khi viết bộ chấm mới. Trang Evaluation và FAQ có diễn đạt khác nhau về RMSE; muốn tái lập điểm chính thức phải lấy evaluator của đúng kỳ và đối chiếu, không tự suy đoán công thức từ một câu mô tả.

Do đó, **không đổi tên F1 cũ thành “F1 theo AI City”**, không đổi MAE thành RMSE và không so thẳng với leaderboard. Cũng không đổi `tol=30` thành 10 rồi giữ nguyên kết quả cũ. Muốn chấm lại cần raw predictions gồm video, timestamp và confidence, nhãn gốc, quy tắc hợp nhất sự kiện và bộ chấm được cố định trước khi đánh giá.

## Thử luồng công khai Đà Nẵng ngày 14/11/2026

Nguồn: [Camera cổng trường Nguyễn Huệ Đà Nẵng](https://www.youtube.com/watch?v=sJvEFrG0wq0), kênh Phát Triển Đà Nẵng, video ID `sJvEFrG0wq0`. ID video YouTube không phải ID của từng phương tiện. Đã lấy được metadata live và giải mã hình 854×480 qua FFmpeg. OpenCV mở trực tiếp URL HLS của lần probe đầu bị timeout/TLS; đây là kết quả kết nối cụ thể, không kết luận mọi camera HTTP/RTSP đều lỗi.

Lượt đầu chạy bằng harness phiên bản ban đầu, khi chưa sửa worker Curb. [Script hiện tại](../scripts/verify_public_live.py) đã được sửa trong lượt tiếp theo; bản đầu được giữ cục bộ ở `outputs/research-2026-11-14/verify_public_live-v1.py` với SHA-256 `0f07e344df0d20043a89489aa8625a50a6358ebc0736f3f12bb296d1f58d319d`. Lệnh lúc thử đầu:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_public_live.py --url 'https://www.youtube.com/watch?v=sJvEFrG0wq0' --seconds 120 --device cuda --out outputs/research-2026-11-14/live-120s
```

Lệnh yêu cầu thư mục đích mới; dùng tên thư mục khác khi chạy lại. Harness resolve HLS bằng yt-dlp IPv4, FFmpeg `-re` và `fps=5`, chuyển JPEG mới nhất qua HTTP loopback để worker camera của Curb đọc. Đây là luồng live qua cầu nối, không phải tính năng nhập trực tiếp trang YouTube đã tích hợp trong giao diện và không phải thử RTSP vật lý.

| Thông số quan sát | Kết quả |
|---|---:|
| Cửa sổ yêu cầu | 120 giây |
| Thời gian từ lúc mở nguồn theo đồng hồ worker | 120,625 giây |
| Thời gian toàn lượt theo worker | 129,889 giây |
| Khung hình xử lý | 74 |
| Quan sát detection có ID | 315 |
| Mục tiêu lấy mẫu | 5 FPS |
| Tốc độ toàn lượt đạt được | 0,570 khung/giây |
| Tổng thời gian gọi phát hiện/theo dõi | 5,938 giây |
| VRAM tensor đỉnh do PyTorch ghi | 110,52 MB |
| Cảnh báo dừng lâu | 0 |
| Cảnh báo timeout đọc luồng trong log | 17 |
| Khung do cầu nối tạo trong toàn lượt harness | 120 |

Cấu hình: GTX 1650, Python 3.12.2, PyTorch 2.11.0+cu126, Ultralytics 8.4.184, OpenCV 4.12.0.88; YOLO26s + ByteTrack, float32, seed 0, ảnh suy luận 640, confidence 0,3, min-area 200 px², cửa sổ đứng yên 2 giây, dung sai chuyển động 0,18, lost grace 1,5 giây, dwell 20 giây, bật chặn ùn xe. ROI mặt đường là vùng theo dõi thử, chưa gán nhãn vi phạm. Không lưu video toàn lượt; có ảnh đầu và ảnh preview cuối để kiểm tra trực quan.

Kết luận: lượt chạy kết thúc và có xử lý ảnh thật, nhưng **chưa đạt mục tiêu realtime 5 FPS trên đường nhận luồng này**. Tổng thời gian model thấp hơn nhiều thời gian toàn lượt; log timeout và số frame cầu nối thấp cho thấy cần điều tra thêm phần nhận luồng/cầu nối trước khi quy nguyên nhân cho GPU. Chưa đo được độ trễ camera gốc đến cảnh báo, chưa có nhãn sự kiện độc lập, chưa tính được precision/recall/F1. Không coi 0 cảnh báo là 100% đúng.

Kiểm tra trực quan hai ảnh: đồng hồ do nhà cung cấp ghi trên ảnh đầu là **12:30:05**, ảnh preview cuối là **12:30:29**, chỉ tiến 24 giây. Đây không phải 120 giây nội dung camera liên tục. `source_seconds` của worker camera đang tính bằng thời gian thực trên máy; không được dùng trường đó để khẳng định luồng đã bám kịp camera. Đồng hồ camera chưa được đối chiếu đồng bộ độc lập nên chưa thể suy ra độ trễ tuyệt đối từ hai ảnh. Cần xử lý phần nhận hình và kiểm chứng timestamp trước khi báo cáo độ trễ hay thời gian dừng trên luồng này.

Manifest, cấu hình, hash code/model, ảnh và log gốc nằm ở `outputs/research-2026-11-14/` trên máy. [Bằng chứng tóm tắt](research-evidence-2026-11-14.json) không chứa URL CDN có chữ ký, địa chỉ mạng của máy hoặc hình camera. Giữ media thô cục bộ trong lượt đối chiếu này.

## Phần cần bổ sung trước bản báo cáo cuối

1. Đưa đúng số liệu và điều kiện đo ở trên vào phần thực nghiệm. Tách nghiên cứu cũ `src/` với ứng dụng Curb `curb/`; không gán F1 của pipeline cũ cho engine mới.
2. Khi có video AI City và raw predictions, tái lập trên dữ liệu được phép sử dụng, cố định evaluator và ngưỡng. Chia phát triển/kiểm tra theo video hoặc camera, tránh cùng nguồn xuất hiện ở cả hai tập.
3. Với camera Đà Nẵng, chọn trước các đoạn gồm di chuyển, dừng thật, che khuất và ùn xe; gán nhãn trước khi xem kết quả. Giữ một phần độc lập và có người đối chiếu nhãn.
4. So YOLO26s + ByteTrack có/bỏ DINOv3 trên cùng dữ liệu, phần cứng, lấy mẫu và quy tắc; báo cáo FP/giờ, bỏ sót, độ trễ cảnh báo và đứt/nối nhầm ID. Chỉ dùng IDF1/HOTA khi có nhãn định danh track phù hợp.
5. Đo luồng trực tuyến lâu hơn sau khi sửa điểm nghẽn nhận hình: tỷ lệ thời gian nhận được hình, timeout/kết nối lại, số khung xử lý, khoảng trống giữa các quan sát và độ trễ có mốc thời gian kiểm chứng. Lượt 120 giây này chưa chứng minh khả năng hoạt động liên tục.
