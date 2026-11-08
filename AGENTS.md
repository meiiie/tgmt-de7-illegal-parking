# Quy tắc làm việc cho Đề 7

Phạm vi repo này là phát hiện xe dừng quá thời gian trong vùng do người vận hành cấu hình. Phạm vi khẩu trang của thư mục cha không áp dụng cho sản phẩm này.

- Tự thực hiện toàn bộ. Không dùng subagent, agent khác hoặc chat khác để giao việc.
- Trao đổi bằng tiếng Việt rõ, ngắn. Nêu kết quả, bằng chứng và giới hạn.
- Kế thừa nguyên tắc chung trong `../AGENTS.md`. Giữ nguyên các dự án khác và dữ liệu hiện có.
- Ưu tiên bản cơ sở chạy được. Chỉ tăng độ phức tạp khi phép đo có kiểm soát chứng minh lợi ích.
- Dùng `pstack` qua adapter tại `C:/Users/Admin/.codex/skills/pstack/SKILL.md`. Tự thực hiện các lượt khám phá và tự review tuần tự.
- Đọc [hồ sơ chuẩn bị ngày 06/11/2026](docs/preparation-2026-11-06.md) trước khi cải thiện.
- Giữ YOLO26s + ByteTrack làm đối chứng theo kết quả v5. SAM 3.1 và DINOv3 là các nhánh thử nghiệm riêng.
- Không gọi số liệu AIC21 hiện tại là chất lượng phát hiện đỗ trái phép trên camera thực tế. Bộ này đã được dùng để chọn ngưỡng.
- Giữ các JSON, CSV và notebook lịch sử nguyên trạng. Ghi kết quả mới vào thư mục mới.
- Ghi commit, hash mã và trọng số, lệnh, môi trường, dữ liệu, cách chia, seed, cấu hình và kết quả thực tế của mỗi thực nghiệm.
- Loại trùng trước khi chia dữ liệu. Chia theo camera hoặc video nguồn; không chia ngẫu nhiên các frame của cùng video.
- Chọn ngưỡng trên tập phát triển. Giữ tập kiểm tra độc lập. Báo cáo theo video, loại tình huống, lỗi và độ trễ toàn luồng.
- Phân biệt kiểm tra logic với suy luận mô hình, huấn luyện và đánh giá độc lập. Không suy ra chất lượng từ ca tổng hợp.
- Không đọc hoặc in tệp bí mật. Không đưa khóa vào mã, notebook hoặc Git.
- Tự quyết việc cục bộ, có thể hoàn tác trong phạm vi yêu cầu. Commit, push, deploy, chia sẻ công khai và chạy GPU cloud cần chỉ thị tương ứng của người dùng.
- Trước một checkpoint Git được cho phép, kiểm tra tệp ứng viên có bí mật mà không in giá trị trùng khớp.

Kiểm tra đặc tính baseline hiện tại bằng `python -X utf8 scripts/inspect_baseline.py --output outputs/baseline-probes.json`.
Lệnh này trả mã 1 khi còn yêu cầu chưa đạt. Đây là bộ tái hiện vấn đề, chưa phải bộ đánh giá mô hình.

## Ứng dụng Curb từ 08/11/2026

- Người dùng xác nhận ưu tiên giám sát dừng đỗ đường phố. Sản phẩm chính mới là `curb/` + `web/`, launcher `run-curb.ps1`; bản Gradio/pipeline cũ là đối chứng nghiên cứu.
- Đọc `PRODUCT.md`, `DESIGN.md` và `docs/rebuild-verification-2026-11-08.md` khi tiếp tục. Không dùng mockup imagegen làm bằng chứng UI đã được render/kiểm tra.
- Kiểm tra logic/API: `.venv/Scripts/python.exe -m unittest discover -s tests -v`. Frontend: `npm --prefix web run build`. Tích hợp thật: `scripts/verify_curb.py` khi dịch vụ đang chạy.
- Không dùng bộ test cũ của `src/pipeline.py` để kết luận engine Curb mới. Mỗi nhánh có phạm vi và dữ liệu kiểm chứng riêng.
- Dữ liệu Curb mặc định `outputs/curb/`, không đưa SQLite, camera URI, video hoặc bằng chứng vào Git. Chỉ một server cho mỗi thư mục dữ liệu; không khởi động server thử khác trên dữ liệu đang dùng.
- Cảnh báo vẫn cần người duyệt. Không đổi nhãn thành vi phạm chắc chắn, thêm OCR giả hoặc dựng số thống kê.
- Đọc thêm `docs/desktop-verification-2026-11-08.md`: bộ cài WinForms/WebView2 + CPython CPU được kiểm tra bằng Computer Use trên cửa sổ native. Local browser use vẫn tắt; mobile chưa kiểm tra. Không dùng bằng chứng desktop để suy ra mobile hoặc chất lượng camera hiện trường.
- Build desktop bằng `build-desktop.ps1`; khóa dependency riêng trong `desktop/requirements-lock.txt`. Dữ liệu desktop `%USERPROFILE%/Curb/data` tách khỏi thư mục cài; không đưa vào gói hoặc xóa khi gỡ phần mềm. Giữ stdin worker tách khỏi kênh quản lý vòng đời desktop, warm-up detector trước đồng hồ camera live.
- Curb 1.0.1 đổi mẫu mặc định sang 30 giây MERL Street Scene Test006, CC BY-SA 4.0; đọc `docs/demo-verification-2026-11-08.md`. Mẫu Gaithersburg và kết quả cũ giữ nguyên. `demo_id` phân biệt phiên bản; ghi nguồn nằm trong `curb/demo.json`.
- Đoạn Test006 60 giây đã phát hiện cảnh báo lặp khi xe tải che khuất xe đỗ ở giây 35–38; chưa sửa engine trong lần thay mẫu. Không dùng kết quả đẹp của mẫu 30 giây để tuyên bố đã xử lý che khuất hoặc đạt chất lượng hiện trường. Test001–Test006 đã được xem để chọn demo, không còn độc lập với quá trình phát triển này.

## Bản phát hành 1.1.0

- Đọc `docs/release-verification-1.1.0.md`. Ca che khuất Test006 60 giây được sửa bằng xác nhận chuyển động liên tục cho lần dừng đã cảnh báo; hồi quy thực tế giảm từ 6 xuống 3 cảnh báo với cùng detections. Đây là sửa lỗi trên tập phát triển, không phải đánh giá độ chính xác độc lập.
- Phiên bản gốc `curb/product.json`; chạy `scripts/sync_version.py --check`. Bộ cài Quick Install dùng `desktop/Setup.cs` gọi gói Inno ở chế độ tiến độ; không bật lại các trang wizard. Giữ AppId cho nâng cấp và giữ dữ liệu khi gỡ.
- Trước phát hành chạy `scripts/check_release.py`, kiểm tra native trên bộ cài thực tế, rồi tạo checksum bằng `scripts/release_manifest.py`. Không công bố dữ liệu người dùng, log thô hoặc thông tin camera.
