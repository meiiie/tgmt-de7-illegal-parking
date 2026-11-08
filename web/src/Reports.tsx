import { useState } from "react";
import { BarChart3, CheckCheck, ClipboardCheck, Clock3 } from "lucide-react";
import {
  Download,
  Empty,
  ErrorBox,
  Loading,
  number,
  statusLabels,
  useResource,
  vehicleLabels,
} from "./lib";
import type { Report, Source } from "./types";

function Breakdown({
  title,
  rows,
  labels,
}: {
  title: string;
  rows: { label: string; value: number }[];
  labels?: Record<string, string>;
}) {
  const total = rows.reduce((sum, row) => sum + row.value, 0);
  return (
    <section className="panel breakdown">
      <h2>{title}</h2>
      {rows.length ? (
        rows.map((row, i) => (
          <div className="breakdown-row" key={row.label}>
            <div>
              <span>
                <i className={`chart-key key-${i % 4}`} />
                {labels?.[row.label] ?? row.label}
              </span>
              <strong>
                {row.value}
                <small>{number((row.value / Math.max(1, total)) * 100)}%</small>
              </strong>
            </div>
            <progress
              max={total}
              value={row.value}
              className={`key-${i % 4}`}
            />
          </div>
        ))
      ) : (
        <p className="muted">Chưa có dữ liệu trong khoảng đã chọn.</p>
      )}
    </section>
  );
}

export function ReportsPage() {
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [source, setSource] = useState("");
  const params = new URLSearchParams({ start, end, source_id: source });
  const resource = useResource<Report>(`/reports?${params}`, 5000);
  const sources = useResource<Source[]>("/sources");
  const report = resource.data;
  const count = (label: string) =>
    report?.by_status.find((row) => row.label === label)?.value ?? 0;
  const max = Math.max(1, ...(report?.daily.map((row) => row.value) ?? []));
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Báo cáo</h1>
        </div>
        <div className="actions">
          <Download path={`/export/events?${params}`} name="curb-report.csv">
            CSV
          </Download>
          <Download
            path={`/export/events?format=json&${params}`}
            name="curb-report.json"
          >
            JSON
          </Download>
        </div>
      </div>
      <section className="panel report-filters">
        <label>
          Từ ngày
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label>
          Đến ngày
          <input
            type="date"
            min={start}
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
        <label>
          Nguồn giám sát
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">Tất cả nguồn</option>
            {sources.data?.map((s) => (
              <option value={s.id} key={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </label>
      </section>
      <ErrorBox message={resource.error} retry={resource.refresh} />
      {!report ? (
        <Loading />
      ) : (
        <>
          <div className="stat-grid report-stats">
            <article className="stat-card">
              <span>
                <BarChart3 size={18} />
                Tổng cảnh báo
              </span>
              <strong>{report.total}</strong>

            </article>
            <article className="stat-card">
              <span>
                <ClipboardCheck size={18} />
                Đã xác nhận
              </span>
              <strong>{count("confirmed")}</strong>

            </article>
            <article className="stat-card">
              <span>
                <CheckCheck size={18} />
                Đã xử lý
              </span>
              <strong>{count("resolved")}</strong>

            </article>
            <article className="stat-card">
              <span>
                <Clock3 size={18} />
                Đang chờ xem xét
              </span>
              <strong>{count("pending")}</strong>

            </article>
          </div>
          <section className="panel report-chart">
            <div className="section-heading">
              <div>
                <h2>Cảnh báo theo ngày</h2>
                <p>{report.period_basis}</p>
              </div>
              <span className="legend">
                <i className="chart-key" />
                Số cảnh báo
              </span>
            </div>
            {report.daily.length ? (
              <div
                className="daily-chart"
                role="img"
                aria-label={report.daily
                  .map((row) => `${row.label}: ${row.value} cảnh báo`)
                  .join("; ")}
              >
                {report.daily.map((row) => (
                  <div className="day-column" key={row.label}>
                    <strong>{row.value}</strong>
                    <div className="day-bar-space">
                      <div
                        className="day-bar"
                        style={{ height: `${(row.value / max) * 100}%` }}
                      />
                    </div>
                    <span>
                      {row.label.slice(8)}/{row.label.slice(5, 7)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <Empty
                icon={<BarChart3 size={30} />}
                title="Chưa có số liệu trong khoảng này"
              >
                Chọn khoảng ngày khác hoặc xử lý thêm nguồn video.
              </Empty>
            )}
          </section>
          <div className="report-breakdowns">
            <Breakdown
              title="Theo loại phương tiện"
              rows={report.by_class}
              labels={vehicleLabels}
            />
            <Breakdown
              title="Theo quyết định"
              rows={report.by_status}
              labels={statusLabels}
            />
            <Breakdown title="Theo nguồn giám sát" rows={report.by_source} />
          </div>
          <div className="info-banner">
            <ClipboardCheck size={20} />
            <div>
              <strong>Số cảnh báo không phải số vi phạm đã xác minh</strong>
              <span>
                Báo cáo phản ánh dữ liệu vận hành và quyết định duyệt. Không suy
                ra độ chính xác mô hình từ các số đếm này.
              </span>
            </div>
          </div>
        </>
      )}
    </>
  );
}
