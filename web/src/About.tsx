import { ArrowUpRight, Download as DownloadIcon, FolderOpen, ShieldCheck } from "lucide-react";
import { Button, Download, ErrorBox, Loading, useResource } from "./lib";
import { desktopAction, isDesktop } from "./desktop";
import type { Health } from "./types";

const repository = "https://github.com/meiiie/tgmt-de7-illegal-parking";

export function AboutPage() {
  const health = useResource<Health>("/health");
  return <>
    <div className="page-heading"><div><h1>Về Curb</h1><p>Quan sát rõ. Xử lý có căn cứ.</p></div></div>
    <div className="about-layout">
      <section className="panel about-product">
        <img src="/curb.svg" width="72" height="72" alt="Biểu trưng Curb" />
        <h2>Curb</h2>
        <p>Giám sát dừng đỗ đường phố</p>
        <ErrorBox message={health.error} retry={health.refresh} />
        {health.data ? <dl className="about-facts"><div><dt>Phiên bản</dt><dd>{health.data.version}</dd></div><div><dt>Ấn bản</dt><dd>{health.data.edition}</dd></div><div><dt>Nhà phát hành</dt><dd>Meiiie</dd></div><div><dt>Giấy phép ứng dụng</dt><dd>AGPL-3.0</dd></div></dl> : <Loading />}
        <a className="button primary" href={`${repository}/releases/latest`} target="_blank" rel="noreferrer"><DownloadIcon size={16} />Xem bản phát hành mới<ArrowUpRight size={15} /></a>
        <p className="field-note">Cập nhật bằng bộ cài mới. Dữ liệu được giữ lại. Curb không tự tải hay cài bản cập nhật trong nền.</p>
      </section>
      <div className="form-stack">
        <section className="panel about-section"><h2><ShieldCheck size={19} /> Quyền riêng tư trên máy của bạn</h2><p>Video, cấu hình và bằng chứng được lưu cục bộ. Không cần tài khoản, không gửi video lên dịch vụ AI, không có quảng cáo hay telemetry. Các liên kết hỗ trợ mở trong trình duyệt ngoài.</p><p>Curb hỗ trợ nhận biết xe dừng lâu và duyệt bằng chứng. Người vận hành kiểm tra quy định tại địa điểm và quyết định cách xử lý.</p></section>
        <section className="panel about-section"><h2>Hỗ trợ & chẩn đoán</h2><p>Gửi báo cáo chẩn đoán cùng mô tả lỗi khi cần hỗ trợ. Gói này chỉ chứa phiên bản, khả năng xử lý và trạng thái dịch vụ; không chứa video, địa chỉ camera hoặc tên người dùng.</p><div className="actions"><Download path="/diagnostics" name="curb-diagnostics.json">Tải chẩn đoán</Download>{isDesktop() && <Button onClick={() => desktopAction("open-data")}><FolderOpen size={16} />Mở thư mục dữ liệu</Button>}</div><a className="text-link" href={`${repository}/issues`} target="_blank" rel="noreferrer">Trang hỗ trợ trên GitHub <ArrowUpRight size={14} /></a></section>
        <section className="panel about-section"><h2>Mã nguồn & ghi nhận</h2><p>Curb sử dụng Ultralytics YOLO/ByteTrack, PyTorch, FFmpeg, React và Microsoft WebView2. Mẫu đường phố do MERL cung cấp theo CC BY-SA 4.0; các ảnh và clip phái sinh giữ ghi nguồn.</p><p>Bản desktop kèm mã nguồn ứng dụng, danh sách gói và giấy phép trong thư mục cài. Các thành phần bên thứ ba giữ giấy phép riêng.</p><div className="actions"><a className="text-link" href={repository} target="_blank" rel="noreferrer">Mã nguồn <ArrowUpRight size={14} /></a><a className="text-link" href={`${repository}/blob/main/desktop/THIRD-PARTY-NOTICES.md`} target="_blank" rel="noreferrer">Giấy phép thành phần <ArrowUpRight size={14} /></a></div></section>
      </div>
    </div>
  </>;
}
