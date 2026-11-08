"""Private desktop entry point; stdin lifetime is owned by the native host."""

import argparse
import json
import os
import socket
import sys
import threading
from pathlib import Path

import uvicorn

from .api import create_app
from .instance import InstanceLock


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()
    root = Path(args.data_dir).resolve()
    os.environ["CURB_EDITION"] = "Desktop · CPU"
    lock = InstanceLock(root)
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    port = listener.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(create_app(root), host="127.0.0.1", port=port, access_log=False, timeout_graceful_shutdown=5))

    def watch_host():
        sys.stdin.readline()
        server.should_exit = True

    threading.Thread(target=watch_host, name="desktop-lifetime", daemon=True).start()
    (root / "desktop-session.json").write_text(json.dumps({"pid": os.getpid(), "url": f"http://127.0.0.1:{port}", "python": sys.executable}), encoding="utf-8")
    print(f"CURB_READY http://127.0.0.1:{port}", flush=True)
    try:
        server.run(sockets=[listener])
    finally:
        listener.close()
        lock.close()


if __name__ == "__main__":
    main()
