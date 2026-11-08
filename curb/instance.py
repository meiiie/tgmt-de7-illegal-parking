import os
from pathlib import Path


class InstanceLock:
    def __init__(self, root: Path):
        root.mkdir(parents=True,exist_ok=True)
        self.file=(root/"app.lock").open("a+b")
        if self.file.tell() == 0:
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.file.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self.file.close()
            raise RuntimeError("Thư mục dữ liệu này đang được một phiên Curb khác sử dụng. Mở phiên đang chạy hoặc chọn thư mục dữ liệu khác.") from exc

    def close(self):
        self.file.close()
