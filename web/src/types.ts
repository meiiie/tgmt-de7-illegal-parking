export type Vehicle = "car" | "motorcycle" | "bus" | "truck";
export type ReviewStatus = "pending" | "confirmed" | "dismissed" | "resolved";
export type JobStatus =
  | "queued"
  | "running"
  | "finalizing"
  | "stopping"
  | "completed"
  | "cancelled"
  | "failed"
  | "interrupted";
export interface Zone {
  id: string;
  name: string;
  polygon: number[][];
  dwell_seconds: number;
  enabled: boolean;
  severity: "watch" | "restricted";
  classes: Vehicle[];
  suppress_congestion: boolean;
  schedule_enabled?: boolean;
  start_time?: string;
  end_time?: string;
  weekdays?: number[];
}
export interface Source {
  id: string;
  name: string;
  kind: "video" | "camera";
  location: string;
  notes: string;
  zones: Zone[];
  archived: boolean;
  has_preview: boolean;
  connection: string;
  created_at: string;
  updated_at: string;
  metadata: {
    recorded_at?: string | null;
    width?: number;
    height?: number;
    fps?: number;
    duration?: number;
    frames?: number;
    bytes?: number;
    demo?: boolean;
    demo_id?: string;
    demo_title?: string;
    demo_description?: string;
    attribution?: string;
    source_url?: string;
    license?: string;
    license_url?: string;
    modifications?: string;
  };
}
export interface Settings {
  operator_name: string;
  site_name: string;
  model: string;
  device: string;
  confidence: number;
  sample_fps: number;
  image_size: number;
  still_window: number;
  movement_tolerance: number;
  lost_grace: number;
  minimum_area: number;
  evidence_before: number;
  evidence_after: number;
  save_annotated: boolean;
  retention_days: number;
}
export interface Job {
  id: string;
  source_id: string;
  source_name: string;
  status: JobStatus;
  progress: number;
  frames: number;
  source_seconds: number;
  fps: number;
  event_count: number;
  error: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  updated_at: string;
  config: {
    settings: Settings;
    zones: Zone[];
    source: Source;
    max_seconds: number;
  };
  metrics: Record<string, number | string | boolean | null>;
}
export interface EventRecord {
  id: string;
  job_id: string;
  source_id: string;
  source_name: string;
  zone_name: string;
  class_name: Vehicle;
  severity: "watch" | "restricted";
  status: ReviewStatus;
  version: number;
  created_at: string;
  updated_at: string;
  payload: {
    track_id: number;
    zone_id: string;
    stop_start_s: number;
    alert_time_s: number;
    dwell_s: number;
    bbox: number[];
    confidence: number;
    snapshot: string;
    clip: string;
    clip_ready: boolean;
    clip_start_s: number;
    clip_end_s?: number;
  };
  reviews?: {
    id: number;
    status: ReviewStatus;
    note: string;
    operator: string;
    created_at: string;
  }[];
  job?: Job;
}
export interface EventList {
  items: EventRecord[];
  total: number;
  page: number;
  page_size: number;
}
export interface Overview {
  sources: number;
  active_jobs: number;
  queued_jobs: number;
  events: number;
  pending: number;
  confirmed: number;
  resolved: number;
  dismissed: number;
  reviewed: number;
  processed_hours: number;
  recent_events: EventRecord[];
}
export interface Health {
  edition: string;
  cuda_supported: boolean;
  status: string;
  version: string;
  database: string;
  storage_path: string;
  free_bytes: number;
  total_bytes: number;
  gpu: string;
  ffmpeg: boolean;
  models: { name: string; available: boolean }[];
  worker_capacity: number;
  server_time: string;
}
export interface Report {
  total: number;
  by_status: { label: string; value: number }[];
  by_class: { label: string; value: number }[];
  by_source: { label: string; value: number }[];
  daily: { label: string; value: number }[];
  period_basis: string;
}
export interface StorageInfo {
  retention_days: number;
  reclaimable_bytes: number;
  free_bytes: number;
  candidates: {
    id: string;
    source_name: string;
    status: JobStatus;
    created_at: string;
    bytes: number;
    event_count: number;
  }[];
}
