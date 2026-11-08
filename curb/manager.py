import os
import subprocess
import sys
import threading
import time

from .media import NO_WINDOW, ROOT
from .store import now


ACTIVE = ("queued", "running", "finalizing", "stopping")


def terminate_worker(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill","/PID",str(process.pid),"/T","/F"],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=NO_WINDOW,timeout=10)
    else:
        process.kill()
    process.wait(timeout=10)


class JobManager:
    def __init__(self, store):
        self.store = store
        self.stop_event = threading.Event()
        self.process = None
        self.job_id = None
        self.log = None
        self.cancel_started = None
        self.thread = None

    def start(self):
        self.store.execute("UPDATE jobs SET status='interrupted',error=?,finished_at=?,updated_at=? WHERE status IN ('running','finalizing','stopping')",("Ứng dụng đã dừng giữa lượt chạy. Bằng chứng đã ghi được giữ lại; có thể chạy lại nguồn.",now(),now()))
        self.thread = threading.Thread(target=self.loop,name="curb-queue",daemon=True)
        self.thread.start()

    def loop(self):
        while not self.stop_event.wait(.4):
            if self.process:
                code = self.process.poll()
                if code is None:
                    cancel = self.store.root/"jobs"/self.job_id/"cancel"
                    if cancel.exists():
                        if self.cancel_started is None:
                            self.cancel_started = time.monotonic()
                        elif time.monotonic()-self.cancel_started > 35:
                            terminate_worker(self.process)
                            self.store.update_job(self.job_id,status="cancelled",error="Đã dừng tiến trình không phản hồi. Video đang ghi có thể chưa hoàn tất.",finished_at=now())
                    continue
                job = self.store.job(self.job_id)
                if job and job["status"] in ACTIVE:
                    self.store.update_job(self.job_id,status="failed",error=f"Tiến trình kết thúc ngoài dự kiến (mã {code}). Kiểm tra mô hình và tài nguyên.",finished_at=now())
                self.log.close()
                self.process,self.job_id,self.cancel_started = None,None,None
            with self.store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
                if row:
                    db.execute("UPDATE jobs SET status='running',started_at=?,updated_at=? WHERE id=?",(now(),now(),row["id"]))
            if not row:
                continue
            jid = row["id"]
            folder = self.store.root/"jobs"/jid
            folder.mkdir(parents=True,exist_ok=True)
            env = os.environ.copy()
            env.update({"PYTHONUTF8":"1","YOLO_CONFIG_DIR":str(self.store.root/"ultralytics"),"OPENCV_LOG_LEVEL":"SILENT"})
            self.log = open(folder/"worker.log","wb")
            try:
                camera = self.store.source(self.store.job(jid)["source_id"])["kind"] == "camera"
                self.process = subprocess.Popen([sys.executable,"-X","utf8","-m","curb.worker",str(self.store.root),jid],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=self.log,stderr=subprocess.DEVNULL if camera else self.log,env=env,creationflags=NO_WINDOW)
                self.job_id=jid
            except OSError:
                self.log.close()
                self.store.update_job(jid,status="failed",error="Không khởi động được tiến trình Python.",finished_at=now())

    def cancel(self, jid):
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            job = db.execute("SELECT status FROM jobs WHERE id=?",(jid,)).fetchone()
            if not job or job["status"] not in ACTIVE:
                return False
            if job["status"] == "queued":
                db.execute("UPDATE jobs SET status='cancelled',finished_at=?,updated_at=? WHERE id=?",(now(),now(),jid))
            else:
                folder = self.store.root/"jobs"/jid
                folder.mkdir(exist_ok=True,parents=True)
                (folder/"cancel").touch()
                db.execute("UPDATE jobs SET status='stopping',updated_at=? WHERE id=?",(now(),jid))
        return True

    def close(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        if self.process and self.process.poll() is None:
            self.cancel(self.job_id)
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                terminate_worker(self.process)
                self.store.update_job(self.job_id,status="interrupted",error="Ứng dụng đóng trong khi xử lý.",finished_at=now())
        if self.log and not self.log.closed:
            self.log.close()
