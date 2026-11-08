import math
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def validate_polygon(points):
    if not 3 <= len(points) <= 32:
        raise ValueError("Vùng cần từ 3 đến 32 điểm.")
    if any(len(p) != 2 or any(not math.isfinite(v) or not 0 <= v <= 1 for v in p) for p in points):
        raise ValueError("Tọa độ vùng phải nằm trong ảnh (0–1).")
    if len(set(map(tuple, points))) != len(points):
        raise ValueError("Vùng có điểm trùng nhau.")
    area = abs(sum(a[0]*b[1] - b[0]*a[1] for a, b in zip(points, points[1:]+points[:1]))) / 2
    if area < 0.0001:
        raise ValueError("Vùng quá nhỏ hoặc không có diện tích.")

    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1]) - (b[1]-a[1])*(c[0]-a[0])

    def on(a, b, c):
        return abs(cross(a, b, c)) < 1e-10 and all(min(a[i], b[i])-1e-10 <= c[i] <= max(a[i], b[i])+1e-10 for i in (0, 1))

    edges = list(zip(points, points[1:]+points[:1]))
    for i, (a, b) in enumerate(edges):
        for j, (c, d) in enumerate(edges):
            if j <= i or j == i+1 or (i == 0 and j == len(edges)-1):
                continue
            if (cross(a,b,c)*cross(a,b,d) < 0 and cross(c,d,a)*cross(c,d,b) < 0) or any((on(a,b,c),on(a,b,d),on(c,d,a),on(c,d,b))):
                raise ValueError("Các cạnh vùng không được cắt hoặc chạm nhau.")
    return points


class Zone(Model):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=1, max_length=80)
    polygon: list[list[float]]
    dwell_seconds: float = Field(default=20, ge=2, le=86400)
    enabled: bool = True
    severity: Literal["watch", "restricted"] = "restricted"
    classes: list[Literal["car", "motorcycle", "bus", "truck"]] = Field(default_factory=lambda: ["car", "motorcycle", "bus", "truck"], min_length=1)
    suppress_congestion: bool = True
    schedule_enabled: bool = False
    start_time: str = Field(default="00:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(default="00:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    weekdays: list[int] = Field(default_factory=lambda: list(range(7)), min_length=1, max_length=7)
    _polygon = field_validator("polygon")(validate_polygon)

    @field_validator("weekdays")
    @classmethod
    def valid_days(cls,value):
        if any(day not in range(7) for day in value) or len(set(value)) != len(value):
            raise ValueError("Ngày trong tuần phải từ 0 (thứ Hai) đến 6 (Chủ nhật), không trùng.")
        return value


class SourceUpdate(Model):
    name: str = Field(min_length=1, max_length=100)
    location: str = Field(default="", max_length=160)
    notes: str = Field(default="", max_length=2000)
    recorded_at: str | None = None

    @field_validator("recorded_at")
    @classmethod
    def recording_time(cls,value):
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).astimezone().isoformat()
        except ValueError as exc:
            raise ValueError("Mốc ghi hình cần là ngày giờ hợp lệ.") from exc


class CameraCreate(SourceUpdate):
    url: str = Field(max_length=2048)

    @field_validator("url")
    @classmethod
    def camera_url(cls, value):
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"rtsp", "rtsps", "http", "https"} or not parsed.hostname or any(c in value for c in "\r\n\x00"):
            raise ValueError("Nhập địa chỉ RTSP hoặc HTTP(S) hợp lệ.")
        return value


class ZonesUpdate(Model):
    zones: list[Zone] = Field(max_length=24)

    @field_validator("zones")
    @classmethod
    def unique_ids(cls, value):
        if len({z.id for z in value}) != len(value):
            raise ValueError("Mã vùng không được trùng nhau.")
        return value


class Settings(Model):
    operator_name: str = Field(default="Người vận hành", min_length=1, max_length=80)
    site_name: str = Field(default="Trạm giám sát cục bộ", min_length=1, max_length=100)
    model: Literal["yolo26s.pt", "yolo26n.pt"] = "yolo26s.pt"
    device: Literal["auto", "cpu", "cuda"] = "auto"
    confidence: float = Field(default=0.3, ge=0.1, le=0.95)
    sample_fps: float = Field(default=5, ge=1, le=15)
    image_size: Literal[480, 640, 960] = 640
    still_window: float = Field(default=2, ge=0.5, le=10)
    movement_tolerance: float = Field(default=0.18, ge=0.03, le=0.8)
    lost_grace: float = Field(default=1.5, ge=0.2, le=5)
    minimum_area: int = Field(default=200, ge=0, le=100000)
    evidence_before: float = Field(default=5, ge=1, le=15)
    evidence_after: float = Field(default=3, ge=0, le=10)
    save_annotated: bool = True
    retention_days: int = Field(default=30, ge=1, le=3650)


class JobCreate(Model):
    source_id: str
    max_seconds: int = Field(default=0, ge=0, le=86400)


class Review(Model):
    status: Literal["pending", "confirmed", "dismissed", "resolved"]
    note: str = Field(default="", max_length=2000)
    version: int = Field(ge=0)


class PurgeRequest(Model):
    job_ids: list[str] = Field(min_length=1, max_length=100)
