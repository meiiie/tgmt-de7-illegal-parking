import argparse
import shutil
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path


def restore(archive: Path, destination: Path):
    destination=destination.resolve()
    if destination.exists():
        raise ValueError("Thư mục đích phải chưa tồn tại để không ghi đè dữ liệu hiện có.")
    with zipfile.ZipFile(archive) as source:
        entries=source.infolist()
        if "curb.sqlite3" not in source.namelist():
            raise ValueError("Không phải bản sao lưu Curb.")
        total=sum(info.file_size for info in entries)
        destination.parent.mkdir(parents=True,exist_ok=True)
        if total+350*1024**2 > shutil.disk_usage(destination.parent).free:
            raise ValueError("Không đủ dung lượng khôi phục và 350 MB dự phòng.")
        for info in entries:
            path=(destination/info.filename).resolve()
            if not path.is_relative_to(destination) or path == destination or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Bản sao lưu chứa đường dẫn không hợp lệ.")
        destination.mkdir()
        source.extractall(destination)
    with closing(sqlite3.connect(destination/"curb.sqlite3")) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Cơ sở dữ liệu không toàn vẹn.")
        for sid,uri in db.execute("SELECT id,uri FROM sources WHERE kind='video'").fetchall():
            path=(destination/uri).resolve()
            if not path.is_relative_to(destination/"uploads"):
                raise ValueError("Nguồn video nằm ngoài thư mục sao lưu.")
            db.execute("UPDATE sources SET uri=? WHERE id=?",(str(path),sid))
        db.execute("UPDATE sources SET metadata='{}' WHERE kind='camera'")
        db.commit()
    return destination


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description="Khôi phục Curb sang thư mục mới; không ghi đè dữ liệu.")
    parser.add_argument("archive",type=Path)
    parser.add_argument("--destination",type=Path,required=True)
    args=parser.parse_args()
    try:
        print(restore(args.archive,args.destination))
    except (OSError, ValueError, zipfile.BadZipFile, sqlite3.Error) as error:
        parser.exit(1, f"Không khôi phục được bản sao lưu: {error}\n")
