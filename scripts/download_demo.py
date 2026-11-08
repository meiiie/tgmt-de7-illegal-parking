import concurrent.futures
import hashlib
import json
import os
import struct
import subprocess
import tempfile
import time
import zlib
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "scripts/demo-frames.json").read_text(encoding="utf-8"))
    cache = Path(tempfile.gettempdir()) / "CurbDemo" / "merl-test006-v1"
    cache.mkdir(parents=True, exist_ok=True)

    def fetch(item):
        number, entry = item
        target = cache / f"{number:06d}.jpg"
        if target.exists():
            data = target.read_bytes()
            if len(data) == entry["size"] and zlib.crc32(data) == entry["crc"]:
                return hashlib.sha256(data).hexdigest()
        start = entry["offset"]
        end = start + 30 + len(entry["name"].encode("utf-8")) + 100 + entry["compressed"]
        for attempt in range(4):
            try:
                with requests.get(manifest["url"], headers={"Range": f"bytes={start}-{end}"}, timeout=60, stream=True) as response:
                    if response.status_code in (429, 500, 502, 503, 504):
                        time.sleep(min(30, 3 * (attempt + 1)))
                        continue
                    response.raise_for_status()
                    expected = f"bytes {start}-{end}/{manifest['archive_size']}"
                    if response.status_code != 206 or response.headers.get("Content-Range") != expected:
                        raise RuntimeError("Server không hỗ trợ tải từng phần; không tải toàn bộ 49 GB.")
                    data = response.raw.read(end - start + 2, decode_content=False)
                if len(data) != end - start + 1 or data[:4] != b"PK\x03\x04":
                    raise RuntimeError("ZIP range không hợp lệ")
                name_size, extra_size = struct.unpack_from("<HH", data, 26)
                if data[30:30 + name_size].decode("utf-8") != entry["name"]:
                    raise RuntimeError("Tên frame không khớp manifest")
                offset = 30 + name_size + extra_size
                payload = data[offset:offset + entry["compressed"]]
                method = struct.unpack_from("<H", data, 8)[0]
                decoded = zlib.decompress(payload, -15) if method == 8 else payload
                if len(decoded) != entry["size"] or zlib.crc32(decoded) != entry["crc"]:
                    raise RuntimeError("CRC frame không khớp")
                target.write_bytes(decoded)
                return hashlib.sha256(decoded).hexdigest()
            except requests.RequestException:
                if attempt == 3:
                    raise
                time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"Không tải được {entry['name']}; có thể chạy lại để tiếp tục.")

    hashes = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for number, digest in enumerate(pool.map(fetch, enumerate(manifest["frames"], 1)), 1):
            hashes.append(digest)
            if number % 30 == 0:
                print(f"Đã kiểm tra {number}/{len(manifest['frames'])} frame", flush=True)
    output = ROOT / "data/streetscene_test006_30s.mp4"
    output.parent.mkdir(exist_ok=True)
    temporary = output.with_suffix(".part.mp4")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(manifest["fps"]),
                    "-start_number", "1", "-i", str(cache / "%06d.jpg"), "-frames:v", str(len(hashes)),
                    "-an", "-c:v", "libx264", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporary)], check=True)
    os.replace(temporary, output)
    report = {"source": manifest["record"], "sequence": manifest["sequence"], "source_fps": manifest["source_fps"],
              "sample_step": manifest["sample_step"], "fps": manifest["fps"], "frames": len(hashes), "frame_sha256": hashes,
              "sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "bytes": output.stat().st_size}
    output.with_suffix(".provenance.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "frame_sha256"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
