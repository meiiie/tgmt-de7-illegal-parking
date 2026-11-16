"""Reproduce how FFmpeg realtime clock resets accumulate delay after a delivery stall."""
import argparse
import json
import subprocess
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    results = []
    for limit in (10,60):
        log_path = args.out / f"limit-{limit}.log"
        with log_path.open("wb") as log:
            process = subprocess.Popen(["ffmpeg","-hide_banner","-loglevel","warning","-f","rawvideo","-pixel_format","rgb24","-video_size","16x16","-framerate","10","-i","pipe:0","-vf",f"realtime=limit={limit}","-f","null","-"],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=log,bufsize=0)
            started = time.monotonic()
            for index in range(320):
                if index == 80:
                    time.sleep(13)
                remaining = started+index/10-time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
                process.stdin.write(bytes([index % 256])*16*16*3)
            process.stdin.close()
            code = process.wait(timeout=40)
            elapsed = time.monotonic()-started
        text = log_path.read_text(encoding="utf-8",errors="replace")
        row = {"limit_seconds":limit,"media_seconds":32,"injected_network_stall_seconds":13,"wall_seconds":round(elapsed,3),"clock_resets":text.count("time discontinuity detected"),"exit_code":code}
        results.append(row)
        print(json.dumps(row),flush=True)
    (args.out / "report.json").write_text(json.dumps(results,indent=2),encoding="utf-8")
    assert results[0]["clock_resets"] >= 1
    assert results[1]["clock_resets"] == 0
    assert results[0]["wall_seconds"]-results[1]["wall_seconds"] > 8


if __name__ == "__main__":
    main()
