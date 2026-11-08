import { useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Cpu,
  FileText,
  ListVideo,
  Pause,
  Play,
  RefreshCw,
  StopCircle,
} from "lucide-react";
import {
  active,
  api,
  Badge,
  Button,
  clockTime,
  Download,
  duration,
  Empty,
  ErrorBox,
  go,
  Loading,
  number,
  send,
  stamp,
  useConfirm,
  useNotice,
  useResource,
} from "./lib";
import type { EventList, Job } from "./types";
import { EventTable } from "./Events";

export function JobTable({
  jobs,
  compact = false,
}: {
  jobs: Job[];
  compact?: boolean;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Nguồn / lượt phân tích</th>
            <th>Tiến độ</th>
            <th>Cảnh báo</th>
            <th>Trạng thái</th>
            {!compact && <th>Bắt đầu</th>}
            <th>
              <span className="sr-only">Mở</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>
                <a className="table-title" href={`#/jobs/${job.id}`}>
                  {job.source_name}
                </a>
                <small>
                  {duration(job.source_seconds)}
                </small>
              </td>
              <td>
                <div className="table-progress">
                  <progress value={job.progress} max={100} />
                  <span>
                    {job.status === "running" &&
                    job.config.source.kind === "camera" &&
                    !job.config.max_seconds
                      ? "Liên tục"
                      : `${Math.round(job.progress)}%`}
                  </span>
                </div>
              </td>
              <td className="tabular">{job.event_count}</td>
              <td>
                <Badge status={job.status} />
              </td>
              {!compact && (
                <td className="muted nowrap">{stamp(job.created_at)}</td>
              )}
              <td>
                <a
                  className="icon-button"
                  href={`#/jobs/${job.id}`}
                  aria-label={`Mở lượt phân tích ${job.id.slice(0, 8)}`}
                >
                  <ArrowRight size={17} />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function JobsPage() {
  const jobs = useResource<Job[]>("/jobs?limit=200", 2000);
  const [filter, setFilter] = useState("all");
  const visible = jobs.data?.filter(
    (job) =>
      filter === "all" ||
      (filter === "active"
        ? active(job.status)
        : ["failed", "interrupted"].includes(job.status)),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Phân tích</h1>
        </div>
        <Button onClick={jobs.refresh}>
          <RefreshCw size={16} />
          Làm mới
        </Button>
      </div>
      <section className="panel">
        <div className="section-heading">
          <div className="segmented">
            <button
              className={filter === "all" ? "selected" : ""}
              onClick={() => setFilter("all")}
            >
              Gần đây
            </button>
            <button
              className={filter === "active" ? "selected" : ""}
              onClick={() => setFilter("active")}
            >
              Đang chạy và chờ
            </button>
            <button
              className={filter === "error" ? "selected" : ""}
              onClick={() => setFilter("error")}
            >
              Cần kiểm tra
            </button>
          </div>
          <span className="muted">{visible?.length ?? 0} lượt</span>
        </div>
        <ErrorBox message={jobs.error} retry={jobs.refresh} />
        {jobs.loading && !jobs.data ? (
          <Loading />
        ) : visible?.length ? (
          <JobTable jobs={visible} />
        ) : (
          <Empty
            icon={<ListVideo size={30} />}
            title="Chưa có lượt phân tích trong mục này"
            action={
              <Button onClick={() => go("/sources")}>
                Mở nguồn giám sát <ArrowRight size={15} />
              </Button>
            }
          >
            Thêm video hoặc camera và lưu vùng để bắt đầu.
          </Empty>
        )}
      </section>
    </>
  );
}

export function JobPage({
  id,
  onOpen,
}: {
  id: string;
  onOpen: (id: string, scope?: string) => void;
}) {
  const resource = useResource<Job>(`/jobs/${id}`, 1500);
  const [eventPage, setEventPage] = useState(1);
  const allEvents = useResource<EventList>(
    `/events?job_id=${id}&page=${eventPage}`,
    2000,
  );
  const [busy, setBusy] = useState(false);
  const notice = useNotice();
  const confirm = useConfirm();
  const job = resource.data;
  if (!job)
    return resource.error ? (
      <ErrorBox message={resource.error} retry={resource.refresh} />
    ) : (
      <Loading />
    );
  const isActive = active(job.status);
  const hasVideo =
    !isActive &&
    job.frames > 0 &&
    job.config.settings.save_annotated &&
    job.config.source.kind === "video" &&
    ["completed", "cancelled"].includes(job.status);
  const events = allEvents.data?.items ?? [];
  const review = async () => {
    setBusy(true);
    try {
      const pending = await api<EventList>(`/events?job_id=${id}&status=pending&page_size=1`);
      const first = pending.items[0] ?? events[0];
      if (first) onOpen(first.id, `job_id=${id}`);
      else notice("Lượt này chưa có cảnh báo");
    } catch (error) {
      notice((error as Error).message, true);
    } finally {
      setBusy(false);
    }
  };
  const cancel = async () => {
    if (
      !(await confirm(
        "Dừng lượt phân tích?",
        "Hệ thống sẽ hoàn tất bằng chứng đã ghi rồi dừng. Các cảnh báo đã tạo vẫn được giữ lại.",
        "Dừng xử lý",
      ))
    )
      return;
    setBusy(true);
    try {
      await send(`/jobs/${id}/cancel`);
      resource.refresh();
      notice("Đã gửi yêu cầu dừng.");
    } catch (e) {
      notice((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <a className="back-link" href="#/jobs">
        <ArrowLeft size={15} />
        Tất cả lượt phân tích
      </a>
      <div className="page-heading">
        <div>
          <h1>{job.source_name}</h1>
          <p>
            Lượt {job.id.slice(0, 8)} · {stamp(job.created_at)}
          </p>
        </div>
        <div className="actions">
          {isActive ? (
            <Button
              variant="danger"
              busy={busy}
              disabled={job.status === "stopping"}
              onClick={cancel}
            >
              <StopCircle size={16} />
              {job.status === "queued" ? "Hủy khỏi hàng đợi" : "Dừng xử lý"}
            </Button>
          ) : (
            <>
              <Download
                path={`/jobs/${id}/export`}
                name={`curb-evidence-${id.slice(0, 8)}.zip`}
              >
                Xuất bằng chứng
              </Download>
              <Button
                variant="primary"
                busy={busy}
                onClick={job.event_count ? review : () => go(`/sources/${job.source_id}`)}
              >
                {job.event_count ? <FileText size={16} /> : <Play size={16} />}
                {job.event_count ? "Duyệt cảnh báo" : "Phân tích lại"}
              </Button>
            </>
          )}
        </div>
      </div>
      <ErrorBox message={resource.error} retry={resource.refresh} />
      <ErrorBox message={job.error} />
      <div className="job-layout">
        <section className="panel job-view">
          <div className="section-heading">
            <Badge status={job.status} />
            <span className="muted">
              {job.config.source.kind === "camera" ? "Camera" : "Video"} · thời
              điểm {clockTime(job.source_seconds)}
            </span>
          </div>
          <div className="job-media">
            {hasVideo ? (
              <video
                controls
                preload="metadata"
                playsInline
                src={`/api/jobs/${id}/video`}
                poster={`/api/jobs/${id}/preview`}
              />
            ) : (
              <img
                src={`/api/jobs/${id}/preview?v=${job.updated_at}`}
                alt="Khung hình xử lý mới nhất"
              />
            )}
            {job.status === "queued" && (
              <div className="waiting-overlay">
                <Pause size={26} />
                <strong>Đang chờ tài nguyên xử lý</strong>
                <span>Tự bắt đầu khi lượt trước kết thúc.</span>
              </div>
            )}
          </div>
          <div className="job-progress">
            <progress max={100} value={job.progress} />
            <span>
              {job.config.source.kind === "camera" &&
              !job.config.max_seconds &&
              isActive
                ? "Giám sát liên tục"
                : `${Math.round(job.progress)}%`}
            </span>
          </div>
          <div className="job-counters">
            <div>
              <strong>{number(job.frames)}</strong>
              <span>khung hình đã xử lý</span>
            </div>
            <div>
              <strong>{number(job.fps)}</strong>
              <span>khung hình / giây xử lý</span>
            </div>
            <div>
              <strong>{job.event_count}</strong>
              <span>cảnh báo được tạo</span>
            </div>
          </div>
        </section>
        <aside className="panel job-config">
          <h2>
            <Cpu size={18} />
            Quy tắc áp dụng
          </h2>
          <dl className="detail-list">
            {job.config.zones.filter((zone) => zone.enabled).map((zone) => (
              <div key={zone.id}>
                <dt>{zone.name}</dt>
                <dd>Dừng từ {duration(zone.dwell_seconds)}</dd>
              </div>
            ))}
          </dl>
          <p className="field-note">
            Thay đổi vùng hoặc cài đặt chỉ áp dụng cho lượt phân tích mới.
          </p>
          <Button onClick={() => go(`/sources/${job.source_id}`)}>
            Sửa vùng giám sát <ArrowRight size={15} />
          </Button>
          <details className="technical-details">
          <summary>Thông số phân tích</summary>
          <dl className="detail-list">
            <div>
              <dt>Mô hình</dt>
              <dd>{job.config.settings.model}</dd>
            </div>
            <div>
              <dt>Theo dõi</dt>
              <dd>ByteTrack</dd>
            </div>
            <div>
              <dt>Lấy mẫu</dt>
              <dd>{job.config.settings.sample_fps} FPS</dd>
            </div>
            <div>
              <dt>Ngưỡng nhận diện</dt>
              <dd>{number(job.config.settings.confidence)}</dd>
            </div>
            <div>
              <dt>Thiết bị</dt>
              <dd>
                {String(job.metrics.device ?? job.config.settings.device)}
              </dd>
            </div>
            <div>
              <dt>Thời gian toàn lượt</dt>
              <dd>
                {job.metrics.wall_seconds
                  ? duration(Number(job.metrics.wall_seconds))
                  : "Đang đo"}
              </dd>
            </div>
            {!!job.metrics.peak_vram_mb && <div>
              <dt>Bộ nhớ GPU cao nhất</dt>
              <dd>
                {number(Number(job.metrics.peak_vram_mb))} MB
              </dd>
            </div>}
          </dl>
          </details>
          {job.config.source.kind === "camera" && (
            <p className="field-note">
              Camera lưu ảnh và clip cảnh báo; không ghi toàn bộ luồng để tránh
              đầy ổ đĩa.
            </p>
          )}
        </aside>
      </div>
      <section className="panel">
        <div className="section-heading">
          <h2>Cảnh báo trong lượt</h2>
          <span className="muted">{job.event_count} cảnh báo</span>
        </div>
        {events.length ? (
          <EventTable events={events} onOpen={(id) => onOpen(id, `job_id=${job.id}`)} />
        ) : (
          <Empty
            icon={<FileText size={27} />}
            title={
              isActive
                ? "Đang theo dõi các vùng"
                : "Không tạo cảnh báo trong lượt này"
            }
          >
            Xe phải được theo dõi liên tục và dừng đủ lâu trong vùng đang bật.
          </Empty>
        )}
        {(allEvents.data?.total ?? 0) > 20 && (
          <div className="pagination">
            <span>Trang {eventPage}</span>
            <div className="actions">
              <Button
                disabled={eventPage <= 1}
                onClick={() => setEventPage((p) => p - 1)}
              >
                Trước
              </Button>
              <Button
                disabled={eventPage * 20 >= (allEvents.data?.total ?? 0)}
                onClick={() => setEventPage((p) => p + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        )}
      </section>
    </>
  );
}
