"""Exercise the Curb worker on a public YouTube live feed via a local MJPEG bridge."""
import argparse
import hashlib
import json
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from curb.models import Settings, Zone
from curb.store import Store, new_id, now
from curb.worker import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=120)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda")
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--serve-only", action="store_true", help="Provide the local camera URL for Curb without running inference")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args()
    if not (10 <= args.seconds <= 600 or args.serve_only and args.seconds == 0):
        parser.error("Use 10–600 seconds for this bounded smoke test")
    args.out.mkdir(parents=True, exist_ok=False)
    if args.metadata:
        source = json.loads(args.metadata.read_text(encoding="utf-8-sig"))
    else:
        extraction = subprocess.run(
            ["uv", "tool", "run", "--from", "yt-dlp==2026.10.26", "yt-dlp", "--no-warnings", "--force-ipv4", "--socket-timeout", "15", "--retries", "1", "--extractor-retries", "1", "--skip-download", "-f", "bestvideo[height<=480]/best[height<=480]", "--dump-single-json", args.url],
            capture_output=True, encoding="utf-8", timeout=60,
        )
        if extraction.returncode:
            raise RuntimeError("YouTube metadata extraction failed; no inference was run")
        source = json.loads(extraction.stdout)
    if not source.get("is_live"):
        raise RuntimeError("The supplied source is not currently live")
    public = {k: source.get(k) for k in ("id", "title", "channel", "webpage_url", "live_status", "format_id", "width", "height", "fps", "protocol")}
    log = (args.out / "bridge.private.log").open("wb")
    decoder = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning", "-stats_period", "1", "-progress", "pipe:2", "-live_start_index", "-3", "-http_persistent", "0", "-rw_timeout", "15000000", "-i", source["url"], "-an", "-vf", "fps=10,realtime=limit=60", "-c:v", "mjpeg", "-q:v", "4", "-flush_packets", "1", "-f", "image2pipe", "pipe:1"],
        stdout=subprocess.PIPE, stderr=log,
    )
    changed = threading.Condition()
    shared = {"frame": None, "sequence": 0, "running": True, "first": None, "last": None, "max_gap": 0.0}

    def produce():
        data = bytearray()
        try:
            while shared["running"]:
                block = decoder.stdout.read1(65536)
                if not block:
                    break
                data.extend(block)
                while True:
                    start = data.find(b"\xff\xd8")
                    end = data.find(b"\xff\xd9", max(start, 0))
                    if start < 0 or end < 0:
                        break
                    frame = bytes(data[start:end + 2])
                    del data[:end + 2]
                    with changed:
                        shared["frame"] = frame
                        shared["sequence"] += 1
                        timestamp = time.monotonic()
                        if shared["last"] is not None:
                            shared["max_gap"] = max(shared["max_gap"], timestamp-shared["last"])
                        shared["last"] = timestamp
                        shared["first"] = shared["first"] or shared["last"]
                        changed.notify_all()
                    if shared["sequence"] == 1:
                        (args.out / "first-frame.jpg").write_bytes(frame)
        finally:
            with changed:
                shared["running"] = False
                changed.notify_all()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            previous = -1
            try:
                while shared["running"]:
                    with changed:
                        changed.wait_for(lambda: shared["sequence"] != previous or not shared["running"], timeout=10)
                        frame, sequence = shared["frame"], shared["sequence"]
                    if not frame or previous == sequence:
                        continue
                    self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(frame)).encode() + b"\r\n\r\n" + frame + b"\r\n")
                    self.wfile.flush()
                    previous = sequence
            except (ConnectionError, OSError):
                pass

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    threading.Thread(target=produce, daemon=True).start()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    started = datetime.now(timezone.utc).isoformat()
    report = {"source": public, "started_utc": started, "requested_seconds": args.seconds, "transport": "YouTube video-only HLS via yt-dlp 2026.10.26 -> FFmpeg live_start_index=-3, http_persistent=0, fps=10,realtime=limit=60, flush_packets=1 -> latest-frame MJPEG -> asynchronously drained Curb capture, scheduled inference at 5 FPS", "accuracy_evaluation": False, "camera_to_alert_latency_measured": False}
    try:
        with changed:
            ready = changed.wait_for(lambda: shared["frame"] is not None or not shared["running"], timeout=30)
        if not ready or shared["frame"] is None:
            raise RuntimeError("No decoded live frame reached the bridge")
        if args.serve_only:
            report["status"] = "streaming"
            report["local_camera_url"] = f"http://127.0.0.1:{server.server_port}/live"
            print(json.dumps({"camera_url":report["local_camera_url"],"instruction":"Add this HTTP camera in Curb. Keep this process running; Ctrl+C stops it."}),flush=True)
            serving_start = time.monotonic()
            try:
                while shared["running"] and (not args.seconds or time.monotonic()-serving_start < args.seconds):
                    time.sleep(.2)
            except KeyboardInterrupt:
                pass
            report["status"] = "stopped"
            report["bridge_frames_produced"] = shared["sequence"]
            return
        store = Store(args.out / "data")
        zone = Zone(id="road-watch", name="Mặt đường · thử vận hành", polygon=[[0,.35],[.55,.22],[.73,.20],[.47,.99],[0,.99]], dwell_seconds=20, severity="watch", suppress_congestion=True)
        settings = Settings(device=args.device, sample_fps=5, image_size=640, save_annotated=False)
        camera = store.add_source("Camera cổng trường Nguyễn Huệ · thử vận hành", "camera", f"http://127.0.0.1:{server.server_port}/live", metadata={"width":source["width"],"height":source["height"],"source_url":args.url}, zones=[zone.model_dump()])
        jid, stamp = new_id(), now()
        config = {"settings":settings.model_dump(),"zones":camera["zones"],"source":store.public_source(camera),"max_seconds":args.seconds}
        store.execute("INSERT INTO jobs(id,source_id,source_name,status,config,created_at,updated_at) VALUES(?,?,?,'queued',?,?,?)", (jid,camera["id"],camera["name"],json.dumps(config,ensure_ascii=False),stamp,stamp))
        print(json.dumps({"phase":"inference_started","job_id":jid,"source_id":public["id"],"seconds":args.seconds}), flush=True)
        run(store, jid)
        job = store.job(jid)
        manifest = json.loads((store.root / "jobs" / jid / "manifest.json").read_text(encoding="utf-8"))
        report.update({"status":job["status"],"job_id":jid,"metrics":job["metrics"],"configuration":config,"manifest":manifest})
        report["harness_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report["first_frame_sha256"] = hashlib.sha256((args.out / "first-frame.jpg").read_bytes()).hexdigest()
        report["bridge_frames_produced"] = shared["sequence"]
        report["bridge_max_gap_s"] = round(shared["max_gap"],4)
    finally:
        with changed:
            shared["running"] = False
            changed.notify_all()
        decoder.terminate()
        try:
            decoder.wait(timeout=5)
        except subprocess.TimeoutExpired:
            decoder.kill()
            decoder.wait()
        server.shutdown()
        log.close()
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (args.out / "report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2), encoding="utf-8")
    print(json.dumps({"status":report["status"],"metrics":report["metrics"]}), flush=True)


if __name__ == "__main__":
    main()
