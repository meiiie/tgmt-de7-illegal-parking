import { useEffect, useRef, useState } from "react";
import type { FormEvent, PointerEvent } from "react";
import {
  Archive,
  ArrowLeft,
  ArrowRight,
  Camera,
  Check,
  CheckCheck,
  FileVideo,
  FolderOpen,
  MapPin,
  MousePointer2,
  Play,
  Plus,
  Radio,
  RefreshCw,
  Save,
  Trash2,
  Undo2,
  Upload,
  X,
} from "lucide-react";
import {
  active,
  api,
  Badge,
  Button,
  bytes,
  duration,
  Empty,
  ErrorBox,
  go,
  Loading,
  Modal,
  send,
  stamp,
  useConfirm,
  useNotice,
  useResource,
  vehicleLabels,
} from "./lib";
import type { Job, Source, Vehicle, Zone } from "./types";

export function AddSource({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [kind, setKind] = useState<"video" | "camera">("video");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [file, setFile] = useState<File>();
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [url, setUrl] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  const notice = useNotice();
  useEffect(() => {
    if (open) {
      setError("");
      setFile(undefined);
      setName("");
      setLocation("");
      setUrl("");
    }
  }, [open]);
  const finish = (source: Source) => {
    onClose();
    go(`/sources/${source.id}`);
    notice("Đã thêm nguồn");
  };
  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (kind === "video") {
        if (!file) throw new Error("Chọn một tệp video trước khi tiếp tục.");
        const body = new FormData();
        body.append("file", file);
        body.append("name", name);
        body.append("location", location);
        finish(await api<Source>("/sources/upload", { method: "POST", body }));
      } else
        finish(await send<Source>("/sources/camera", { name, location, url }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const demo = async () => {
    setBusy(true);
    setError("");
    try {
      finish(await send<Source>("/demo"));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal
      title="Thêm nguồn giám sát"
      open={open}
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <div className="segmented" role="group" aria-label="Loại nguồn">
        <button
          className={kind === "video" ? "selected" : ""}
          onClick={() => setKind("video")}
          disabled={busy}
        >
          <FileVideo size={17} />
          Tệp video
        </button>
        <button
          className={kind === "camera" ? "selected" : ""}
          onClick={() => setKind("camera")}
          disabled={busy}
        >
          <Camera size={17} />
          Camera IP
        </button>
      </div>
      <form onSubmit={submit} className="form-stack">
        {kind === "video" ? (
          <>
            <input
              ref={fileInput}
              className="sr-only"
              type="file"
              accept="video/*,.mkv,.avi"
              aria-label="Chọn tệp video"
              onChange={(e) => {
                const chosen = e.target.files?.[0];
                setFile(chosen);
                if (!name && chosen)
                  setName(chosen.name.replace(/\.[^.]+$/, "").slice(0, 100));
              }}
            />
            <button
              type="button"
              className="upload-area"
              onClick={() => fileInput.current?.click()}
              disabled={busy}
            >
              <Upload size={27} />
              <strong>{file?.name ?? "Chọn video từ máy tính"}</strong>
              <span>
                {file
                  ? bytes(file.size)
                  : "MP4, MOV, MKV, AVI, WebM · tối đa 1 GB"}
              </span>
            </button>
          </>
        ) : (
          <label>
            Địa chỉ camera
            <input
              type="password"
              autoComplete="off"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="rtsp://địa-chỉ-camera:554/stream"
              required
              maxLength={2048}
            />
            <small>
              Hỗ trợ RTSP và HTTP(S). Địa chỉ được giữ kín trên giao diện và
              loại khỏi bản sao lưu.
            </small>
          </label>
        )}
        <label>
          Tên nguồn
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Ví dụ: Nguyễn Trãi · hướng về trung tâm"
            required
            maxLength={100}
          />
        </label>
        <label>
          Địa điểm
          <input
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Tên đường, nút giao hoặc vị trí camera"
            maxLength={160}
          />
        </label>
        <ErrorBox message={error} />
        {busy && (
          <p className="muted" role="status">
            Đang nhập và kiểm tra nguồn. Video lớn có thể cần thêm thời gian…
          </p>
        )}
        <Button type="submit" variant="primary" busy={busy}>
          <Plus size={17} />
          Thêm nguồn
        </Button>
      </form>
      <div className="demo-invite">

        <Button variant="quiet" onClick={demo} busy={busy}>
          Dùng video mẫu <ArrowRight size={15} />
        </Button>
        <small>Camera đường phố cố định · MERL Street Scene · CC BY-SA 4.0</small>
      </div>
    </Modal>
  );
}

export function SourcesPage({ onAdd }: { onAdd: () => void }) {
  const [archived, setArchived] = useState(false);
  const [query, setQuery] = useState("");
  const sources = useResource<Source[]>(`/sources?archived=${archived}`);
  const jobs = useResource<Job[]>("/jobs", 2500);
  const visible = sources.data?.filter((source) =>
    `${source.name} ${source.location}`
      .toLocaleLowerCase("vi")
      .includes(query.toLocaleLowerCase("vi")),
  );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Video và camera</h1>
        </div>
        <Button variant="primary" onClick={onAdd}>
          <Plus size={17} />
          Thêm nguồn
        </Button>
      </div>
      <div className="toolbar">
        <input
          className="search-input"
          aria-label="Tìm nguồn"
          placeholder="Tìm tên nguồn hoặc địa điểm…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="segmented">
          <button
            className={!archived ? "selected" : ""}
            onClick={() => setArchived(false)}
          >
            Đang sử dụng
          </button>
          <button
            className={archived ? "selected" : ""}
            onClick={() => setArchived(true)}
          >
            Đã lưu trữ
          </button>
        </div>
      </div>
      <ErrorBox message={sources.error} retry={sources.refresh} />
      {sources.loading && !sources.data ? (
        <Loading />
      ) : !visible?.length ? (
        <section className="panel">
          <Empty
            icon={<Camera size={31} />}
            title={
              query
                ? "Không tìm thấy nguồn phù hợp"
                : archived
                  ? "Chưa có nguồn lưu trữ"
                  : "Chưa có video hoặc camera"
            }
            action={
              !archived && !query ? (
                <Button variant="primary" onClick={onAdd}>
                  Thêm video hoặc camera
                </Button>
              ) : undefined
            }
          >
            {query
              ? "Thử tên khác hoặc xóa từ khóa."
              : !archived
                ? "Chọn video từ máy tính, kết nối camera hoặc dùng video mẫu."
                : undefined}
          </Empty>
        </section>
      ) : (
        <div className="source-grid">
          {visible.map((source) => {
            const job = jobs.data?.find(
              (j) => j.source_id === source.id && active(j.status),
            );
            return (
              <a
                className="source-card"
                key={source.id}
                href={`#/sources/${source.id}`}
              >
                <div className="source-image">
                  {source.has_preview ? (
                    <img
                      src={`/api/sources/${source.id}/preview?v=${source.updated_at}`}
                      alt={`Khung hình từ ${source.name}`}
                      loading="lazy"
                    />
                  ) : (
                    <div className="camera-placeholder">
                      <Camera size={35} />
                      <span>Chưa kiểm tra kết nối</span>
                    </div>
                  )}
                  <span className="source-kind">
                    {source.kind === "camera" ? (
                      <Radio size={13} />
                    ) : (
                      <FileVideo size={13} />
                    )}
                    {source.kind === "camera" ? "Camera IP" : "Video"}
                    {source.metadata.demo && " · mẫu"}
                  </span>
                  {job && (
                    <div className="source-running">
                      <Badge status={job.status} />
                    </div>
                  )}
                </div>
                <div className="source-info">
                  <h3>{source.name}</h3>
                  <p>
                    <MapPin size={14} />
                    {source.location || "Chưa ghi địa điểm"}
                  </p>
                  <div className="source-footer">
                    <span>
                      {source.zones.filter((z) => z.enabled).length} vùng đang
                      bật
                    </span>
                    <span>
                      {source.kind === "video"
                        ? duration(source.metadata.duration ?? 0)
                        : "RTSP / HTTP"}
                      <ArrowRight size={16} />
                    </span>
                  </div>
                </div>
              </a>
            );
          })}
        </div>
      )}
    </>
  );
}

function ZoneEditor({
  source,
  saved,
  onDirty,
}: {
  source: Source;
  saved: () => void;
  onDirty: (dirty: boolean) => void;
}) {
  const [zones, setZones] = useState<Zone[]>(structuredClone(source.zones));
  const [selected, setSelected] = useState(source.zones[0]?.id ?? "");
  const [drawing, setDrawing] = useState(false);
  const [points, setPoints] = useState<number[][]>([]);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<number | null>(null);
  const notice = useNotice();
  const confirm = useConfirm();
  const zone = zones.find((z) => z.id === selected);
  useEffect(() => onDirty(dirty || drawing), [dirty, drawing, onDirty]);
  useEffect(() => {
    const handler = (event: BeforeUnloadEvent) => {
      if (dirty || drawing) {
        event.preventDefault();
        event.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [dirty, drawing]);
  useEffect(() => {
    if (!dirty && !drawing) return;
    let waiting = false;
    const navigate = (event: Event) => {
      event.preventDefault();
      if (waiting) return;
      waiting = true;
      void confirm(
        "Rời cấu hình chưa lưu?",
        "Các vùng đang sửa chưa được lưu. Bạn có thể quay lại lưu trước khi chuyển trang.",
        "Bỏ thay đổi và chuyển trang",
      ).then((accepted) => {
        waiting = false;
        if (accepted)
          window.location.hash = (event as CustomEvent<string>).detail;
      });
    };
    const link = (event: MouseEvent) => {
      if (
        event.button !== 0 ||
        event.ctrlKey ||
        event.metaKey ||
        event.shiftKey
      )
        return;
      const anchor = (event.target as Element).closest('a[href^="#/"]');
      const href = anchor?.getAttribute("href");
      if (href && href !== window.location.hash) {
        event.preventDefault();
        go(href.slice(1));
      }
    };
    window.addEventListener("curb:navigate", navigate);
    document.addEventListener("click", link, true);
    return () => {
      window.removeEventListener("curb:navigate", navigate);
      document.removeEventListener("click", link, true);
    };
  }, [dirty, drawing, confirm]);
  const patch = (change: Partial<Zone>) => {
    setZones((current) =>
      current.map((z) => (z.id === selected ? { ...z, ...change } : z)),
    );
    setDirty(true);
    setError("");
  };
  const coordinate = (event: { clientX: number; clientY: number }) => {
    const box = svg.current!.getBoundingClientRect();
    return [
      Math.max(0, Math.min(1, (event.clientX - box.left) / box.width)),
      Math.max(0, Math.min(1, (event.clientY - box.top) / box.height)),
    ];
  };
  const finish = () => {
    if (points.length < 3) return;
    const id = crypto.randomUUID();
    setZones((current) => [
      ...current,
      {
        id,
        name: `Vùng ${current.length + 1}`,
        polygon: points,
        dwell_seconds: 20,
        enabled: true,
        severity: "restricted",
        classes: ["car", "motorcycle", "bus", "truck"],
        suppress_congestion: true,
      },
    ]);
    setSelected(id);
    setPoints([]);
    setDrawing(false);
    setDirty(true);
  };
  const move = (event: PointerEvent<SVGSVGElement>) => {
    if (drag.current !== null && zone) {
      const next = zone.polygon.map((p, i) =>
        i === drag.current ? coordinate(event) : p,
      );
      patch({ polygon: next });
    }
  };
  const save = async () => {
    setBusy(true);
    setError("");
    try {
      await send(`/sources/${source.id}/zones`, { zones }, "PUT");
      setDirty(false);
      onDirty(false);
      notice("Đã lưu vùng");
      saved();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="panel zone-editor">
      <div className="section-heading">
        <div>
          <h2>Vùng giám sát</h2>
        </div>
        <Button
          variant="primary"
          onClick={save}
          busy={busy}
          disabled={!dirty || drawing}
        >
          <Save size={16} />
          Lưu vùng
        </Button>
      </div>
      <div className="zone-tools">
        {drawing ? (
          <>
            <span>
              <MousePointer2 size={16} />
              {points.length} điểm · chọn ít nhất 3 điểm quanh vùng cần theo dõi
            </span>
            <Button
              onClick={() => setPoints((current) => current.slice(0, -1))}
              disabled={!points.length}
            >
              <Undo2 size={15} />
              Hoàn tác
            </Button>
            <Button onClick={finish} disabled={points.length < 3}>
              <CheckCheck size={15} />
              Đóng vùng
            </Button>
            <Button
              variant="quiet"
              onClick={() => {
                setDrawing(false);
                setPoints([]);
              }}
            >
              <X size={15} />
              Hủy vẽ
            </Button>
          </>
        ) : (
          <>
            <Button
              onClick={() => {
                setDrawing(true);
                setPoints([]);
              }}
              disabled={zones.length >= 24}
            >
              <Plus size={16} />
              Vẽ vùng mới
            </Button>
            <span className="muted">
              Kéo các điểm để sửa vùng.
            </span>
          </>
        )}
      </div>
      <div
        className={`zone-canvas ${drawing ? "drawing" : ""}`}
        style={{
          aspectRatio: `${source.metadata.width ?? 16} / ${source.metadata.height ?? 9}`,
          maxWidth: `${((source.metadata.width ?? 16) / (source.metadata.height ?? 9)) * 60}dvh`,
        }}
      >
        <img
          src={`/api/sources/${source.id}/preview?v=${source.updated_at}`}
          alt="Khung hình để vẽ vùng giám sát"
          draggable={false}
        />
        <svg
          ref={svg}
          viewBox="0 0 1000 1000"
          preserveAspectRatio="none"
          aria-label="Bản đồ vùng giám sát trên video"
          onClick={(event) => {
            if (drawing && points.length < 32)
              setPoints((current) => [...current, coordinate(event)]);
          }}
          onPointerMove={move}
          onPointerUp={() => {
            drag.current = null;
          }}
          onPointerCancel={() => {
            drag.current = null;
          }}
        >
          {zones.map((z) => (
            <g key={z.id}>
              <polygon
                points={z.polygon
                  .map((p) => `${p[0] * 1000},${p[1] * 1000}`)
                  .join(" ")}
                className={`zone-polygon ${z.id === selected ? "chosen" : ""} ${!z.enabled ? "disabled-zone" : ""}`}
                onClick={(event) => {
                  if (!drawing) {
                    event.stopPropagation();
                    setSelected(z.id);
                  }
                }}
              />
              <text
                x={z.polygon[0][0] * 1000 + 8}
                y={Math.max(28, z.polygon[0][1] * 1000 - 12)}
                className="zone-label"
              >
                {z.name}
              </text>
            </g>
          ))}
          {drawing && (
            <polyline
              points={points
                .map((p) => `${p[0] * 1000},${p[1] * 1000}`)
                .join(" ")}
              className="drawing-line"
            />
          )}
          {(drawing ? points : (zone?.polygon ?? [])).map((point, i) => (
            <ellipse
              key={i}
              cx={point[0] * 1000}
              cy={point[1] * 1000}
              rx="6"
              ry="10"
              className="zone-handle"
              tabIndex={drawing ? -1 : 0}
              role="button"
              aria-label={`Điểm ${i + 1}; dùng phím mũi tên để di chuyển`}
              onClick={(event) => {
                event.stopPropagation();
                if (drawing && i === 0) finish();
              }}
              onPointerDown={(event) => {
                if (!drawing) {
                  event.preventDefault();
                  drag.current = i;
                  event.currentTarget.setPointerCapture(event.pointerId);
                }
              }}
              onKeyDown={(event) => {
                if (
                  zone &&
                  ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(
                    event.key,
                  )
                ) {
                  event.preventDefault();
                  const next = zone.polygon.map((p) => [...p]);
                  const axis = ["ArrowLeft", "ArrowRight"].includes(event.key)
                    ? 0
                    : 1;
                  next[i][axis] = Math.min(
                    1,
                    Math.max(
                      0,
                      next[i][axis] +
                        (["ArrowLeft", "ArrowUp"].includes(event.key)
                          ? -0.005
                          : 0.005),
                    ),
                  );
                  patch({ polygon: next });
                }
              }}
            />
          ))}
        </svg>
        {drawing && (
          <span className="canvas-hint">
            Bấm quanh vùng cần theo dõi · tối thiểu 3 điểm
          </span>
        )}
      </div>
      <ErrorBox message={error} />
      {drawing && (
        <Button
          variant="quiet"
          onClick={() => setPoints((current) => [...current, [0.5, 0.5]])}
          disabled={points.length >= 32}
        >
          Thêm điểm bằng bàn phím
        </Button>
      )}
      <div className="zone-config">
        <div className="zone-list" aria-label="Danh sách vùng">
          {zones.length ? (
            zones.map((z) => (
              <button
                key={z.id}
                className={z.id === selected ? "selected" : ""}
                onClick={() => setSelected(z.id)}
              >
                <span className={`zone-swatch ${!z.enabled ? "off" : ""}`} />
                <span>
                  {z.name}
                  <small>
                    {duration(z.dwell_seconds)} ·{" "}
                    {z.enabled ? "Đang bật" : "Đang tắt"}
                  </small>
                </span>
                <ArrowRight size={15} />
              </button>
            ))
          ) : (
            <p className="muted">
              Chưa có vùng. Chọn “Vẽ vùng mới” để bắt đầu.
            </p>
          )}
        </div>
        {zone && (
          <div className="zone-fields">
            <div className="field-grid">
              <label>
                Tên vùng
                <input
                  value={zone.name}
                  maxLength={80}
                  onChange={(e) => patch({ name: e.target.value })}
                />
              </label>
              <label>
                Cảnh báo sau (giây)
                <input
                  type="number"
                  min={2}
                  max={86400}
                  value={zone.dwell_seconds}
                  onChange={(e) =>
                    patch({ dwell_seconds: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Mức theo dõi
                <select
                  value={zone.severity}
                  onChange={(e) =>
                    patch({ severity: e.target.value as Zone["severity"] })
                  }
                >
                  <option value="restricted">Vùng hạn chế dừng đỗ</option>
                  <option value="watch">Theo dõi tình huống</option>
                </select>
              </label>
              <label className="toggle-field">
                <input
                  type="checkbox"
                  checked={zone.enabled}
                  onChange={(e) => patch({ enabled: e.target.checked })}
                />
                Bật vùng này
              </label>
            </div>
            <fieldset>
              <legend>Loại phương tiện</legend>
              <div className="checkbox-row">
                {(Object.keys(vehicleLabels) as Vehicle[]).map((label) => (
                  <label key={label}>
                    <input
                      type="checkbox"
                      checked={zone.classes.includes(label)}
                      onChange={(e) =>
                        patch({
                          classes: e.target.checked
                            ? [...zone.classes, label]
                            : zone.classes.filter((c) => c !== label),
                        })
                      }
                    />
                    {vehicleLabels[label]}
                  </label>
                ))}
              </div>
            </fieldset>
            <label className="toggle-field">
              <input
                type="checkbox"
                checked={zone.suppress_congestion}
                onChange={(e) =>
                  patch({ suppress_congestion: e.target.checked })
                }
              />
              Bỏ qua tình huống ùn xe
            </label>
            <p className="field-note">
              Tạm ngừng cảnh báo khi có ít nhất 4 xe trong vùng và 60% đứng yên.
            </p>
            <div className="schedule-fields">
              <label className="toggle-field">
                <input
                  type="checkbox"
                  checked={zone.schedule_enabled ?? false}
                  onChange={(e) =>
                    patch({ schedule_enabled: e.target.checked })
                  }
                />
                Chỉ giám sát trong khung giờ quy định
              </label>
              {zone.schedule_enabled && (
                <>
                  <div className="field-grid">
                    <label>
                      Bắt đầu
                      <input
                        type="time"
                        value={zone.start_time ?? "00:00"}
                        onChange={(e) => patch({ start_time: e.target.value })}
                      />
                    </label>
                    <label>
                      Kết thúc
                      <input
                        type="time"
                        value={zone.end_time ?? "00:00"}
                        onChange={(e) => patch({ end_time: e.target.value })}
                      />
                    </label>
                  </div>
                  <div className="checkbox-row">
                    {["T2", "T3", "T4", "T5", "T6", "T7", "CN"].map(
                      (day, index) => (
                        <label key={day}>
                          <input
                            type="checkbox"
                            checked={(
                              zone.weekdays ?? [0, 1, 2, 3, 4, 5, 6]
                            ).includes(index)}
                            onChange={(e) =>
                              patch({
                                weekdays: e.target.checked
                                  ? [
                                      ...(zone.weekdays ?? [
                                        0, 1, 2, 3, 4, 5, 6,
                                      ]),
                                      index,
                                    ]
                                  : (
                                      zone.weekdays ?? [0, 1, 2, 3, 4, 5, 6]
                                    ).filter((d) => d !== index),
                              })
                            }
                          />
                          {day}
                        </label>
                      ),
                    )}
                  </div>
                  <p className="field-note">
                    Hai giờ bằng nhau nghĩa là cả ngày. Khung qua nửa đêm thuộc
                    ngày bắt đầu. Camera dùng giờ máy; video cần mốc bắt đầu ghi
                    hình trong thông tin nguồn.
                  </p>
                </>
              )}
            </div>
            <details>
              <summary>Tọa độ điểm (% khung hình)</summary>
              <div className="point-grid">
                {zone.polygon.map((point, i) => (
                  <div key={i}>
                    <span>{i + 1}</span>
                    {point.map((value, axis) => (
                      <input
                        key={axis}
                        aria-label={`${axis === 0 ? "X" : "Y"} điểm ${i + 1}`}
                        type="number"
                        min={0}
                        max={100}
                        step={0.1}
                        value={Math.round(value * 1000) / 10}
                        onChange={(e) =>
                          patch({
                            polygon: zone.polygon.map((p, j) =>
                              j === i
                                ? p.map((v, a) =>
                                    a === axis
                                      ? Number(e.target.value) / 100
                                      : v,
                                  )
                                : p,
                            ),
                          })
                        }
                      />
                    ))}
                  </div>
                ))}
              </div>
            </details>
            <Button
              variant="danger"
              onClick={async () => {
                if (
                  await confirm(
                    "Xóa vùng giám sát?",
                    `Vùng “${zone.name}” sẽ được bỏ khỏi cấu hình đang sửa. Các lượt chạy và bằng chứng trước đây vẫn được giữ.`,
                    "Xóa vùng",
                  )
                ) {
                  setZones((current) =>
                    current.filter((z) => z.id !== selected),
                  );
                  setSelected(zones.find((z) => z.id !== selected)?.id ?? "");
                  setDirty(true);
                }
              }}
            >
              <Trash2 size={15} />
              Xóa vùng
            </Button>
          </div>
        )}
      </div>
      {dirty && (
        <div className="inline-note">
          Có thay đổi chưa lưu. Lưu vùng trước khi chạy phân tích.
        </div>
      )}
    </section>
  );
}

export function SourcePage({ id }: { id: string }) {
  const resource = useResource<Source>(`/sources/${id}`);
  const jobs = useResource<Job[]>(`/jobs?source_id=${id}`, 2000);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState("");
  const [edit, setEdit] = useState(false);
  const [connection, setConnection] = useState(false);
  const [limit, setLimit] = useState(0);
  const notice = useNotice();
  const confirm = useConfirm();
  const source = resource.data;
  const runAction = async (key: string, fn: () => Promise<void>) => {
    setBusy(key);
    try {
      await fn();
    } catch (e) {
      notice((e as Error).message, true);
    } finally {
      setBusy("");
    }
  };
  if (!source)
    return resource.error ? (
      <ErrorBox message={resource.error} retry={resource.refresh} />
    ) : (
      <Loading />
    );
  const current = jobs.data?.find((job) => active(job.status));
  const startHint = source.archived
    ? "Khôi phục nguồn để tiếp tục phân tích."
    : dirty
      ? "Lưu vùng đã chỉnh sửa trước khi chạy phân tích."
      : !source.has_preview
        ? "Kiểm tra kết nối camera để lấy khung hình và chọn vùng giám sát."
        : !source.zones.some((zone) => zone.enabled)
          ? "Vẽ và bật ít nhất một vùng giám sát để chạy phân tích."
          : "";
  const start = () =>
    runAction("run", async () => {
      const job = await send<Job>("/jobs", {
        source_id: id,
        max_seconds: limit,
      });
      notice("Đã thêm vào hàng đợi phân tích");
      go(`/jobs/${job.id}`);
    });
  return (
    <>
      <a href="#/sources" className="back-link">
        <ArrowLeft size={15} />
        Tất cả nguồn
      </a>
      <div className="page-heading">
        <div>
          <h1>{source.name}</h1>
          <p>
            <MapPin size={15} />
            {source.location || "Chưa ghi địa điểm"}
            <span className="dot-separator">·</span>
            {source.kind === "camera"
              ? "Camera IP"
              : duration(source.metadata.duration ?? 0)}
            {source.archived && " · Đã lưu trữ"}
          </p>
        </div>
        <div className="actions">
          <Button onClick={() => setEdit(true)}>Sửa thông tin</Button>
          {current ? (
            <Button variant="primary" onClick={() => go(`/jobs/${current.id}`)}>
              <Radio size={17} />
              Xem tiến trình
            </Button>
          ) : (
            <Button
              variant="primary"
              busy={busy === "run"}
              disabled={!!startHint}
              onClick={start}
            >
              <Play size={17} />
              Chạy phân tích
            </Button>
          )}
        </div>
      </div>
      {!current && startHint && <p className="state-hint" role="status">{startHint}</p>}
      <ErrorBox message={resource.error} retry={resource.refresh} />
      {source.metadata.demo && (
        <details className="demo-details">
          <summary>Video mẫu · Nguồn và giấy phép</summary>
          <div>
            <strong>{source.metadata.demo_title || "Video mẫu có xe chờ đèn đỏ"}</strong>
            <span>
              {source.metadata.demo_description || "Vùng và ngưỡng 5 giây dùng để kiểm tra luồng cảnh báo. Đây không phải bằng chứng xe vi phạm."}{" "}
              <a
                href={source.metadata.source_url}
                target="_blank"
                rel="noreferrer"
              >
                {source.metadata.attribution || "G. Edward Johnson · Wikimedia Commons · CC BY 4.0"}
              </a>
              {source.metadata.license_url && <> · <a href={source.metadata.license_url} target="_blank" rel="noreferrer">Giấy phép</a></>}
              {source.metadata.modifications && <> · {source.metadata.modifications}</>}
            </span>
          </div>
        </details>
      )}
      {source.has_preview ? (
        <ZoneEditor
          key={`${source.id}-${source.updated_at}`}
          source={source}
          saved={resource.refresh}
          onDirty={setDirty}
        />
      ) : (
        <section className="panel">
          <Empty
            icon={<Camera size={35} />}
            title="Lấy khung hình đầu tiên"
            action={
              <Button
                busy={busy === "probe"}
                variant="primary"
                onClick={() =>
                  runAction("probe", async () => {
                    await send(`/sources/${id}/probe`);
                    resource.refresh();
                    notice("Đã kết nối và lấy khung hình camera.");
                  })
                }
              >
                <RefreshCw size={17} />
                Kiểm tra kết nối
              </Button>
            }
          >
            Kiểm tra camera để vẽ vùng trên đúng góc nhìn.
          </Empty>
        </section>
      )}
      <div className="two-columns source-bottom">
        <section className="panel">
          <div className="section-heading">
            <h2>Tùy chọn phân tích</h2>
          </div>
          <label>
            Phân tích tối đa (giây)
            <input
              type="number"
              min={0}
              max={86400}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
            />
            <small>
              Nhập 0 để phân tích hết video hoặc chạy camera đến khi dừng.
            </small>
          </label>
          <div className="detail-list">
            <div>
              <span>Độ phân giải</span>
              <strong>
                {source.metadata.width
                  ? `${source.metadata.width} × ${source.metadata.height}`
                  : "Chưa kiểm tra"}
              </strong>
            </div>
            <div>
              <span>Vùng giám sát</span>
              <strong>
                {source.zones.filter((z) => z.enabled).length} đang bật
              </strong>
            </div>
            <div>
              <span>Thêm lúc</span>
              <strong>{stamp(source.created_at)}</strong>
            </div>
          </div>
          <div className="actions wrap">
            {source.kind === "camera" && (
              <>
                <Button onClick={() => setConnection(true)}>Đổi kết nối</Button>
                <Button
                  busy={busy === "probe"}
                  disabled={dirty}
                  onClick={() =>
                    runAction("probe", async () => {
                      await send(`/sources/${id}/probe`);
                      resource.refresh();
                    })
                  }
                >
                  <RefreshCw size={15} />
                  Lấy lại khung hình
                </Button>
              </>
            )}
            <Button
              variant="quiet"
              disabled={!!current || dirty}
              onClick={() =>
                runAction("archive", async () => {
                  if (
                    await confirm(
                      source.archived ? "Khôi phục nguồn?" : "Lưu trữ nguồn?",
                      "Các lượt phân tích và bằng chứng đã có vẫn được giữ lại.",
                      source.archived ? "Khôi phục" : "Lưu trữ",
                    )
                  ) {
                    await send(
                      `/sources/${id}/archive?archived=${!source.archived}`,
                    );
                    resource.refresh();
                  }
                })
              }
            >
              <Archive size={15} />
              {source.archived ? "Khôi phục nguồn" : "Lưu trữ nguồn"}
            </Button>
          </div>
        </section>
        <section className="panel">
          <div className="section-heading">
            <h2>Lượt phân tích của nguồn</h2>
            <a href="#/jobs" className="text-link">
              Tất cả <ArrowRight size={15} />
            </a>
          </div>
          {jobs.data?.length ? (
            <div className="compact-jobs">
              {jobs.data.slice(0, 5).map((job) => (
                <a href={`#/jobs/${job.id}`} key={job.id}>
                  <div>
                    <strong>{stamp(job.created_at)}</strong>
                    <small>
                      {job.frames} khung hình · {job.event_count} cảnh báo
                    </small>
                  </div>
                  <Badge status={job.status} />
                  <ArrowRight size={15} />
                </a>
              ))}
            </div>
          ) : (
            <Empty icon={<FolderOpen size={25} />} title="Chưa có lượt phân tích">
              Lưu vùng rồi chọn “Chạy phân tích”.
            </Empty>
          )}
        </section>
      </div>
      <Modal
        title={connection ? "Cập nhật kết nối camera" : "Thông tin nguồn"}
        open={edit || connection}
        onClose={() => {
          setEdit(false);
          setConnection(false);
        }}
      >
        <form
          className="form-stack"
          onSubmit={(event) => {
            event.preventDefault();
            const form = new FormData(event.currentTarget);
            void runAction("edit", async () => {
              const body = {
                name: form.get("name"),
                location: form.get("location"),
                notes: form.get("notes"),
                recorded_at: form.get("recorded_at") || null,
                ...(connection ? { url: form.get("url") } : {}),
              };
              await send(
                `/sources/${id}${connection ? "/connection" : ""}`,
                body,
                "PUT",
              );
              setEdit(false);
              setConnection(false);
              resource.refresh();
              notice("Đã cập nhật nguồn.");
            });
          }}
        >
          <label>
            Tên nguồn
            <input
              name="name"
              defaultValue={source.name}
              required
              maxLength={100}
            />
          </label>
          <label>
            Địa điểm
            <input
              name="location"
              defaultValue={source.location}
              maxLength={160}
            />
          </label>
          {source.kind === "video" && (
            <label>
              Mốc bắt đầu ghi hình (giờ máy)
              <input
                name="recorded_at"
                type="datetime-local"
                defaultValue={
                  source.metadata.recorded_at
                    ? new Date(
                        new Date(source.metadata.recorded_at).getTime() -
                          new Date(
                            source.metadata.recorded_at,
                          ).getTimezoneOffset() *
                            60000,
                      )
                        .toISOString()
                        .slice(0, 16)
                    : ""
                }
              />
              <small>
                Cần nhập khi dùng quy tắc theo khung giờ. Để trống nếu chưa biết
                thời điểm gốc.
              </small>
            </label>
          )}
          <label>
            Ghi chú
            <textarea
              name="notes"
              defaultValue={
                source.notes === "curb-wikimedia-demo" ? "" : source.notes
              }
              maxLength={2000}
              rows={3}
            />
          </label>
          {connection && (
            <label>
              Địa chỉ kết nối mới
              <input
                name="url"
                type="password"
                autoComplete="off"
                required
                placeholder="rtsp://…"
              />
            </label>
          )}
          <Button type="submit" variant="primary" busy={busy === "edit"}>
            <Check size={16} />
            Lưu thay đổi
          </Button>
        </form>
      </Modal>
    </>
  );
}
