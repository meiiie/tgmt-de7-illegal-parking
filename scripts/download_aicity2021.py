"""Download the archive linked by the official 2021 Track 4 page, with resume."""
import argparse
import hashlib
import json
import socket
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import gdown
import urllib3.util.connection

FILE_ID = "1gsR4pIEiWK7htPmIjiZjXetaa1X-T-Am"
OFFICIAL_PAGE = "https://www.aicitychallenge.org/2021-track4-download/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True,exist_ok=True)
    destination = args.directory / "AICity21-Track4-Anomaly-Detection.zip"
    urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET
    started, previous = time.monotonic(), [0.0]

    def progress(received, total):
        elapsed = time.monotonic() - started
        if elapsed - previous[0] >= 5:
            previous[0] = elapsed
            print(json.dumps({"downloaded_bytes":received,"total_bytes":total,"elapsed_seconds":round(elapsed,1)}),flush=True)

    result = gdown.download(id=FILE_ID,output=str(destination),resume=True,quiet=True,use_cookies=False,timeout=(15,30),retries=3,progress=progress)
    if not result or not destination.is_file():
        raise RuntimeError("Archive download did not complete")
    with zipfile.ZipFile(destination) as archive:
        files = archive.infolist()
        labels = [info for info in files if info.filename.endswith("train-anomaly-results.txt")]
        if len(labels) != 1:
            raise RuntimeError("The downloaded archive does not contain the expected labels")
        ground_truth = archive.read(labels[0])
        (args.directory / "train-anomaly-results.txt").write_bytes(ground_truth)
    with destination.open("rb") as stream:
        digest = hashlib.file_digest(stream,"sha256").hexdigest()
    report = {"downloaded_utc":datetime.now(timezone.utc).isoformat(),"official_page":OFFICIAL_PAGE,"drive_file_id":FILE_ID,"filename":destination.name,"bytes":destination.stat().st_size,"sha256":digest,"archive_entries":len(files),"train_videos":sum(info.filename.lower().endswith(".mp4") and "train" in info.filename.lower() for info in files),"test_videos":sum(info.filename.lower().endswith(".mp4") and "test" in info.filename.lower() for info in files),"uncompressed_bytes":sum(info.file_size for info in files),"ground_truth_sha256":hashlib.sha256(ground_truth).hexdigest(),"validation":"ZIP central directory opened and training labels read with CRC verification; full video CRC/inference not yet verified"}
    (args.directory / "download-manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report),flush=True)


if __name__ == "__main__":
    main()
