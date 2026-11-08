import argparse
import os
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import uvicorn

from .api import create_app
from .instance import InstanceLock
from .media import ROOT


def main():
    parser=argparse.ArgumentParser(description="Curb · ứng dụng giám sát dừng đỗ cục bộ")
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--data-dir",default=os.environ.get("CURB_DATA_DIR"))
    parser.add_argument("--open",action="store_true",help="Mở trình duyệt khi dịch vụ sẵn sàng")
    args=parser.parse_args()
    root=Path(args.data_dir or ROOT/"outputs"/"curb").resolve()
    lock=InstanceLock(root)
    if args.open:
        def open_when_ready():
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(40):
                try:
                    with opener.open(f"http://127.0.0.1:{args.port}/api/settings",timeout=1) as response:
                        if response.status == 200:
                            webbrowser.open(f"http://127.0.0.1:{args.port}/")
                            return
                except OSError:
                    time.sleep(.5)
        threading.Thread(target=open_when_ready,daemon=True).start()
    try:
        uvicorn.run(create_app(root),host="127.0.0.1",port=args.port,access_log=False)
    finally:
        lock.close()


if __name__ == "__main__":
    main()
