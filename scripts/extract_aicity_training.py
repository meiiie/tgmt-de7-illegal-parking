"""Validate complete training members, including from a still-downloading ZIP prefix."""
import argparse
import binascii
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True,exist_ok=True)
    records = []
    size = args.archive.stat().st_size
    with args.archive.open("rb") as stream:
        while stream.tell()+30 <= size:
            offset = stream.tell()
            header = struct.unpack("<IHHHHHIIIHH",stream.read(30))
            if header[0] != 0x04034B50:
                break
            flags, compression, crc, packed, unpacked, name_size, extra_size = header[2],header[3],header[6],header[7],header[8],header[9],header[10]
            name = stream.read(name_size).decode("utf-8")
            stream.seek(extra_size,1)
            data_start = stream.tell()
            if flags & 8 or packed == 0xFFFFFFFF:
                raise RuntimeError("ZIP member needs a central-directory reader")
            if data_start+packed > size:
                break
            matched = re.fullmatch(r"AIC21-Track4-Anomaly-Detection/aic21-track4-train-data/(\d+\.mp4)",name)
            filename = matched[1] if matched else "train-anomaly-results.txt" if name.endswith("/train-anomaly-results.txt") else "ReadMe.txt" if name.endswith("/ReadMe.txt") else None
            if filename:
                if compression not in (0,8):
                    raise RuntimeError("Unsupported ZIP compression")
                target = args.directory / filename
                if target.exists():
                    raise FileExistsError(f"Refusing to overwrite {filename}")
                remaining, written, actual_crc = packed, 0, 0
                digest = hashlib.sha256()
                decoder = zlib.decompressobj(-15) if compression == 8 else None
                with target.open("xb") as output:
                    while remaining:
                        block = stream.read(min(1024**2,remaining))
                        if not block:
                            raise EOFError(name)
                        remaining -= len(block)
                        decoded = decoder.decompress(block) if decoder else block
                        output.write(decoded)
                        digest.update(decoded)
                        actual_crc = binascii.crc32(decoded,actual_crc)
                        written += len(decoded)
                if written != unpacked or actual_crc & 0xFFFFFFFF != crc or (decoder and not decoder.eof):
                    raise RuntimeError(f"CRC or length mismatch for {filename}")
                records.append({"file":filename,"bytes":written,"sha256":digest.hexdigest(),"zip_crc32":f"{crc:08x}","zip_offset":offset,"crc_verified":True})
                print(json.dumps({"extracted":filename,"bytes":written}),flush=True)
            stream.seek(data_start+packed)
    videos = [r for r in records if r["file"].endswith(".mp4")]
    report = {"source":"official AICity21-Track4-Anomaly-Detection.zip","archive_bytes_available_at_start":size,"complete_archive_verified":False,"training_videos":len(videos),"files":records}
    (args.directory / "training-manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if len(videos) != 100:
        raise RuntimeError(f"Only {len(videos)} complete training videos available; expected 100")
    print(json.dumps({"training_videos":len(videos),"all_extracted_members_crc_verified":True}),flush=True)


if __name__ == "__main__":
    main()
