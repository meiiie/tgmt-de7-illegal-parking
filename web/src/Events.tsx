import { useEffect, useState } from "react";
import {
  ArrowRight,
  Check,
  CheckCheck,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FileImage,
  Filter,
  History,
  MapPin,
  Search,
  ShieldCheck,
  Video,
  X,
} from "lucide-react";
import {
  Badge,
  api,
  Button,
  clockTime,
  Download,
  duration,
  Empty,
  ErrorBox,
  go,
  Loading,
  Modal,
  send,
  stamp,
  statusLabels,
  useNotice,
  useResource,
  vehicleLabels,
} from "./lib";
import type {
  EventList,
  EventRecord,
  ReviewStatus,
  Source,
  Vehicle,
} from "./types";

export function EventDrawer({
  id,
  onClose,
  onNext,
  scope = "",
}: {
  id: string;
  onClose: () => void;
  onNext?: (id: string) => void;
  scope?: string;
}) {
  const resource = useResource<EventRecord>(`/events/${id}`, 2000);
  const event = resource.data;
  const [media, setMedia] = useState<"snapshot" | "clip">("snapshot");
  const [status, setStatus] = useState<ReviewStatus>("pending");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const notice = useNotice();
  useEffect(() => {
    if (event) setStatus(event.status);
  }, [event?.status]);
  const save = async (next = false) => {
    setBusy(true);
    setError("");
    try {
      await send(`/events/${id}/review`, {
        status,
        note,
        version: event!.version,
      });
      setNote("");
      resource.refresh();
      notice("Đã lưu kết quả duyệt");
      if (next && onNext) {
        try {
          const query = new URLSearchParams(scope);
          query.set("status", "pending");
          query.set("page_size", "1");
          query.delete("page");
          const pending = await api<EventList>(`/events?${query}`);
          if (pending.items[0]) onNext(pending.items[0].id);
          else { onClose(); notice("Không còn cảnh báo chờ duyệt trong danh sách này"); }
        } catch {
          notice("Đã lưu. Chưa tải được cảnh báo tiếp theo; mở lại danh sách để tiếp tục.", true);
        }
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal open title="Hồ sơ cảnh báo" onClose={() => { if (!busy) onClose(); }} wide>
      {!event ? (
        resource.error ? (
          <ErrorBox message={resource.error} retry={resource.refresh} />
        ) : (
          <Loading />
        )
      ) : (
        <>
          <div className="evidence-title">
            <div>
              <h3>{event.zone_name}</h3>
              <p>
                <MapPin size={14} />
                {event.source_name}
              </p>
            </div>
            <Badge status={event.status} />
          </div>
          <div className="evidence-layout">
            <div className="evidence-main">
              <div className="segmented media-tabs">
                <button
                  className={media === "snapshot" ? "selected" : ""}
                  onClick={() => setMedia("snapshot")}
                >
                  <FileImage size={16} />
                  Ảnh
                </button>
                <button
                  className={media === "clip" ? "selected" : ""}
                  disabled={!event.payload.clip_ready}
                  onClick={() => setMedia("clip")}
                >
                  <Video size={16} />
                  {event.payload.clip_ready
                    ? "Video"
                    : "Video đang hoàn tất"}
                </button>
              </div>
              <div className="evidence-media">
                {media === "snapshot" ? (
                  <img
                    src={`/api/events/${id}/media/snapshot`}
                    alt={`Bằng chứng xe dừng tại ${event.zone_name}`}
                  />
                ) : (
                  <video
                    src={`/api/events/${id}/media/clip`}
                    controls
                    autoPlay
                    playsInline
                    preload="metadata"
                  />
                )}
              </div>
              <div className="evidence-downloads">
                <Download
                  path={`/events/${id}/media/snapshot?download=true`}
                  name={`curb-${id.slice(0, 8)}.jpg`}
                  variant="quiet"
                >
                  Tải ảnh
                </Download>
                {event.payload.clip_ready && (
                  <Download
                    path={`/events/${id}/media/clip?download=true`}
                    name={`curb-${id.slice(0, 8)}.mp4`}
                    variant="quiet"
                  >
                    Tải video
                  </Download>
                )}
                <Download
                  path={`/export/events?format=json&q=${id}`}
                  name={`curb-${id.slice(0, 8)}.json`}
                  variant="quiet"
                >
                  Hồ sơ JSON
                </Download>
              </div>
              <div className="evidence-facts">
                <div>
                  <span>Loại xe</span>
                  <strong>{vehicleLabels[event.class_name]}</strong>
                </div>
                <div>
                  <span>Thời gian dừng</span>
                  <strong>{duration(event.payload.dwell_s)}</strong>
                </div>
                <div>
                  <span>{event.job?.config.source.kind === "camera" ? "Thời điểm từ lúc bắt đầu" : "Thời điểm trong video"}</span>
                  <strong>{clockTime(event.payload.alert_time_s)}</strong>
                </div>
                <div>
                  <span>Mã theo dõi</span>
                  <strong>#{event.payload.track_id}</strong>
                </div>
              </div>
              {event.job?.config.source.metadata.attribution && (
                <p className="field-note">
                  Video mẫu · <a href={event.job.config.source.metadata.source_url} target="_blank" rel="noreferrer">{event.job.config.source.metadata.attribution}</a>.
                </p>
              )}
              <details className="technical-details">
                <summary>Thông tin truy vết</summary>
                <dl className="detail-list">
                  <div>
                    <dt>Tạo hồ sơ</dt>
                    <dd>{stamp(event.created_at)}</dd>
                  </div>
                  <div>
                    <dt>Bắt đầu dừng trong nguồn</dt>
                    <dd>{clockTime(event.payload.stop_start_s)}</dd>
                  </div>
                  <div>
                    <dt>Điểm nhận diện</dt>
                    <dd>
                      {Math.round(event.payload.confidence * 100)}%{" "}
                      <small>(không phải độ chắc chắn vi phạm)</small>
                    </dd>
                  </div>
                  <div>
                    <dt>Mô hình</dt>
                    <dd>{event.job?.config.settings.model}</dd>
                  </div>
                  <div>
                    <dt>Mã cảnh báo</dt>
                    <dd className="mono">{id}</dd>
                  </div>
                </dl>
                <Button
                  onClick={() => {
                    onClose();
                    go(`/jobs/${event.job_id}`);
                  }}
                >
                  Mở lượt phân tích <ArrowRight size={15} />
                </Button>
              </details>
            </div>
            <aside className="review-panel">
              <h3>Duyệt cảnh báo</h3>
              <div
                className="review-options"
                role="group"
                aria-label="Quyết định xử lý"
              >
                {(
                  [
                    "confirmed",
                    "dismissed",
                    "resolved",
                    "pending",
                  ] as ReviewStatus[]
                ).map((value) => (
                  <button
                    key={value}
                    className={status === value ? "selected" : ""}
                    aria-pressed={status === value}
                    disabled={busy}
                    onClick={() => setStatus(value)}
                  >
                    {value === "confirmed" ? (
                      <ShieldCheck size={17} />
                    ) : value === "dismissed" ? (
                      <X size={17} />
                    ) : value === "resolved" ? (
                      <CheckCheck size={17} />
                    ) : (
                      <Clock3 size={17} />
                    )}
                    <span>{{ confirmed: "Xác nhận", dismissed: "Bỏ qua", resolved: "Đã xử lý", pending: "Chờ duyệt" }[value]}</span>
                    {status === value && <Check size={15} />}
                  </button>
                ))}
              </div>
              <label>
                {status === "pending" ? "Ghi chú (không bắt buộc)" : "Lý do"}
                <textarea
                  rows={4}
                  value={note}
                  disabled={busy}
                  onChange={(e) => setNote(e.target.value)}
                  maxLength={2000}
                  placeholder={status === "dismissed" ? "Ví dụ: xe đang chờ đèn đỏ" : status === "confirmed" ? "Ví dụ: xe dừng quá thời gian cho phép" : "Nhập ghi chú"}
                  required={status !== "pending"}
                />
              </label>
              <ErrorBox message={error} />
              <p className="field-note">Xác nhận sau khi xem bằng chứng và đối chiếu quy định tại vị trí này.</p>
              <div className="review-actions">
                <Button variant="primary" onClick={() => save(!!onNext && status !== "pending")} busy={busy} disabled={status !== "pending" && !note.trim()}>
                  <Check size={16} />{onNext && status !== "pending" ? "Lưu và duyệt tiếp" : "Lưu kết quả"}
                </Button>
                {onNext && status !== "pending" && <Button onClick={() => save()} disabled={busy || !note.trim()}>Lưu và ở lại</Button>}
              </div>
              <div className="review-history">
                <h4>
                  <History size={16} />
                  Lịch sử xử lý
                </h4>
                {event.reviews?.length ? (
                  event.reviews.map((review) => (
                    <article key={review.id}>
                      <strong>{statusLabels[review.status]}</strong>
                      <p>{review.note || "Đưa về danh sách chờ duyệt."}</p>
                      <small>
                        {review.operator} · {stamp(review.created_at)}
                      </small>
                    </article>
                  ))
                ) : (
                  <p className="muted">
                    Chưa có lượt duyệt
                  </p>
                )}
              </div>
            </aside>
          </div>
        </>
      )}
    </Modal>
  );
}

export function EventTable({
  events,
  onOpen,
}: {
  events: EventRecord[];
  onOpen: (id: string) => void;
}) {
  return (
    <div className="table-scroll">
      <table className="event-table">
        <thead>
          <tr>
            <th>Phương tiện / vùng</th>
            <th>Nguồn giám sát</th>
            <th>Thời gian dừng</th>
            <th>Trạng thái</th>
            <th>Tạo hồ sơ</th>
            <th>
              <span className="sr-only">Thao tác</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.id}>
              <td>
                <button className="event-cell" onClick={() => onOpen(event.id)}>
                  <img
                    src={`/api/events/${event.id}/media/thumbnail`}
                    alt=""
                    loading="lazy"
                  />
                  <span>
                    <strong>
                      {vehicleLabels[event.class_name]}{" "}
                      <span className="muted">#{event.payload.track_id}</span>
                    </strong>
                    <small>{event.zone_name}</small>
                  </span>
                </button>
              </td>
              <td>{event.source_name}</td>
              <td className="tabular">
                {duration(event.payload.dwell_s)}
                <small>Tại {clockTime(event.payload.alert_time_s)}</small>
              </td>
              <td>
                <Badge status={event.status} />
              </td>
              <td className="muted nowrap">{stamp(event.created_at)}</td>
              <td>
                <button
                  className="icon-button"
                  onClick={() => onOpen(event.id)}
                  aria-label={`Xem bằng chứng ${event.zone_name} xe ${event.payload.track_id}`}
                >
                  <ArrowRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EventsPage({ onOpen, initialStatus = "" }: { onOpen: (id: string, scope?: string) => void; initialStatus?: string }) {
  const [status, setStatus] = useState(initialStatus);
  const [source, setSource] = useState("");
  const [vehicle, setVehicle] = useState("");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [page, setPage] = useState(1);
  const sources = useResource<Source[]>("/sources");
  useEffect(() => {
    const timer = window.setTimeout(() => setSearch(query), 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  useEffect(() => setPage(1), [status, source, vehicle, search, start, end]);
  const params = new URLSearchParams({
    status,
    source_id: source,
    class_name: vehicle,
    q: search,
    start,
    end,
  });
  const events = useResource<EventList>(`/events?${params}&page=${page}`, 2500);
  const clear = () => {
    setStatus("");
    setSource("");
    setVehicle("");
    setQuery("");
    setStart("");
    setEnd("");
  };
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Cảnh báo</h1>
        </div>
        <Download path={`/export/events?${params}`} name="curb-events.csv">
          Xuất CSV
        </Download>
      </div>
      <section className="panel events-panel">
        <div className="event-toolbar">
          <div className="search-field">
            <Search size={17} />
            <input
              aria-label="Tìm cảnh báo"
              placeholder="Tìm nguồn, vùng hoặc mã cảnh báo…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <select
            aria-label="Lọc trạng thái"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">Tất cả trạng thái</option>
            {(
              [
                "pending",
                "confirmed",
                "dismissed",
                "resolved",
              ] as ReviewStatus[]
            ).map((s) => (
              <option key={s} value={s}>
                {statusLabels[s]}
              </option>
            ))}
          </select>
          <select
            aria-label="Lọc nguồn"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="">Tất cả nguồn</option>
            {sources.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          <select
            aria-label="Lọc loại xe"
            value={vehicle}
            onChange={(e) => setVehicle(e.target.value)}
          >
            <option value="">Tất cả loại xe</option>
            {(Object.keys(vehicleLabels) as Vehicle[]).map((v) => (
              <option key={v} value={v}>
                {vehicleLabels[v]}
              </option>
            ))}
          </select>
        </div>
        <div className="date-toolbar">
          <Filter size={15} />
          <label>
            Từ ngày
            <input
              aria-label="Cảnh báo từ ngày"
              type="date"
              value={start}
              onChange={(e) => setStart(e.target.value)}
            />
          </label>
          <label>
            Đến ngày
            <input
              aria-label="Cảnh báo đến ngày"
              type="date"
              value={end}
              min={start}
              onChange={(e) => setEnd(e.target.value)}
            />
          </label>
          {(status || source || vehicle || query || start || end) && (
            <Button variant="quiet" onClick={clear}>
              Xóa bộ lọc
            </Button>
          )}
          <span>{events.data?.total ?? 0} cảnh báo</span>
        </div>
        <ErrorBox message={events.error} retry={events.refresh} />
        {events.loading && !events.data ? (
          <Loading />
        ) : events.data?.items.length ? (
          <EventTable events={events.data.items} onOpen={(id) => onOpen(id, params.toString())} />
        ) : (
          <Empty
            icon={<ShieldCheck size={32} />}
            title={
              status || source || vehicle || search || start || end
                ? "Không có cảnh báo khớp bộ lọc"
                : "Chưa có cảnh báo"
            }
          >
            {status || source || vehicle || search || start || end
              ? "Thay đổi hoặc xóa bộ lọc để xem cảnh báo khác."
              : "Chạy phân tích video hoặc camera để tạo cảnh báo."}
          </Empty>
        )}
        <div className="pagination">
          <span>
            Trang {page} /{" "}
            {Math.max(1, Math.ceil((events.data?.total ?? 0) / 20))}
          </span>
          <div className="actions">
            <Button disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft size={16} />
              Trước
            </Button>
            <Button
              disabled={page * 20 >= (events.data?.total ?? 0)}
              onClick={() => setPage((p) => p + 1)}
            >
              Sau
              <ChevronRight size={16} />
            </Button>
          </div>
        </div>
      </section>
      <p className="footnote">
        Bộ lọc ngày dùng thời gian tạo hồ sơ trên máy này. Thời điểm trong video
        được ghi riêng trong từng cảnh báo.
      </p>
    </>
  );
}
