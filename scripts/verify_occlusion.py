"""Development regression on MERL Test006; not an independent accuracy benchmark."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

bootstrap = argparse.ArgumentParser(add_help=False)
bootstrap.add_argument("--app-root", type=Path, default=Path(__file__).resolve().parents[1])
runtime, _ = bootstrap.parse_known_args()
sys.path.insert(0, str(runtime.app_root))
from fastapi.testclient import TestClient
from curb import worker
from curb.api import DEMO, create_app
from curb.engine import DwellEngine
from curb.media import sha256


def main():
    parser = argparse.ArgumentParser(parents=[bootstrap])
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    baseline_events, frames = [], []
    baseline_type = None
    if args.baseline:
        spec = importlib.util.spec_from_file_location("curb.baseline_engine", args.baseline)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        baseline_type = module.DwellEngine

    class CompareEngine(DwellEngine):
        def __init__(self, zones, settings):
            super().__init__(zones, settings)
            self.baseline = baseline_type(zones, settings) if baseline_type else None

        def update(self, t, detections, width, height, wall_time=None):
            if self.baseline:
                baseline_events.extend(self.baseline.update(t, detections, width, height, wall_time))
            frames.append({"time": t, "detections": [vars(d) for d in detections]})
            return super().update(t, detections, width, height, wall_time)

    worker.DwellEngine = CompareEngine
    app = create_app(args.data_dir, start_worker=False)
    with TestClient(app) as client:
        settings = client.get("/api/settings").json()
        settings.update(device=args.device, sample_fps=5, image_size=640, model="yolo26s.pt")
        client.put("/api/settings", json=settings).raise_for_status()
        with args.video.open("rb") as video:
            response = client.post("/api/sources/upload", data={"name": "MERL Test006 · regression 60s"}, files={"file": (args.video.name, video, "video/mp4")})
        response.raise_for_status()
        source = response.json()
        client.put(f'/api/sources/{source["id"]}/zones', json={"zones": [DEMO["zone"]]}).raise_for_status()
        response = client.post("/api/jobs", json={"source_id": source["id"]})
        response.raise_for_status()
        job_id = response.json()["id"]
        worker.run(app.state.store, job_id)
        job = client.get(f"/api/jobs/{job_id}").json()
        events = client.get("/api/events", params={"source_id": source["id"]}).json()["items"]
        manifest = json.loads((args.data_dir / "jobs" / job_id / "manifest.json").read_text(encoding="utf-8"))
        report = {"purpose": "development regression, not independent evaluation", "video_sha256": sha256(args.video), "baseline_sha256": sha256(args.baseline) if args.baseline else None, "baseline_events": baseline_events, "events": events, "job": job, "manifest": manifest}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        args.output.with_suffix(".detections.json").write_text(json.dumps(frames), encoding="utf-8")
        assert job["status"] == "completed", job["status"]
        assert len(events) == 3, f"Expected 3 stop episodes; got {len(events)}"
        assert len({event["payload"]["track_id"] for event in events}) == 3
        print(json.dumps({"job": job_id, "before": len(baseline_events), "after": len(events), "metrics": job["metrics"]}))


if __name__ == "__main__":
    main()
