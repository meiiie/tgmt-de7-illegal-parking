# AI City đã tải, lần chạy mới và bản sửa nhận camera

Ngày 14/11/2026. Các thay đổi và thực nghiệm trong tài liệu này thực hiện cục bộ, dựa trên commit `06f38bc6bff630c8b3dcd3a4c8892fd70a3715fe` có bản vá chưa commit. Không phải bản nhị phân Curb 1.1.0 đã phát hành trước đó. Hash mã thực sự được chạy nằm trong manifest từng job.

## Dữ liệu đã có trên máy

Nguồn gốc là [trang tải AI City Challenge 2021 Track 4](https://www.aicitychallenge.org/2021-track4-download/), dẫn trực tiếp tới [AICity21-Track4-Anomaly-Detection.zip trên Google Drive](https://drive.google.com/file/d/1gsR4pIEiWK7htPmIjiZjXetaa1X-T-Am/view). Đây cũng là file ID được notebook nghiên cứu cũ sử dụng.

Đã tải xong archive **15.060.951.187 byte**, gồm **100 train + 150 test**. Tệp nằm tại `C:\Users\Admin\CurbResearch\aicity-2021-track4\AICity21-Track4-Anomaly-Detection.zip`; SHA-256: `e2cf0957af3e666a3049aca677a0ddcb119308023d941cd0c494fa04bc6d6c22`. Đã mở central directory và đọc nhãn có kiểm tra CRC; chưa kiểm tra CRC toàn bộ 150 video test.

Đã giải nén **100/100 video train** cùng `train-anomaly-results.txt` và `ReadMe.txt` tại:

```text
C:\Users\Admin\CurbResearch\aicity-2021-track4\train
```

Tổng dung lượng 100 video train là 4.716.410.162 byte. Từng video đã kiểm tra CRC theo header ZIP và tính SHA-256, lưu ở `train/training-manifest.json`. Trong lúc archive đầy đủ còn tải, script chỉ lấy những member đã tải trọn vẹn; không dùng member dở dang. Trạng thái archive đầy đủ và hash cuối được ghi riêng trong `download-manifest.json` sau khi tải xong lúc 13:09 ngày 14/11/2026. Trường `complete_archive_verified: false` trong manifest giải nén phản ánh thời điểm giải nén, không phải trạng thái tải cuối. **150 video test vẫn nằm trong ZIP, chưa giải nén/chấm; chưa chạy toàn bộ 100 train.**

Lệnh tái hiện tải, có tiếp tục tải và retry, dùng gdown trong môi trường tool riêng:

```powershell
uv tool run --from gdown==6.5.1 python -u scripts/download_aicity2021.py --directory C:/Users/Admin/CurbResearch/aicity-2021-track4
```

Không đưa video, archive hoặc hình camera lên Git. Giữ nguyên JSON/CSV/ngưỡng thực nghiệm lịch sử.

## Lượt AI City mới, chạy bằng engine Curb

```powershell
.venv/Scripts/python.exe -X utf8 scripts/evaluate_aicity_local.py --train C:/Users/Admin/CurbResearch/aicity-2021-track4/train --window 240 --sample-fps 1 --device cuda --out outputs/realtime-fix-2026-11-14/aicity-curb-9x240s
```

Đây là lượt suy luận mới ngày 14/11/2026 trên 240 giây đầu của 9 video train: 2, 9, 11, 14, 33, 35, 58, 62 và 7. Có 5 sự kiện GT bắt đầu trong cửa sổ. Các ID này từng được dùng để chọn ngưỡng nên vẫn là tập phát triển, không phải kiểm tra độc lập.

Cấu hình: YOLO26s + ByteTrack, ảnh suy luận 640, confidence 0,25, float32, seed 0, lấy mẫu 1 FPS, ROI toàn khung, dwell 20 giây, cửa sổ đứng yên 3 giây, dung sai chuyển động 0,1, lost grace 4 giây, min-area 200 px², bật chặn ùn xe, không ghi video toàn lượt. Phần cứng GTX 1650; Python 3.12.2, PyTorch 2.11.0+cu126, Ultralytics 8.4.184, OpenCV 4.12.0.88. Không huấn luyện mới, không dùng DINOv3.

| Video | Khung đã xử lý | TP | FP | FN |
|---|---:|---:|---:|---:|
| 2 | 240 | 0 | 0 | 0 |
| 9 | 240 | 0 | 0 | 1 |
| 11 | 240 | 0 | 0 | 1 |
| 14 | 240 | 0 | 0 | 0 |
| 33 | 240 | 2 | 0 | 0 |
| 35 | 240 | 1 | 0 | 0 |
| 58 | 240 | 0 | 0 | 0 |
| 62 | 240 | 0 | 0 | 0 |
| 7 | 240 | 0 | 0 | 0 |
| **Tổng** | **2.160** | **3** | **0** | **2** |

Precision **1,000**, Recall **0,600**, F1 **0,750**; MAE bắt đầu dừng **19,33 giây**, độ trễ cảnh báo trung bình **39,33 giây** trên các TP được ghép. Tổng thời gian worker 172,522 giây, tương ứng 12,520 khung lấy mẫu/giây. Đây là xử lý video ngoại tuyến; nguồn chỉ lấy mẫu 1 FPS, không phải suy luận mọi khung hình camera 30 FPS.

Bộ chấm là `src/evaluate.py`, ghép thời gian với dung sai 30 giây. **Các số này không phải điểm chính thức AI City**, không phải accuracy đỗ trái phép và không chứng minh không có cảnh báo giả trên camera khác. Không có GT không gian để chấm đúng xe. Hai video 2 và 14 có sự kiện ở ngoài cửa sổ 240 giây nên không được tính là sự kiện bị bỏ sót trong bảng này.

F1 tổng bằng v6 lịch sử nhưng không gọi là tái lập nguyên trạng v6: engine, phần cứng và cách lấy mẫu theo FPS nguồn có khác. V6 cũ xử lý 2.165 khung vì video có FPS phân số; lượt mới xử lý 2.160 khung. Dữ liệu, hash model và hash code của lượt mới được lưu ở `outputs/realtime-fix-2026-11-14/aicity-curb-9x240s/`.

## Vì sao lượt YouTube đầu chỉ đạt 0,57 FPS?

Lượt đầu có 74 khung/120,625 giây đồng hồ nhận luồng, 17 timeout đọc ảnh. Thời gian gọi phát hiện/theo dõi chỉ 5,938 giây trong 129,889 giây toàn worker. Do đó cần đo chặng nhận/giải mã ảnh trước khi đổi mô hình.

Các phép dò cho thấy:

- yt-dlp cũ 2026.03.17 trả các format HLS ghép âm thanh/hình, trong các lần dò sau có manifest HTTP 200 nhưng URL segment HTTP 403. Không dùng các lần không có ảnh đó để kết luận tốc độ mô hình bằng 0.
- yt-dlp 2026.10.26 lấy được HLS video-only format 231, 854×480, 30 FPS, từ cùng camera. Không hard-code format 94 của bộ lấy URL cũ.
- Với nguồn mới, phép dò 30 giây có `-re` nhận 44 ảnh, chờ ảnh đầu 21,015 giây; bỏ `-re` nhận 190 ảnh nhưng có khoảng trống gần 6 giây giữa các đợt. Đây là các phép dò truyền tải một lượt ở thời điểm khác nhau, không phải benchmark độ chính xác hoặc bằng chứng một cờ luôn cải thiện mọi mạng.
- HLS tải theo segment. Vừa tránh đọc chậm ở đầu vào, vừa cần đưa ảnh ra theo PTS để không dồn ảnh thành đợt. [FFmpeg mô tả `-re` chủ yếu để mô phỏng đầu vào thời gian thực](https://ffmpeg.org/ffmpeg.html); dùng nó trên nguồn live phải thận trọng.
- Curb cũ đọc và suy luận nối tiếp. Khi xử lý chậm hoặc ảnh tới theo đợt, hàng đợi ảnh và lịch lấy mẫu dựa trên thời điểm nhận có thể làm mất nhịp hoặc tăng độ trễ.

## Bản sửa đã chạy

1. Nguồn YouTube thử nghiệm dùng extractor được pin, HLS video-only, IPv4, bắt đầu ở các segment cuối. FFmpeg không dùng `-re`; bản đầu xuất `fps=10,realtime=limit=10`, bản cuối dùng **`fps=10,realtime=limit=60`** và flush từng packet qua cầu nối MJPEG cục bộ. Lý do sửa tiếp ngưỡng đồng hồ được kiểm chứng bên dưới. Mục tiêu suy luận vẫn là 5 FPS, không tăng số FPS báo cáo bằng lặp lại ảnh cũ.
2. `curb/capture.py` nhận ảnh trên luồng riêng và chỉ giữ ảnh mới nhất. Consumer chậm bỏ ảnh dư thay vì tích backlog. Không trả lại cùng một frame như một quan sát mới. Đóng nguồn đánh thức consumer đang chờ.
3. `curb/worker.py` lập lịch suy luận camera trước khi lấy ảnh mới nhất, thêm số timeout, reconnect, số ảnh bỏ qua và tuổi ảnh sau giải mã. Đường xử lý video tệp giữ cách lấy mẫu cũ.

Lượt kiểm tra camera thật 120 giây qua cầu nối với bản đầu, cùng YOLO26s + ByteTrack, ảnh suy luận 640, confidence 0,3, GTX 1650:

| Phép đo | Trước sửa | Sau sửa |
|---|---:|---:|
| Cửa sổ đồng hồ nhận luồng | 120,625 giây | 120,125 giây |
| Khung suy luận | 74 | 580 |
| Khung / giây từ lúc mở nguồn | 0,613 | **4,828** |
| Thời gian toàn worker, gồm khởi động/kết thúc | 129,889 giây | 156,285 giây |
| Khung / giây tính trên toàn worker | 0,570 | 3,711 |
| Thời gian gọi model/track | 5,938 giây | 45,266 giây |
| Timeout đọc ảnh | 17 cảnh báo trong log | **0 lần trong capture** |
| Reconnect | Chưa có bộ đếm tương ứng | **0** |
| Tuổi ảnh sau giải mã lớn nhất trong tiến trình | Chưa đo | **0,172 giây** |
| Khoảng cách ảnh cầu nối lớn nhất | Chưa đo | 0,422 giây |

Phải giữ cả hai mẫu số FPS để tránh làm đẹp số liệu: toàn worker gồm thời gian khởi động, còn số đo theo đồng hồ nhận luồng cho biết hệ thống có theo kịp luồng sau khi bắt đầu hay không. 0,172 giây là tuổi ảnh **kể từ khi tiến trình giải mã nhận ảnh**, không bao gồm camera, YouTube hoặc HLS.

Đồng hồ ghi trên ảnh cầu nối đầu là 12:52:25, preview cuối là 12:55:01: tiến 156 giây; khoảng cách thời điểm ghi hai ảnh là 156,002 giây. Toàn harness dài 158,666 giây vì còn phần mở/đóng. Chưa đồng bộ đồng hồ camera độc lập, nên chưa có độ trễ camera-gốc-đến-cảnh-báo được kiểm chứng.

## Thử 5 phút phát hiện lỗi đồng hồ và bản sửa cuối

Không dừng kết luận ở lượt 120 giây thuận lợi. Với cùng bản đầu (`limit=10`), lượt 300 giây tiếp theo xử lý 1.336 khung, 4,452 FPS theo đồng hồ nhận nguồn, nhưng có 4 timeout/kết nối lại và khoảng trống cầu nối 15,172 giây. Đồng hồ trên hình chỉ tiến từ **13:03:45 đến 13:08:23** (278 giây) trong **308,256 giây** giữa hai tệp ảnh. Độ trễ tăng khoảng **30,26 giây**; lượt này chưa bám kịp nội dung camera dù số FPS đã tốt hơn.

Đối chiếu [mã nguồn bộ lọc realtime của FFmpeg 7.1.1](https://github.com/FFmpeg/FFmpeg/blob/n7.1.1/libavfilter/f_realtime.c): khi độ lệch đồng hồ vượt `limit`, bộ lọc đặt lại mốc thời gian. Với `limit=10`, một đợt ngừng cung cấp ảnh hơn 10 giây có thể bị xem là nhảy timestamp và giữ lại độ trễ. Bản sửa tăng giới hạn lên 60 giây, cho phép đầu ra bắt kịp sau các khoảng ngừng ngắn hơn; bộ đệm chỉ giữ ảnh mới nhất bỏ phần ảnh cũ khi bắt kịp.

Đã tái hiện riêng bằng [phép thử đồng hồ](../scripts/verify_stream_clock.py): 32 giây ảnh tổng hợp, cố ý ngừng cấp ảnh 13 giây ở giây thứ 8. `limit=10` mất **44,828 giây**, có 1 lần đặt lại đồng hồ; `limit=60` mất **31,953 giây**, không đặt lại. Đây là kiểm tra cơ chế thời gian, không phải đánh giá mô hình.

**Lượt xác nhận cuối trên chính camera Đà Nẵng**, từ 13:14 đến 13:20, sau khi tải dữ liệu đã kết thúc:

| Phép đo | Bản cuối, 300 giây |
|---|---:|
| Khung suy luận | **1.475** |
| Khung / giây trong cửa sổ nhận nguồn | **4,917** |
| Toàn worker, gồm khởi động/kết thúc | 311,381 giây |
| Khung / giây trên toàn worker | **4,737** |
| Thời gian gọi model/track | 92,624 giây |
| Timeout / kết nối lại | **0 / 0** |
| Ảnh bỏ qua ở bộ đệm capture | 1.510 |
| Tuổi ảnh sau giải mã lớn nhất | **0,172 giây** |
| Khoảng trống ảnh cầu nối lớn nhất | 3,141 giây |
| VRAM tensor đỉnh | 110,52 MB |
| Cảnh báo tạo ra, chưa chấm đúng/sai | 6 |

Đồng hồ trên ảnh đầu **13:14:55**, preview cuối **13:20:06**, tiến **311 giây**. Khoảng cách thời điểm ghi hai tệp là **311,128 giây**, tương ứng độ trễ tăng xấp xỉ **0,13 giây**, trong độ phân giải đồng hồ ảnh 1 giây. Không quan sát thấy độ trễ tích lũy ở hai đầu lượt này. Không dùng chênh lệch đồng hồ camera và máy để kết luận độ trễ tuyệt đối vì chưa biết sai lệch đồng hồ nguồn.

Lượt cuối không gặp khoảng ngừng 13 giây; phép thử tổng hợp phía trên mới kiểm chứng khả năng bắt kịp sau khoảng ngừng đó. Các lượt live chạy ở thời điểm/mạng khác nhau; lượt 300 giây trước còn đồng thời tải dữ liệu. Không quy toàn bộ cải thiện cho riêng một cờ FFmpeg.

Preview cuối còn hiển thị trạng thái ùn xe trong khi có xe lưu thông. Quy tắc ùn xe hiện dựa trên tỷ lệ track đứng yên trong ROI, nên xe đỗ có thể làm trạng thái này nhạy quá mức. Chưa có nhãn độc lập để chấm 6 cảnh báo hay tính FP/giờ, bỏ sót và độ trễ sự kiện trên camera này. Kết quả tốc độ không chứng minh nghiệp vụ phát hiện đã đủ chính xác.

Đã chạy 35 unittest, gồm hai ca mới về bỏ backlog và không trả ảnh cũ sau đóng nguồn; tất cả đạt. 24 kiểm tra tích hợp thật cũng đạt, gồm phân tích video, camera HTTP phát lại, clip theo đồng hồ, dừng và báo mất kết nối. Camera HTTP phát lại không thay thế thử RTSP vật lý.

Bằng chứng đã bỏ URL CDN có chữ ký, ảnh và địa chỉ nội bộ: [JSON tổng hợp](realtime-and-aicity-evidence-2026-11-14.json). Log, ảnh và manifest gốc nằm ở `outputs/realtime-fix-2026-11-14/` trên máy.

## Cách chạy lại và giới hạn

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_public_live.py --url 'https://www.youtube.com/watch?v=sJvEFrG0wq0' --seconds 300 --device cuda --out outputs/live-new-run
```

Mỗi lần dùng một thư mục output mới. Cần FFmpeg, uv, môi trường Python của repo có PyTorch CUDA và trọng số YOLO26s. Script tự lấy URL mới; URL CDN tạm không được lưu vào tài liệu công khai. Media camera chỉ lưu cục bộ trong lượt nghiên cứu.

Để cấp camera YouTube cho giao diện Curb thay vì tự chạy một job kiểm tra:

```powershell
.venv/Scripts/python.exe -X utf8 scripts/verify_public_live.py --url 'https://www.youtube.com/watch?v=sJvEFrG0wq0' --serve-only --seconds 0 --port 18768 --out outputs/live-operator-new
```

Mở `Start-Curb.cmd`, thêm nguồn loại camera với địa chỉ `http://127.0.0.1:18768/live`, cấu hình vùng và chọn CUDA trong cài đặt trên máy có môi trường này. Giữ tiến trình cầu nối chạy; Ctrl+C để dừng. Chế độ cấp luồng đã được kiểm tra giải mã 8 khung 854×480 và thoát sạch sau lượt hữu hạn 30 giây. Chưa tự làm mới URL CDN khi hết hạn; khởi động lại cầu nối nếu nguồn dừng. Chế độ này chưa thay thế tích hợp YouTube một bước trong bộ cài desktop.

Với camera triển khai thật, ưu tiên luồng RTSP/HTTP trực tiếp được chủ camera cấp: giảm được lớp phân phối YouTube/HLS. Chưa thử RTSP vật lý trong lượt này. Mục tiêu đã đo là suy luận khoảng 5 lần/giây trên một nguồn, phù hợp làm đối chứng giám sát dừng lâu; không tuyên bố đạt 30 lần suy luận/giây, không suy ra chất lượng không đổi khi giảm lấy mẫu hoặc khả năng chạy nhiều camera.

Thứ tự cải thiện tiếp theo dựa trên số đo: (1) nguồn trực tiếp và giám sát ảnh cũ/mất hình; (2) kiểm tra timer, nối ID và chặn ùn xe bằng nhãn camera thực; (3) chỉ khi GPU thành nút thắt mới thử kích thước ảnh nhỏ hơn, YOLO26n hoặc ONNX/TensorRT và chấm lại trên cùng dữ liệu. Chưa benchmark các cấu hình tăng tốc đó. Thay mô hình không sửa được nguồn HLS ngừng cấp ảnh; `limit=60` cũng không bảo đảm bắt kịp khi ngừng hơn 60 giây hoặc sai timestamp kéo dài.

Các số đo CUDA này thuộc bản nguồn chạy trên GTX 1650. Bộ cài 1.1.0 trước đó đóng gói PyTorch CPU và chưa được cập nhật bằng bản vá này; không dùng số GPU để quảng cáo tốc độ của bộ cài CPU. Cảnh báo trên camera Đà Nẵng cần đối chiếu thủ công; chưa có nhãn độc lập nên chưa tính precision/recall/F1 cho luồng live.
