import { useEffect, useState } from "react";
import {
  ArrowRight,
  Camera,
  ChartNoAxesCombined,
  CheckCheck,
  CircleHelp,
  ClipboardCheck,
  Clock3,
  HardDrive,
  Info,
  ListVideo,
  MapPin,
  Plus,
  ScanLine,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import {
  active,
  Button,
  bytes,
  duration,
  Empty,
  ErrorBox,
  go,
  Loading,
  number,
  useResource,
  vehicleLabels,
} from "./lib";
import type { Health, Job, Overview, Source } from "./types";
import { AddSource, SourcePage, SourcesPage } from "./Sources";
import { EventDrawer, EventsPage } from "./Events";
import { JobPage, JobsPage, JobTable } from "./Jobs";
import { ReportsPage } from "./Reports";
import { HelpPage, SettingsPage } from "./Settings";
import { AboutPage } from "./About";

function OverviewPage({
  onAdd,
  onOpen,
}: {
  onAdd: () => void;
  onOpen: (id: string) => void;
}) {
  const overview = useResource<Overview>("/overview", 2500);
  const sources = useResource<Source[]>("/sources", 6000);
  const jobs = useResource<Job[]>("/jobs", 2000);
  const health = useResource<Health>("/health", 20000);
  const [selected, setSelected] = useState("");
  const data = overview.data;
  const source =
    sources.data?.find((s) => s.id === selected) ?? sources.data?.[0];
  const job = jobs.data?.find((j) => j.source_id === source?.id);
  const running = job && active(job.status);
  return (
    <>
      <div className="page-heading overview-heading">
        <div>
          <h1>Tổng quan</h1>
        </div>
        <Button variant="primary" onClick={onAdd}>
          <Plus size={17} />
          Thêm nguồn
        </Button>
      </div>
      <ErrorBox message={overview.error} retry={overview.refresh} />
      {!data ? (
        <Loading />
      ) : (
        <>
          <div className="stat-grid">
            <article className="stat-card accent">
              <span>
                <ClipboardCheck size={18} />
                Chờ duyệt
                <ArrowRight size={17} className="stat-arrow" />
              </span>
              <a
                href="#/events/pending"
                className="stat-value"
                aria-label={`${data.pending} cảnh báo chờ duyệt`}
              >
                {number(data.pending)}
              </a>
            </article>
            <article className="stat-card">
              <span>
                <CheckCheck size={18} />
                Đã duyệt
              </span>
              <strong>{number(data.reviewed)}</strong>
              <small>
                {data.confirmed} xác nhận · {data.dismissed} bỏ qua ·{" "}
                {data.resolved} xử lý
              </small>
            </article>
            <article className="stat-card">
              <span>
                <Camera size={18} />
                Nguồn giám sát
              </span>
              <strong>
                {number(data.sources)}
                <em>nguồn</em>
              </strong>
              <small>
                <i
                  className={`inline-dot ${data.active_jobs ? "green" : ""}`}
                />
                {data.active_jobs} đang xử lý · {data.queued_jobs} chờ
              </small>
            </article>
            <article className="stat-card">
              <span>
                <Clock3 size={18} />
                Thời lượng đã phân tích
              </span>
              <strong>
                {number(data.processed_hours * 60)}
                <em>phút</em>
              </strong>
            </article>
          </div>
          <div className="overview-grid">
            <section className="panel monitor-panel">
              <div className="section-heading">
                <div className="monitor-title">
                  <span className={running ? "health-dot" : "idle-dot"} />
                  <h2>{running ? "Đang phân tích" : "Hình ảnh gần nhất"}</h2>
                </div>
                {sources.data?.length ? (
                  <select
                    aria-label="Chọn video hoặc camera"
                    value={source?.id ?? ""}
                    onChange={(event) => setSelected(event.target.value)}
                  >
                    {sources.data.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className="muted">Chưa có nguồn</span>
                )}
              </div>
              {source?.has_preview ? (
                <>
                  <a
                    className="monitor-image"
                    href={job ? `#/jobs/${job.id}` : `#/sources/${source.id}`}
                  >
                    <img
                      src={
                        job
                          ? `/api/jobs/${job.id}/preview?v=${job.updated_at}`
                          : `/api/sources/${source.id}/preview?v=${source.updated_at}`
                      }
                      alt={`Góc nhìn từ ${source.name}`}
                    />
                    <span className="monitor-overlay">
                      <span>
                        {source.metadata.demo
                          ? "VIDEO MẪU"
                          : source.kind === "camera"
                            ? "CAMERA"
                            : "VIDEO"}
                      </span>
                      {job && (
                        <span>
                          {job.frames} khung hình · {job.event_count} cảnh báo
                        </span>
                      )}
                    </span>
                    <span className="monitor-open">
                      <ScanLine size={18} />
                      {job ? "Xem kết quả" : "Thiết lập vùng"}
                    </span>
                  </a>
                  <div className="monitor-footer">
                    <div>
                      <strong>{source.name}</strong>
                      <span>
                        <MapPin size={13} />
                        {source.location || "Chưa ghi địa điểm"}
                      </span>
                    </div>
                    <a href={`#/sources/${source.id}`} className="button">
                      <SlidersHorizontal size={15} />
                      Sửa vùng
                    </a>
                  </div>
                </>
              ) : (
                <Empty
                  icon={<Camera size={36} />}
                  title="Thêm video hoặc camera"
                  action={
                    <Button variant="primary" onClick={onAdd}>
                      <Plus size={16} />
                      Thêm nguồn
                    </Button>
                  }
                >
                  Chọn video trên máy, kết nối camera hoặc dùng video mẫu.
                </Empty>
              )}
            </section>
            <section className="panel queue-panel">
              <div className="section-heading">
                <h2>
                  Chờ duyệt{" "}
                  <span className="count-pill">{data.pending}</span>
                </h2>
                <a
                  className="icon-button"
                  href="#/events/pending"
                  aria-label="Xem danh sách chờ duyệt"
                  title="Xem danh sách chờ duyệt"
                >
                  <ArrowRight size={18} />
                </a>
              </div>
              {data.recent_events.length ? (
                <div className="review-queue">
                  {data.recent_events.slice(0, 3).map((event) => (
                    <button
                      className="queue-event"
                      key={event.id}
                      onClick={() => onOpen(event.id)}
                    >
                      <img
                        src={`/api/events/${event.id}/media/thumbnail`}
                        alt=""
                      />
                      <div>
                        <div>
                          <strong>
                            {vehicleLabels[event.class_name]} #
                            {event.payload.track_id}
                          </strong>
                          <span className="alert-time">
                            {duration(event.payload.dwell_s)}
                          </span>
                        </div>
                        <p>{event.zone_name}</p>
                        <small>
                          <MapPin size={12} />
                          {event.source_name}
                        </small>
                        <span className="queue-action">
                          Xem bằng chứng <ArrowRight size={14} />
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <Empty
                  icon={<ShieldCheck size={31} />}
                  title="Không có cảnh báo chờ duyệt"
                >
                </Empty>
              )}
            </section>
            <section className="panel recent-panel">
              <div className="section-heading">
                <h2>Phân tích gần đây</h2>
                <a href="#/jobs" className="text-link">
                  Tất cả <ArrowRight size={15} />
                </a>
              </div>
              {jobs.data?.length ? (
                <JobTable jobs={jobs.data.slice(0, 4)} compact />
              ) : (
                <Empty
                  icon={<ListVideo size={28} />}
                  title="Chưa chạy phân tích"
                >
                  Chọn video hoặc camera để bắt đầu.
                </Empty>
              )}
            </section>
            <section className="panel station-panel">
              <div className="section-heading">
                <h2>Lưu trữ</h2>
                <a
                  href="#/settings"
                  className="icon-button"
                  aria-label="Cài đặt trạm"
                >
                  <Settings2 size={17} />
                </a>
              </div>
              <div className="storage-summary">
                <span className="storage-icon">
                  <HardDrive size={22} />
                </span>
                <div>
                  <span>Dung lượng còn trống</span>
                  <strong>
                    {health.data
                      ? bytes(health.data.free_bytes)
                      : "Đang kiểm tra"}
                  </strong>
                </div>
              </div>
              {health.data && (
                <progress
                  className="storage-bar"
                  max={health.data.total_bytes}
                  value={health.data.total_bytes - health.data.free_bytes}
                />
              )}
              <div className="station-status">
                <span>
                  <i className={overview.error ? "idle-dot" : "health-dot"} />
                  {overview.error
                    ? "Mất kết nối dịch vụ"
                    : "Dịch vụ đang hoạt động"}
                </span>
                <small>{data.active_jobs}/1 lượt phân tích</small>
              </div>
              <a href="#/reports" className="report-shortcut">
                <ChartNoAxesCombined size={18} />
                <span>Mở báo cáo vận hành</span>
                <ArrowRight size={16} />
              </a>
            </section>
          </div>
        </>
      )}
    </>
  );
}

export function App() {
  const [route, setRoute] = useState(window.location.hash.slice(1) || "/");
  const [adding, setAdding] = useState(false);
  const [eventId, setEventId] = useState<string>();
  const [reviewScope, setReviewScope] = useState("");
  const openEvent = (id: string, scope = "") => { setReviewScope(scope); setEventId(id); };
  useEffect(() => {
    const changed = () => {
      setRoute(window.location.hash.slice(1) || "/");
      window.scrollTo({ top: 0 });
    };
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  const [section = "", id] = route.split("/").filter(Boolean);
  useEffect(() => {
    document.title = `${({ sources: "Video và camera", events: "Cảnh báo", reports: "Báo cáo", jobs: "Phân tích", settings: "Cài đặt", help: "Hướng dẫn", about: "Về Curb" } as Record<string, string>)[section] ?? "Tổng quan"} · Curb`;
  }, [section]);
  const nav = [
    { path: "/", label: "Tổng quan", section: "" },
    { path: "/sources", label: "Video và camera", section: "sources" },
    { path: "/jobs", label: "Phân tích", section: "jobs" },
    { path: "/events", label: "Cảnh báo", section: "events" },
    { path: "/reports", label: "Báo cáo", section: "reports" },
  ];
  return (
    <div className="app-shell">
      <a
        className="skip-link"
        href="#main-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Bỏ qua điều hướng
      </a>
      <header className="topbar">
        <a className="brand" href="#/" aria-label="Curb — Tổng quan">
          <img className="brand-mark" src="/curb.svg" width="38" height="38" alt="" />
          <strong>Curb</strong>
        </a>
        <nav className="top-nav" aria-label="Điều hướng chính">
          {nav.map((item) => (
            <a
              href={`#${item.path}`}
              key={item.path}
              aria-current={section === item.section ? "page" : undefined}
              className={section === item.section ? "active" : ""}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="topbar-right">
          <a className="button quiet" href="#/settings"><Settings2 size={18} />Cài đặt</a>
          <a
            className="icon-button"
            href="#/help"
            title="Hướng dẫn"
            aria-label="Hướng dẫn"
          >
            <CircleHelp size={20} />
          </a>
          <a href="#/about" title="Về Curb" aria-label="Về Curb" className="icon-button"><Info size={20} /></a>
        </div>
      </header>
      <main
        id="main-content"
        tabIndex={-1}
        className="main-content"
        key={route}
      >
        {!section ? (
          <OverviewPage onAdd={() => setAdding(true)} onOpen={openEvent} />
        ) : section === "sources" ? (
          id ? (
            <SourcePage id={id} />
          ) : (
            <SourcesPage onAdd={() => setAdding(true)} />
          )
        ) : section === "events" ? (
          <EventsPage onOpen={openEvent} initialStatus={id === "pending" ? "pending" : ""} />
        ) : section === "jobs" ? (
          id ? (
            <JobPage id={id} onOpen={openEvent} />
          ) : (
            <JobsPage />
          )
        ) : section === "reports" ? (
          <ReportsPage />
        ) : section === "settings" ? (
          <SettingsPage />
        ) : section === "help" ? (
          <HelpPage />
        ) : section === "about" ? (
          <AboutPage />
        ) : (
          <section className="panel">
            <Empty
              icon={<CircleHelp size={30} />}
              title="Không tìm thấy trang"
              action={<Button onClick={() => go("/")}>Về tổng quan</Button>}
            />
          </section>
        )}
      </main>
      <AddSource open={adding} onClose={() => setAdding(false)} />
      {eventId && (
        <EventDrawer
          key={eventId}
          id={eventId}
          onNext={setEventId}
          scope={reviewScope}
          onClose={() => setEventId(undefined)}
        />
      )}
    </div>
  );
}
