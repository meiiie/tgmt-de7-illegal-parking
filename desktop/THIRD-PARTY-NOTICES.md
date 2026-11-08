# Thành phần đi kèm Curb Desktop 1.1.0

Curb: Copyright 2026 Meiiie, AGPL-3.0-only. `packages.json` liệt kê phiên bản Python và metadata giấy phép. Nội dung giấy phép của từng gói được giữ trong `runtime/Lib/site-packages/*.dist-info/`; Python và WebView2 nằm trong `licenses/`.

- CPython 3.12.10 x64: https://www.python.org/downloads/release/python-31210/
- Microsoft WebView2 SDK 1.0.4314.35: https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4314.35 — dùng Evergreen Runtime đã có hoặc bộ cài chính thức của Microsoft.
- Microsoft Visual C++ x64: runtime hệ thống v14.44 trở lên; nếu thiếu, tải trực tiếp bản 14.51.36247.0 từ Microsoft, xác minh SHA-256 trước khi cài. Không sao chép DLL từ máy phát triển vào gói. Điều khoản và tải chính thức: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist.
- PyTorch 2.11.0+cpu và torchvision 0.26.0+cpu: https://download.pytorch.org/whl/cpu — giấy phép BSD và các thành phần được ghi trong gói.
- Ultralytics 8.4.184 và YOLO26: https://github.com/ultralytics/ultralytics — AGPL-3.0, trừ khi có thỏa thuận Enterprise riêng. Trọng số giữ nguyên, không huấn luyện lại.
- FFmpeg 7.1.1 essentials build của Gyan, GPLv3, binary không sửa đổi. Phiên bản/cấu hình và danh sách thư viện trong `licenses/ffmpeg-version.txt` và `licenses/FFmpeg-build.txt`. Mã nguồn FFmpeg chính xác: https://github.com/FFmpeg/FFmpeg/commit/db69d06eeeab4f46da15030a80d539efb4503ca8; tarball tương ứng được kèm trong bộ cài và release. Thông tin bản build và các thư viện ngoài: https://www.gyan.dev/ffmpeg/builds/. FFmpeg được gọi như chương trình riêng qua subprocess.
- React, Vite, Lucide và Be Vietnam Pro: phiên bản trong `application-source.zip` và `web/package-lock.json`; giấy phép frontend được sao chép trong `licenses/frontend/`.
- Video mẫu MERL Street Scene: CC BY-SA 4.0. Created by Mitsubishi Electric Research Laboratories (MERL), 2023. Test006 được lấy mẫu từ 15 xuống 5 FPS, ghép H.264 30 giây, giữ thời gian thực. Video và ảnh phái sinh giữ CC BY-SA 4.0. Nguồn, giấy phép và trích dẫn tại `licenses/demo-video.md`.
- Fixture Gaithersburg cũ (nếu có): G. Edward Johnson, CC BY 4.0; ghi nguồn tại `licenses/legacy-demo-video.md`.

Mã nguồn ứng dụng cho bản build này nằm trong `application-source.zip`. Bản phát hành đầu tiên chưa ký mã. Xem LICENSE và trang GitHub Releases của dự án.
