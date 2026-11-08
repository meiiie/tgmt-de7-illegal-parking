import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  Cpu,
  Database,
  HardDrive,
  History,
  LockKeyhole,
  Save,
  Server,
  Trash2,
} from "lucide-react";
import {
  Button,
  bytes,
  Download,
  ErrorBox,
  Loading,
  send,
  stamp,
  useConfirm,
  useNotice,
  useResource,
} from "./lib";
import type { Health, Settings, StorageInfo } from "./types";
import { desktopAction, isDesktop } from "./desktop";

export function SettingsPage() {
  const resource = useResource<Settings>("/settings");
  const health = useResource<Health>("/health", 15000);
  const storage = useResource<StorageInfo>("/storage");
  const audit =
    useResource<
      { id: number; action: string; subject: string; created_at: string }[]
    >("/audit");
  const [form, setForm] = useState<Settings>();
  const [busy, setBusy] = useState(false);
  const [purging, setPurging] = useState(false);
  const [error, setError] = useState("");
  const notice = useNotice();
  const confirm = useConfirm();
  useEffect(() => {
    if (resource.data) setForm(resource.data);
  }, [resource.data]);
  const change = <K extends keyof Settings>(key: K, value: Settings[K]) =>
    setForm((current) => (current ? { ...current, [key]: value } : current));
  const save = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await send("/settings", form, "PUT");
      resource.refresh();
      storage.refresh();
      audit.refresh();
      notice("Đã lưu cài đặt. Áp dụng cho các lượt chạy mới.");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const purge = async () => {
    if (!storage.data?.candidates.length) return;
    if (
      !(await confirm(
        "Xóa dữ liệu đã hết hạn?",
        `Sẽ xóa ${storage.data.candidates.length} lượt xử lý, sự kiện và bằng chứng đi kèm, khoảng ${bytes(storage.data.reclaimable_bytes)}. Thao tác này không thể hoàn tác; hãy tải bản sao lưu nếu cần giữ hồ sơ.`,
        "Xóa dữ liệu hết hạn",
      ))
    )
      return;
    setPurging(true);
    try {
      await send("/storage/purge", {
        job_ids: storage.data.candidates.slice(0, 100).map((job) => job.id),
      });
      notice("Đã dọn dữ liệu hết hạn.");
      storage.refresh();
      audit.refresh();
    } catch (e) {
      notice((e as Error).message, true);
    } finally {
      setPurging(false);
    }
  };
  if (!form)
    return resource.error ? (
      <ErrorBox message={resource.error} retry={resource.refresh} />
    ) : (
      <Loading />
    );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Cài đặt trạm</h1>
          <p>Dữ liệu và suy luận nằm trên máy của bạn.</p>
        </div>
        <span className="local-chip">
          <LockKeyhole size={14} />
          Chỉ trên máy này
        </span>
      </div>
      <div className="settings-layout">
        <form onSubmit={save} className="form-stack">
          <section className="panel settings-section">
            <h2>Không gian vận hành</h2>
            <div className="field-grid">
              <label>
                Tên trạm
                <input
                  value={form.site_name}
                  onChange={(e) => change("site_name", e.target.value)}
                  required
                  maxLength={100}
                />
              </label>
              <label>
                Tên người vận hành
                <input
                  value={form.operator_name}
                  onChange={(e) => change("operator_name", e.target.value)}
                  required
                  maxLength={80}
                />
                <small>
                  Được ghi vào lịch sử duyệt; đây không phải tài khoản đăng
                  nhập.
                </small>
              </label>
            </div>
          </section>
          <section className="panel settings-section">
            <h2>Mô hình & xử lý</h2>
            <div className="field-grid">
              <label>
                Mô hình
                <select
                  value={form.model}
                  onChange={(e) => change("model", e.target.value)}
                >
                  <option value="yolo26s.pt">YOLO26s · bản cơ sở</option>
                  <option value="yolo26n.pt">YOLO26n · nhẹ hơn</option>
                </select>
              </label>
              <label>
                Thiết bị
                <select
                  value={form.device}
                  onChange={(e) => change("device", e.target.value)}
                >
                  <option value="auto">{health.data?.cuda_supported === false ? "Tự động (CPU)" : "Tự động (ưu tiên GPU)"}</option>
                  <option value="cuda" disabled={health.data?.cuda_supported === false}>NVIDIA CUDA</option>
                  <option value="cpu">CPU</option>
                </select>
              </label>
              <label>
                Lấy mẫu (khung hình/giây)
                <input
                  type="number"
                  min={1}
                  max={15}
                  step={1}
                  value={form.sample_fps}
                  onChange={(e) => change("sample_fps", Number(e.target.value))}
                  required
                />
              </label>
              <label>
                Kích thước suy luận
                <select
                  value={form.image_size}
                  onChange={(e) => change("image_size", Number(e.target.value))}
                >
                  {[480, 640, 960].map((size) => (
                    <option key={size} value={size}>
                      {size} px
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Ngưỡng detector
                <input
                  type="number"
                  min={0.1}
                  max={0.95}
                  step={0.05}
                  value={form.confidence}
                  onChange={(e) => change("confidence", Number(e.target.value))}
                  required
                />
              </label>
              <label>
                Diện tích xe nhỏ nhất (px²)
                <input
                  type="number"
                  min={0}
                  max={100000}
                  step={10}
                  value={form.minimum_area}
                  onChange={(e) =>
                    change("minimum_area", Number(e.target.value))
                  }
                  required
                />
              </label>
            </div>
            <p className="field-note">
              Ngưỡng và diện tích cần hiệu chỉnh theo góc camera. Khung hình xử
              lý được giới hạn cạnh dài 1.280 px.
            </p>
            <details>
              <summary>Quy tắc chuyển động nâng cao</summary>
              <div className="field-grid">
                <label>
                  Cửa sổ đứng yên (giây)
                  <input
                    type="number"
                    min={0.5}
                    max={10}
                    step={0.5}
                    value={form.still_window}
                    onChange={(e) =>
                      change("still_window", Number(e.target.value))
                    }
                  />
                </label>
                <label>
                  Dung sai chuyển động / chiều cao xe
                  <input
                    type="number"
                    min={0.03}
                    max={0.8}
                    step={0.01}
                    value={form.movement_tolerance}
                    onChange={(e) =>
                      change("movement_tolerance", Number(e.target.value))
                    }
                  />
                </label>
                <label>
                  Mất dấu tối đa (giây)
                  <input
                    type="number"
                    min={0.2}
                    max={5}
                    step={0.1}
                    value={form.lost_grace}
                    onChange={(e) =>
                      change("lost_grace", Number(e.target.value))
                    }
                  />
                </label>
              </div>
            </details>
          </section>
          <section className="panel settings-section">
            <h2>Bằng chứng & lưu trữ</h2>
            <div className="field-grid">
              <label>
                Video trước cảnh báo (giây)
                <input
                  type="number"
                  min={1}
                  max={15}
                  step={1}
                  value={form.evidence_before}
                  onChange={(e) =>
                    change("evidence_before", Number(e.target.value))
                  }
                />
              </label>
              <label>
                Video sau cảnh báo (giây)
                <input
                  type="number"
                  min={0}
                  max={10}
                  step={1}
                  value={form.evidence_after}
                  onChange={(e) =>
                    change("evidence_after", Number(e.target.value))
                  }
                />
              </label>
              <label>
                Thời hạn lưu trữ (ngày)
                <input
                  type="number"
                  min={1}
                  max={3650}
                  value={form.retention_days}
                  onChange={(e) =>
                    change("retention_days", Number(e.target.value))
                  }
                />
                <small>Chỉ đưa vào danh sách dọn; không tự xóa.</small>
              </label>
              <label className="toggle-field">
                <input
                  type="checkbox"
                  checked={form.save_annotated}
                  onChange={(e) => change("save_annotated", e.target.checked)}
                />
                Lưu video có lớp hiển thị cho tệp nhập
              </label>
            </div>
          </section>
          <ErrorBox message={error} />
          <div className="save-settings">
            <span className="muted">
              Lượt đang chạy giữ nguyên cấu hình lúc bắt đầu.
            </span>
            <Button type="submit" variant="primary" busy={busy}>
              <Save size={16} />
              Lưu cài đặt
            </Button>
          </div>
        </form>
        <aside className="settings-aside">
          <section className="panel system-panel">
            <h2>
              <Server size={18} />
              Tình trạng hệ thống
            </h2>
            <ErrorBox message={health.error} retry={health.refresh} />
            {health.data && (
              <>
                <div className="system-line">
                  <span className="health-dot" />
                  <strong>Dịch vụ đang hoạt động</strong>
                  <span>v{health.data.version}</span>
                </div>
                <div className="system-spec">
                  <Cpu size={18} />
                  <div>
                    <strong>{health.data?.edition}</strong>
                    <span>{health.data.gpu}</span>
                    <small>{health.data?.cuda_supported === false ? "Bộ xử lý CPU đi kèm · không dùng CUDA" : "Tên GPU, VRAM tổng / đang dùng (MB)"}</small>
                  </div>
                </div>
                <div className="system-spec">
                  <HardDrive size={18} />
                  <div>
                    <strong>{bytes(health.data.free_bytes)} còn trống</strong>
                    <span>Trên ổ dữ liệu</span>
                  </div>
                </div>
                <div className="system-spec">
                  <Database size={18} />
                  <div>
                    <strong>{health.data.database}</strong>
                    <span className="path-text">
                      {health.data.storage_path}
                    </span>
                  </div>
                </div>
                <div className="check-list">
                  <p
                    className={
                      health.data.ffmpeg ? "success-text" : "danger-text"
                    }
                  >
                    {health.data.ffmpeg ? "✓" : "×"} FFmpeg{" "}
                    {health.data.ffmpeg ? "sẵn sàng" : "chưa được cài"}
                  </p>
                  {health.data.models.map((model) => (
                    <p
                      key={model.name}
                      className={
                        model.available ? "success-text" : "danger-text"
                      }
                    >
                      {model.available ? "✓" : "×"} {model.name}
                    </p>
                  ))}
                </div>
              </>
            )}
          </section>
          <section className="panel">
            <h2>Sao lưu dữ liệu</h2>
            <p className="muted">
              Gói SQLite, video đã nhập, cấu hình và bằng chứng. Dừng các lượt
              xử lý trước khi sao lưu.
            </p>
            <Download
              path="/backup"
              name={`curb-backup-${new Date().toISOString().slice(0, 10)}.zip`}
            >
              Tải bản sao lưu
            </Download>
            <p className="field-note">
              Địa chỉ và mật khẩu camera được loại khỏi bản sao lưu. Hướng dẫn
              khôi phục vào thư mục mới nằm trong gói và README.
            </p>
            {isDesktop() && <Button onClick={() => desktopAction("restore-backup")}>Khôi phục bản sao lưu…</Button>}
          </section>
          <section className="panel">
            <h2>Dữ liệu hết hạn</h2>
            <p className="muted">
              {storage.data?.candidates.length ?? 0} lượt quá{" "}
              {storage.data?.retention_days ?? form.retention_days} ngày ·{" "}
              {bytes(storage.data?.reclaimable_bytes ?? 0)}
            </p>
            {storage.data?.candidates.slice(0, 4).map((job) => (
              <div className="retention-row" key={job.id}>
                <span>
                  {job.source_name}
                  <small>{stamp(job.created_at)}</small>
                </span>
                <span>{bytes(job.bytes)}</span>
              </div>
            ))}
            <Button
              variant="danger"
              disabled={!storage.data?.candidates.length}
              busy={purging}
              onClick={purge}
            >
              <Trash2 size={15} />
              Dọn dữ liệu hết hạn
            </Button>
            <p className="field-note">
              Nguồn và tệp video gốc đã nhập được giữ lại. Hồ sơ thuộc các lượt
              đã dọn sẽ bị xóa.
            </p>
          </section>
        </aside>
      </div>
      <section className="panel audit-panel">
        <div className="section-heading">
          <h2>
            <History size={18} />
            Nhật ký hệ thống
          </h2>
          <span className="muted">100 hoạt động gần nhất</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Thời gian</th>
                <th>Hoạt động</th>
                <th>Đối tượng</th>
              </tr>
            </thead>
            <tbody>
              {audit.data?.map((entry) => (
                <tr key={entry.id}>
                  <td>{stamp(entry.created_at)}</td>
                  <td>
                    {(
                      {
                        "source.created": "Thêm nguồn",
                        "source.updated": "Sửa nguồn",
                        "source.connection_updated": "Đổi kết nối camera",
                        "zones.updated": "Lưu vùng giám sát",
                        "settings.updated": "Đổi cài đặt",
                        "job.queued": "Tạo lượt xử lý",
                        "job.cancel_requested": "Yêu cầu dừng",
                        "source.archived": "Lưu trữ nguồn",
                        "source.restored": "Khôi phục nguồn",
                        "job.purged": "Dọn lượt hết hạn",
                      } as Record<string, string>
                    )[entry.action] ?? entry.action}
                  </td>
                  <td className="mono">{entry.subject.slice(0, 12)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

export function HelpPage() {
  const health = useResource<Health>("/health");
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Từ góc nhìn đến bằng chứng</h1>
          <p>Hướng dẫn vận hành Curb trên đường phố.</p>
        </div>
      </div>
      <div className="help-grid">
        <section className="panel help-guide">
          <h2>Một lượt giám sát</h2>
          <ol>
            <li>
              <strong>Thêm nguồn</strong>
              <p>
                Nhập video hoặc địa chỉ camera RTSP/HTTP. Với camera, kiểm tra
                kết nối để lấy khung hình đầu.
              </p>
            </li>
            <li>
              <strong>Vẽ vùng mặt đường</strong>
              <p>
                Đặt tối thiểu 3 điểm quanh đoạn đường cần quan sát. Tránh phần
                làn xe thường xếp hàng trước đèn đỏ. Có thể kéo điểm hoặc sửa
                tọa độ.
              </p>
            </li>
            <li>
              <strong>Đặt quy tắc và lưu</strong>
              <p>
                Chọn loại xe và thời gian dừng. Ngưỡng phù hợp phụ thuộc địa
                điểm; 20 giây mặc định chỉ là điểm bắt đầu để hiệu chỉnh.
              </p>
            </li>
            <li>
              <strong>Chạy và theo dõi</strong>
              <p>
                Một nguồn dùng GPU tại một thời điểm. Camera chạy liên tục sẽ
                giữ tài nguyên đến khi dừng. Nút dừng giữ lại bằng chứng đã ghi.
              </p>
            </li>
            <li>
              <strong>Duyệt từng cảnh báo</strong>
              <p>
                Xem ảnh và clip trước/sau. Phân biệt xe chờ đèn, ùn xe, che
                khuất với tình huống cần xử lý. Ghi lý do và lưu quyết định.
              </p>
            </li>
            <li>
              <strong>Xuất hồ sơ và sao lưu</strong>
              <p>
                Báo cáo xuất CSV/JSON. Mỗi lượt có gói ảnh, video, cấu hình,
                hash và số đo. Sao lưu toàn bộ trước khi dọn dữ liệu hết hạn.
              </p>
            </li>
          </ol>
        </section>
        <div className="form-stack">
          <section className="panel">
            <h2>Hiểu đúng giới hạn</h2>
            <p>
              Hệ thống phát hiện phương tiện dừng quá ngưỡng trong vùng. Hệ
              thống không tự xác định quy định giao thông tại địa điểm và không
              tự ra quyết định xử phạt.
            </p>
            <p>
              Chưa có nhận dạng biển số. Chưa đánh giá độc lập trên camera đường
              phố của bạn. Cần chạy thử nhiều tình huống ban ngày/ban đêm, mưa,
              che khuất và ùn xe trước khi đưa vào quy trình vận hành chính
              thức.
            </p>
            <p>
              Số FPS trong tác vụ là tốc độ xử lý các khung hình đã lấy mẫu,
              không phải cam kết đáp ứng nhiều camera đồng thời.
            </p>
          </section>
          <section className="panel">
            <h2>Khi có sự cố</h2>
            <dl className="help-faq">
              <dt>Không mở được camera</dt>
              <dd>
                Kiểm tra máy có truy cập camera trong cùng mạng, địa chỉ luồng
                và thông tin đăng nhập. Thử lại bằng nút kiểm tra kết nối.
              </dd>
              <dt>Cảnh báo quá nhiều</dt>
              <dd>
                Thu hẹp vùng, tránh hàng xe chờ đèn; tăng thời gian dừng và kiểm
                tra mức nhiễu chuyển động. Duyệt các trường hợp bỏ qua để ghi
                bối cảnh.
              </dd>
              <dt>Thiếu tài nguyên</dt>
              <dd>
                Chọn YOLO26n, kích thước 480 px hoặc giảm FPS lấy mẫu. Ứng dụng
                cần tối thiểu 350 MB trống để bắt đầu.
              </dd>
              <dt>Ứng dụng đóng đột ngột</dt>
              <dd>
                Lượt đang chạy được đánh dấu gián đoạn ở lần mở sau. Sự kiện đã
                lưu vẫn còn; tạo lượt mới từ nguồn để chạy lại.
              </dd>
            </dl>
          </section>
          <section className="panel">
            <h2>Dữ liệu riêng trên máy</h2>
            <p>
              Ứng dụng chỉ nghe tại 127.0.0.1. Tên người vận hành là nhãn lịch
              sử, không phải hệ thống phân quyền. Không mở cổng này ra Internet.
            </p>
            <p>
              Dữ liệu ở <code>{health.data?.storage_path ?? "đang kiểm tra…"}</code>; dùng{" "}
              <code>CURB_DATA_DIR</code> hoặc tham số launcher để chọn ổ lưu trữ
              khác.
            </p>
          </section>
        </div>
      </div>
    </>
  );
}
