# Curb

**Quan sát rõ. Xử lý có căn cứ.**

Curb là công cụ giám sát dừng đỗ cho người vận hành tại một máy Windows. Tên gợi mép lề đường; biểu trưng kết hợp chữ C và hai vạch phân làn. Không dùng huy hiệu cơ quan công quyền hoặc tuyên bố tự động kết luận vi phạm.

Biểu trưng chuẩn: `web/public/curb.svg`. Bản PNG/ICO và bitmap bộ cài được xuất bởi `scripts/brand_assets.py`. Giữ vùng trống tối thiểu bằng 1/4 bề ngang biểu trưng. Không kéo méo, thêm bóng sáng hoặc đặt trên ảnh bận.

| Vai trò | Màu |
|---|---|
| Nhận diện | Cam `#ed592e` |
| Nền | `#f3f3f0` |
| Bề mặt | `#ffffff` |
| Chữ, hành động chính | `#24261f` |
| Chữ phụ | `#696d62` |
| Chữ trên cam | Dùng nền cam đậm `#c54620` với chữ trắng để giữ tương phản |

Giao diện dùng Be Vietnam Pro cục bộ, Lucide, panel bo góc 16 px, nút có nhãn rõ. Màu trạng thái đi cùng chữ. Video/bằng chứng thật chiếm ưu tiên thị giác; không dựng số liệu hoặc bản đồ giả.

Tên sản phẩm: **Curb**. Nhà phát hành: **Meiiie**. Tên mô tả: **Giám sát dừng đỗ đường phố**. Phiên bản gốc nằm ở `curb/product.json`; Python, metadata Windows và installer đọc từ đây. `scripts/sync_version.py --check` kiểm tra metadata npm.
