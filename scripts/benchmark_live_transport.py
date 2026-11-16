"""Measure FFmpeg live delivery before inference; keep signed media URLs local."""
import argparse
import json
import os
import subprocess
import threading
import time
from pathlib import Path


def measure(source, out, label, input_options, seconds, output_filter="fps=5"):
    folder = out / label
    folder.mkdir(exist_ok=False)
    arrived = []
    latest = [None]
    stop = threading.Event()
    log = (folder / "decoder.private.log").open("wb")
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "warning", "-stats_period", "1", "-progress", "pipe:2", *input_options, "-rw_timeout", "15000000", "-i", source["url"], "-an", "-vf", output_filter, "-c:v", "mjpeg", "-q:v", "4", "-flush_packets", "1", "-f", "image2pipe", "pipe:1"]
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=log, bufsize=0)

    def drain():
        data = bytearray()
        while not stop.is_set():
            chunk = os.read(proc.stdout.fileno(), 65536)
            if not chunk:
                break
            data.extend(chunk)
            while True:
                start = data.find(b"\xff\xd8")
                end = data.find(b"\xff\xd9", max(0, start))
                if start < 0 or end < 0:
                    break
                frame = bytes(data[start:end + 2])
                del data[:end + 2]
                arrived.append(time.monotonic())
                latest[0] = frame
                if len(arrived) == 1:
                    (folder / "first.jpg").write_bytes(frame)

    thread = threading.Thread(target=drain, daemon=True)
    before = time.monotonic()
    thread.start()
    try:
        while time.monotonic() - before < seconds and proc.poll() is None:
            time.sleep(.1)
    finally:
        stop.set()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        thread.join(timeout=2)
        log.close()
    if latest[0]:
        (folder / "last.jpg").write_bytes(latest[0])
    gap = [b - a for a, b in zip(arrived, arrived[1:])]
    progress = {}
    text = (folder / "decoder.private.log").read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key in ("frame", "fps", "out_time_us", "speed"):
                progress[key] = value
    report = {"label":label,"seconds":round(time.monotonic()-before,3),"frames":len(arrived),"delivery_fps":round(len(arrived)/seconds,3),"first_frame_wait_s":round(arrived[0]-before,3) if arrived else None,"max_interarrival_s":round(max(gap),3) if gap else None,"input_options":input_options,"output_filter":output_filter,"progress":progress,"tls_error_count":text.count("[tls"),"interarrival_s":[round(x,4) for x in gap]}
    (folder / "report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({key:value for key,value in report.items() if key != "interarrival_s"}),flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=35)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    source = json.loads(args.metadata.read_text(encoding="utf-8-sig"))
    reports = [measure(source,args.out,label,options,args.seconds) for label,options in (("readrate-on",["-re"]),("readrate-off",[]),("live-edge",["-live_start_index","-1"]))]
    (args.out / "report.json").write_text(json.dumps(reports,indent=2),encoding="utf-8")


if __name__ == "__main__":
    main()
