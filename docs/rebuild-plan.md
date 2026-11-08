# Kế hoạch xây Curb — 08/11/2026

Baseline: `10f94e8a3c93a4b4654653b246ae9875c91250d1`. Tự thực hiện, tự review tuần tự theo adapter pstack. Không commit/push/deploy.

## Kiến trúc đã chọn

Đã so sánh hai hình dạng: Tauri/Rust điều phối Python sidecar và web cục bộ FastAPI phục vụ React. Chọn web cục bộ: model CUDA và FFmpeg đã chạy được, không thêm runtime đóng gói lớn khi ổ E còn khoảng 1,5 GB. Frontend build được phục vụ cùng origin; không cần dev server khi dùng ứng dụng.

Bản cũ Gradio gọi pipeline đơn khối rồi đọc tệp kết quả. Bản mới tách dữ liệu vận hành khỏi suy luận: `Store` sở hữu SQLite; API xác thực đầu vào, enqueue và duyệt; `JobManager` sở hữu tiến trình; worker đọc snapshot và ghi tiến độ/bằng chứng; `DwellEngine` thuần Python sở hữu vòng đời lần dừng. Chỉ worker giữ model GPU, mỗi lần một công việc. Worker không giữ request HTTP.

Đối tượng: Source → nhiều Zone; Job giữ snapshot Source/Zone/Settings; Event thuộc Job, Zone và một stop episode; ReviewHistory lưu tác giả/trạng thái/ghi chú. Job: queued → running → finalizing → completed; nhánh cancelled/failed/interrupted. Review: pending/confirmed/dismissed/resolved; mọi chuyển đổi được audit.

## Checkpoint pstack

- Blocking first steps: đọc baseline, kiểm tra môi trường, chốt hợp đồng dữ liệu và lưu hướng UI.
- Independent workstreams: backend/worker/UI có thể tách nhưng thực hiện tuần tự theo yêu cầu không dùng subagent.
- Shared mutable state: SQLite WAL, transaction ngắn; snapshot cấu hình bất biến mỗi job; một worker GPU; không ghi cùng tệp media giữa request.
- Smallest safe decomposition: domain + persistence → API + worker → giao diện → kiểm thử thực và tự review. Không thêm Redis, Kubernetes hoặc rewrite detector.

## Các đơn vị kiểm chứng

1. Zone validation và dwell lifecycle: ra khỏi vùng, quay lại, đổi ID, mất dấu, chuyển động quay về điểm cũ, chống gộp khác lần dừng.
2. API persistence: nguồn/video/vùng, queue/cancel/recovery, review/audit, báo cáo/backup, giới hạn upload/path/origin.
3. Inference thật: video mẫu, CUDA, bằng chứng H.264, progress, hủy và lỗi nguồn.
4. UI thật: nhập mẫu và upload, vẽ/sửa vùng, chạy, xem bằng chứng, lọc/xuất, lưu cấu hình; desktop/mobile.
5. Báo cáo lệnh/phiên bản/hash/kết quả/giới hạn; hướng dẫn khởi động và vận hành.

## Nguồn kỹ thuật đã đọc

- https://fastapi.tiangolo.com/tutorial/background-tasks/ — tác vụ tính toán nặng cần tách khỏi request.
- https://docs.ultralytics.com/modes/track/ — tracking persist và ByteTrack; giữ phiên bản đã thử 8.4.184.
- https://v2.tauri.app/develop/sidecar/ — đóng gói binary sidecar theo target, không tự biến môi trường CUDA thành gói desktop.
- https://vite.dev/guide/ — frontend build tĩnh, lock phiên bản cài thực tế.

## Thiết kế hình ảnh

Built-in imagegen; ảnh gốc người dùng là tham chiếu phong cách, tạo mockup Curb theo tiếng Việt, bố cục dashboard/video/hàng đợi/công việc với trắng–xám–cam–đen. Tệp `docs/design/curb-concept.png`. Prompt chính: “high-fidelity, implementation-ready desktop web application dashboard for a local video-based parking operations product named Curb; Image 1 STYLE REFERENCE only; quiet warm white panels, pale grey background, soft rounded corners, narrow icon rail, capsule navigation, near-black active controls and vivid coral-orange accent; real operations, camera view with zone, review queue, jobs table; no invented runtime claims.” Mockup không được dùng làm dữ liệu ứng dụng.
