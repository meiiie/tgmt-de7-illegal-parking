"""Reproduce rule-engine behavior with synthetic detections, without model inference."""

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import platform
from pathlib import Path
import subprocess
import sys
import uuid
from unittest.mock import patch

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import evaluate
import pipeline


def run_scenario(folder, observations, polygon, missing_video=False):
    folder.mkdir(parents=True)
    video = folder / "input.avi"
    frame = np.zeros((64, 64, 3), dtype=np.uint8)
    if not missing_video:
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*"MJPG"), 1, (64, 64))
        if not writer.isOpened():
            raise RuntimeError("MJPG video writer is unavailable")
        for _ in observations:
            writer.write(frame)
        writer.release()
    config = {
        "still_window_s": 1,
        "still_tol": 0.15,
        "lost_grace_s": 3,
        "zones": [{"name": "test_zone", "polygon": polygon, "max_dwell_s": 4}],
    }
    zones = folder / "zones.json"
    zones.write_text(json.dumps(config), encoding="utf-8")

    def synthetic_backend(args, timers):
        for fi, image in pipeline.frames(args.video, args.stride, args.max_frames):
            detections = [
                {"id": tid, "box": np.array(box, dtype=float), "cls": "car", "mask": None, "score": 1.0}
                for tid, box in observations[fi]
            ]
            yield fi, image, detections

    argv = ["pipeline.py", "--video", str(video), "--zones", str(zones), "--out", str(folder), "--device", "cpu"]
    with patch.object(sys, "argv", argv), patch.object(pipeline, "yolo_backend", synthetic_backend):
        with contextlib.redirect_stdout(io.StringIO()):
            pipeline.main()
    alerts = json.loads((folder / "alerts.json").read_text(encoding="utf-8"))
    metrics = json.loads((folder / "metrics.json").read_text(encoding="utf-8"))
    return alerts, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    work = ROOT / "outputs" / ("baseline-inspection-" + uuid.uuid4().hex[:8])
    full = [[0, 0], [1, 0], [1, 1], [0, 1]]
    left = [[0, 0], [0.5, 0], [0.5, 1], [0, 1]]
    checks = []

    def record(name, expected, observed, evidence):
        checks.append({"case": name, "expected": expected, "observed": observed, "meets_expectation": observed == expected, "evidence": evidence})

    still = [[(1, [21, 10, 41, 50])]] * 6
    alerts, _ = run_scenario(work / "stationary_positive", still, left)
    record("stationary_positive", 1, len(alerts), "The real pipeline.main emits an alert after four seconds.")

    moving = [[(1, [i * 8, 10, i * 8 + 20, 50])] for i in range(6)]
    alerts, _ = run_scenario(work / "moving_negative", moving, full)
    record("moving_negative", 0, len(alerts), "The bottom-center moves eight pixels each second.")

    outside = still[:3] + [[(1, [23, 10, 43, 50])]] * 3
    alerts, _ = run_scenario(work / "exit_roi", outside, left)
    record("exit_roi", 0, len(alerts), {"alert_times": [a["alert_time_s"] for a in alerts], "bottom_center_x": 33, "roi_max_x": 32})

    episodes = still + [[]] * 5 + [[(2, [21, 10, 41, 50])]] * 6
    alerts, _ = run_scenario(work / "two_episodes", episodes, left)
    record("two_distinct_stop_episodes", 2, len(alerts), {"alert_times": [a["alert_time_s"] for a in alerts], "second_episode_starts_s": 11})

    first = {"video": "test.mp4", "zone": "a", "stop_start_s": 0, "alert_time_s": 4, "bbox": [0, 0, 20, 20]}
    later = {**first, "stop_start_s": 100, "alert_time_s": 104}
    record("evaluator_distinct_episodes", 2, len(evaluate.filter_alerts([first, later], 0.3)), "Same position, separate events one hundred seconds apart.")
    other_zone = {**first, "zone": "b"}
    record("evaluator_separate_zones", 2, len(evaluate.filter_alerts([first, other_zone], 0.3)), "Different zones are currently deduplicated together.")

    gt = [{"video": "test.mp4", "zone": "a", "stop_start_s": 0, "stop_end_s": 20, "bbox": [100, 100, 120, 120]}]
    scores = evaluate.score(gt, [first])
    record("spatial_event_matching", 0, scores["tp"], "GT and prediction boxes do not overlap. The current temporal-only evaluator ignores GT bbox.")

    track = pipeline.Track(1, "car")
    track.hist.extend([(0, 0, 0, 40), (1, 100, 0, 40), (2, 0, 0, 40)])
    record("motion_between_equal_endpoints", False, bool(track.stationary(2, 2, 0.15)), "A moving or jittering track returns to its first position within the observation window.")

    try:
        _, metrics = run_scenario(work / "missing_video", [], full, missing_video=True)
        rejected = False
        missing_evidence = {"returned_normally": True, "frames_processed": metrics["frames_processed"]}
    except (ValueError, RuntimeError) as error:
        rejected = True
        missing_evidence = {"error_type": type(error).__name__}
    record("missing_video_rejected", True, rejected, missing_evidence)

    versions = {}
    for name in ["numpy", "opencv-python", "torch", "ultralytics", "gradio", "transformers", "lap"]:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    paths = ["src/pipeline.py", "src/evaluate.py", "app.py", "scripts/inspect_baseline.py"]
    report = {
        "kind": "synthetic_rule_engine_characterization",
        "date": "2026-11-06",
        "timezone": "Asia/Saigon",
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version,
        "platform": platform.platform(),
        "packages": versions,
        "source_sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "seed": None,
        "data": "Deterministic black 64x64 MJPG frames at one FPS, with prescribed boxes and IDs. No dataset split.",
        "limitations": ["No detector, tracker, re-ID or SAM model is executed.", "No accuracy, GPU performance or browser usability claim is made.", "Spatial matching is a proposed stronger contract, not the current evaluator specification.", "The missing-video probe replaces the model backend; full model startup is not covered."],
        "artifacts": str(work.relative_to(ROOT)),
        "checks": checks,
        "summary": {"total": len(checks), "met": sum(c["meets_expectation"] for c in checks), "unmet": sum(not c["meets_expectation"] for c in checks)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.output), **report["summary"]}))
    return 1 if report["summary"]["unmet"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
