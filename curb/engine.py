from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from math import hypot

from .models import Settings, Zone


def contains(poly, x, y):
    inside = False
    for a, b in zip(poly, poly[1:]+poly[:1]):
        cross = (b[0]-a[0])*(y-a[1]) - (b[1]-a[1])*(x-a[0])
        if abs(cross) < 1e-9 and min(a[0],b[0]) <= x <= max(a[0],b[0]) and min(a[1],b[1]) <= y <= max(a[1],b[1]):
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def iou(a, b):
    intersection = max(0, min(a[2],b[2])-max(a[0],b[0])) * max(0,min(a[3],b[3])-max(a[1],b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union > 0 else 0


@dataclass
class Detection:
    track_id: int
    label: str
    box: tuple[float, float, float, float]
    confidence: float = 1.0


@dataclass
class Stop:
    track_id: int
    label: str
    zone_id: str
    since: float
    last_seen: float
    anchor: tuple[float, float]
    box: tuple[float, float, float, float]
    history: deque = field(default_factory=deque)
    alerted: bool = False
    still: bool = False
    motion_since: float | None = None
    anchor_height: float = 0


class DwellEngine:
    """One stop episode per zone and track; all timestamps are source seconds."""

    def __init__(self, zones: list[Zone], settings: Settings):
        self.zones = [z for z in zones if z.enabled]
        self.settings = settings
        self.stops: dict[tuple[str, int], Stop] = {}
        self.last_time = -1.0
        self.congested: set[str] = set()

    def update(self, t: float, detections: list[Detection], width: int, height: int, wall_time: datetime | None = None):
        if t < self.last_time:
            raise ValueError("Thời gian nguồn phải tăng dần.")
        self.last_time = t
        cfg = self.settings
        present = {d.track_id for d in detections}
        for key, state in list(self.stops.items()):
            if t-state.last_seen > cfg.lost_grace:
                del self.stops[key]
        visible: dict[str, list[tuple[Stop, Detection]]] = {z.id: [] for z in self.zones}
        for zone in self.zones:
            if zone.schedule_enabled:
                if wall_time is None:
                    raise ValueError("Quy tắc theo giờ cần mốc thời gian ghi hình.")
                minute=wall_time.hour*60+wall_time.minute
                start=sum(int(v)*factor for v,factor in zip(zone.start_time.split(":"),(60,1)))
                end=sum(int(v)*factor for v,factor in zip(zone.end_time.split(":"),(60,1)))
                day=wall_time.weekday()
                if start == end:
                    enabled=day in zone.weekdays
                elif start < end:
                    enabled=day in zone.weekdays and start <= minute < end
                else:
                    enabled=(day in zone.weekdays and minute >= start) or ((day-1)%7 in zone.weekdays and minute < end)
                if not enabled:
                    self.stops={key:state for key,state in self.stops.items() if state.zone_id != zone.id}
                    continue
            for det in detections:
                x1,y1,x2,y2 = det.box
                x,y = (x1+x2)/2, y2
                key = (zone.id, det.track_id)
                eligible = det.label in zone.classes and (x2-x1)*(y2-y1) >= cfg.minimum_area and contains(zone.polygon, x/width, y/height)
                if not eligible:
                    self.stops.pop(key, None)
                    continue
                state = self.stops.get(key)
                if state is None:
                    candidates = [(k,s) for k,s in self.stops.items() if s.zone_id == zone.id and s.track_id not in present and s.label == det.label and iou(s.box,det.box) >= 0.7]
                    if candidates:
                        old_key, state = max(candidates, key=lambda pair: iou(pair[1].box, det.box))
                        del self.stops[old_key]
                        state.track_id = det.track_id
                    else:
                        state = Stop(det.track_id, det.label, zone.id, t, t, (x,y), det.box, anchor_height=y2-y1)
                    self.stops[key] = state
                tolerance = max(2.0, (y2-y1)*cfg.movement_tolerance)
                state.history.append((t,x,y))
                while len(state.history) > 1 and state.history[1][0] <= t-cfg.still_window:
                    state.history.popleft()
                excursion = max(hypot(px-x,py-y) for _,px,py in state.history)
                moved = hypot(x-state.anchor[0], y-state.anchor[1]) > tolerance or excursion > tolerance
                if state.alerted:
                    # A contracted box during partial occlusion is not a new parking episode.
                    anchor_tolerance = max(tolerance, state.anchor_height*cfg.movement_tolerance)
                    displaced = hypot(x-state.anchor[0], y-state.anchor[1]) > anchor_tolerance
                    if displaced:
                        if state.motion_since is None:
                            state.motion_since = t
                        moved = t-state.motion_since >= cfg.still_window
                    else:
                        state.motion_since = None
                        moved = False
                if moved:
                    state.since, state.anchor, state.alerted = t, (x,y), False
                    state.anchor_height, state.motion_since = y2-y1, None
                    state.history.clear()
                    state.history.append((t,x,y))
                state.last_seen, state.box = t, det.box
                state.still = state.motion_since is None and t-state.since >= cfg.still_window
                visible[zone.id].append((state,det))
        events = []
        self.congested.clear()
        for zone in self.zones:
            states = visible[zone.id]
            jam = zone.suppress_congestion and len(states) >= 4 and sum(s.still for s,_ in states)/len(states) >= 0.6
            if jam:
                self.congested.add(zone.id)
            for state,det in states:
                if state.still and not state.alerted and not jam and t-state.since >= zone.dwell_seconds:
                    state.alerted = True
                    events.append({"track_id":det.track_id,"class_name":det.label,"zone_id":zone.id,"zone_name":zone.name,"severity":zone.severity,"stop_start_s":round(state.since,3),"alert_time_s":round(t,3),"dwell_s":round(t-state.since,3),"bbox":list(det.box),"confidence":det.confidence})
        return events
