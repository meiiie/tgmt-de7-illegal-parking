import csv
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import zipfile
from functools import wraps
from contextlib import asynccontextmanager, closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import PRODUCT, __version__
from .manager import ACTIVE, JobManager
from .media import NO_WINDOW, ROOT, probe, sha256
from .models import CameraCreate, JobCreate, PurgeRequest, Review, Settings, SourceUpdate, ZonesUpdate
from .store import Store, new_id, now

DEMO = json.loads(Path(__file__).with_name("demo.json").read_text(encoding="utf-8"))

def create_app(data_dir=None, start_worker=True):
    store = Store(Path(data_dir or os.environ.get("CURB_DATA_DIR",ROOT/"outputs"/"curb")))
    manager = JobManager(store)
    operation_lock = threading.Lock()

    def exclusive_operation(function):
        @wraps(function)
        def wrapped(*args,**kwargs):
            if not operation_lock.acquire(blocking=False):
                raise HTTPException(409,"Đang nhập, sao lưu hoặc bảo trì dữ liệu. Chờ hoàn tất rồi thử lại.")
            try:
                return function(*args,**kwargs)
            finally:
                operation_lock.release()
        return wrapped

    @asynccontextmanager
    async def lifespan(app):
        if start_worker:
            manager.start()
        yield
        if start_worker:
            manager.close()

    app = FastAPI(title="Curb · Giám sát dừng đỗ",version=__version__,lifespan=lifespan,docs_url="/api/docs",redoc_url=None,openapi_url="/api/openapi.json")
    app.state.store, app.state.manager = store, manager
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=["127.0.0.1","localhost","[::1]","testserver"])

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in {"GET","HEAD","OPTIONS"} and origin:
            parsed=urlsplit(origin)
            if parsed.netloc != request.headers.get("host") or parsed.scheme not in {"http","https"}:
                return JSONResponse({"detail":"Yêu cầu khác nguồn bị từ chối. Mở ứng dụng trực tiếp trên máy này."},status_code=403)
        response=await call_next(request)
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="same-origin"
        response.headers["Cross-Origin-Resource-Policy"]="same-origin"
        response.headers["X-Frame-Options"]="DENY"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"]="no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        messages=[]
        for error in exc.errors():
            messages.append(".".join(str(p) for p in error["loc"][1:])+": "+error["msg"].removeprefix("Value error, "))
        return JSONResponse({"detail":"; ".join(messages)},status_code=422)

    def source_or_404(sid):
        if not re.fullmatch(r"[a-f0-9]{32}",sid):
            raise HTTPException(404,"Không tìm thấy nguồn.")
        source=store.source(sid)
        if not source:
            raise HTTPException(404,"Không tìm thấy nguồn.")
        return source

    def job_or_404(jid):
        if not re.fullmatch(r"[a-f0-9]{32}",jid):
            raise HTTPException(404,"Không tìm thấy lượt xử lý.")
        job=store.job(jid)
        if not job:
            raise HTTPException(404,"Không tìm thấy lượt xử lý.")
        return job

    def event_or_404(eid):
        if not re.fullmatch(r"[a-f0-9]{32}",eid):
            raise HTTPException(404,"Không tìm thấy sự kiện.")
        event=store.one("SELECT * FROM events WHERE id=?",(eid,))
        if not event:
            raise HTTPException(404,"Không tìm thấy sự kiện.")
        return event

    def file_response(path, filename=None, media_type=None):
        if not path.resolve().is_relative_to(store.root):
            raise HTTPException(400,"Tệp nằm ngoài thư mục dữ liệu.")
        if not path.is_file():
            raise HTTPException(404,"Tệp chưa sẵn sàng hoặc đã được dọn.")
        return FileResponse(path,filename=filename,media_type=media_type)

    @app.get("/api/health")
    def health():
        disk=shutil.disk_usage(store.root)
        gpu="Không phát hiện GPU NVIDIA"
        try:
            info=subprocess.run(["nvidia-smi","--query-gpu=name,memory.total,memory.used","--format=csv,noheader,nounits"],stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=3,creationflags=NO_WINDOW)
            if info.returncode == 0:
                gpu=info.stdout.strip().splitlines()[0]
        except (OSError,subprocess.TimeoutExpired):
            pass
        return {"status":"ok","version":__version__,"edition":os.environ.get("CURB_EDITION","Local · CPU/CUDA"),"cuda_supported":os.environ.get("CURB_EDITION") != "Desktop · CPU","database":"SQLite · WAL","storage_path":str(store.root),"free_bytes":disk.free,"total_bytes":disk.total,"gpu":gpu,"ffmpeg":bool(shutil.which("ffmpeg")),"models":[{"name":name,"available":(ROOT/name).is_file()} for name in ("yolo26s.pt","yolo26n.pt")],"local_only":True,"worker_capacity":1,"server_time":now()}

    @app.get("/curb.svg", include_in_schema=False)
    def brand_mark():
        return FileResponse(ROOT/"web/dist/curb.svg", media_type="image/svg+xml")

    @app.get("/api/diagnostics")
    def diagnostics():
        status = health()
        keys = ("status", "version", "edition", "cuda_supported", "database", "free_bytes", "ffmpeg", "models", "worker_capacity", "server_time")
        payload = {key: status[key] for key in keys}
        payload["product"] = PRODUCT
        return Response(json.dumps(payload, ensure_ascii=False, indent=2), media_type="application/json", headers={"Content-Disposition": 'attachment; filename="curb-diagnostics.json"'})

    @app.get("/api/settings")
    def settings():
        return store.settings()

    @app.put("/api/settings")
    def save_settings(body: Settings):
        if os.environ.get("CURB_EDITION") == "Desktop · CPU" and body.device == "cuda":
            raise HTTPException(422,"Bản desktop này dùng CPU. Chọn Tự động hoặc CPU.")
        store.execute("UPDATE settings SET value=? WHERE id=1",(body.model_dump_json(),))
        store.audit("settings.updated","settings")
        return body

    @app.get("/api/sources")
    def sources(archived: bool=False):
        return [store.public_source(s) for s in store.all("SELECT * FROM sources WHERE archived=? ORDER BY created_at DESC",(int(archived),))]

    @app.get("/api/sources/{sid}")
    def get_source(sid: str):
        return store.public_source(source_or_404(sid))

    @app.post("/api/sources/upload",status_code=201)
    async def upload(file: UploadFile=File(...),name: str=Form(...,min_length=1,max_length=100),location: str=Form("",max_length=160)):
        suffix=Path(file.filename or "").suffix.lower()
        if suffix not in {".mp4",".mov",".mkv",".avi",".webm",".m4v"}:
            raise HTTPException(422,"Chọn video MP4, MOV, MKV, AVI hoặc WebM.")
        if not name.strip():
            raise HTTPException(422,"Tên nguồn không được để trống.")
        if not operation_lock.acquire(blocking=False):
            raise HTTPException(409,"Đang nhập một video khác. Chờ hoàn tất rồi thử lại.")
        sid=new_id()
        path=store.root/"uploads"/f"{sid}{suffix}"
        size=0
        try:
            limit=min(1024**3,max(0,shutil.disk_usage(store.root).free-350*1024**2))
            with path.open("wb") as target:
                while block:=await file.read(1024*1024):
                    size+=len(block)
                    if size > limit:
                        raise HTTPException(413,"Video vượt 1 GB hoặc ổ lưu trữ không còn đủ 350 MB dự phòng.")
                    target.write(block)
            if size == 0:
                raise HTTPException(422,"Tệp video rỗng.")
            metadata=await run_in_threadpool(probe,str(path),store.root/"sources"/sid/"preview.jpg")
            metadata.update({"bytes":size,"original_name":Path(file.filename).name,"sha256":await run_in_threadpool(sha256,path)})
            source=store.add_source(name.strip(),"video",path,location.strip(),metadata=metadata,source_id=sid)
            return store.public_source(source)
        except ValueError as exc:
            path.unlink(missing_ok=True)
            raise HTTPException(422,str(exc)) from exc
        except Exception:
            path.unlink(missing_ok=True)
            raise
        finally:
            operation_lock.release()
            await file.close()

    @app.post("/api/sources/camera",status_code=201)
    def camera(body: CameraCreate):
        return store.public_source(store.add_source(body.name,"camera",body.url,body.location,body.notes))

    @app.put("/api/sources/{sid}")
    def update_source(sid: str, body: SourceUpdate):
        source=source_or_404(sid)
        metadata={**source["metadata"],"recorded_at":body.recorded_at}
        store.execute("UPDATE sources SET name=?,location=?,notes=?,metadata=?,updated_at=? WHERE id=?",(body.name,body.location,body.notes,json.dumps(metadata),now(),sid))
        store.audit("source.updated",sid)
        return store.public_source(store.source(sid))

    @app.put("/api/sources/{sid}/connection")
    def update_connection(sid: str, body: CameraCreate):
        source=source_or_404(sid)
        if source["kind"] != "camera":
            raise HTTPException(409,"Nguồn này là tệp video.")
        if store.one("SELECT id FROM jobs WHERE source_id=? AND status IN ('queued','running','finalizing','stopping')",(sid,)):
            raise HTTPException(409,"Dừng lượt chạy của camera trước khi đổi kết nối.")
        store.execute("UPDATE sources SET uri=?,name=?,location=?,notes=?,metadata='{}',updated_at=? WHERE id=?",(body.url,body.name,body.location,body.notes,now(),sid))
        (store.root/"sources"/sid/"preview.jpg").unlink(missing_ok=True)
        store.audit("source.connection_updated",sid)
        return store.public_source(store.source(sid))

    @app.post("/api/sources/{sid}/probe")
    async def probe_source(sid: str):
        source=source_or_404(sid)
        try:
            metadata=await run_in_threadpool(probe,source["uri"],store.root/"sources"/sid/"preview.jpg")
        except ValueError as exc:
            raise HTTPException(422,str(exc)) from exc
        metadata={**source["metadata"],**metadata}
        if source["kind"] == "camera":
            metadata["duration"]=None
        store.execute("UPDATE sources SET metadata=?,updated_at=? WHERE id=?",(json.dumps(metadata),now(),sid))
        return store.public_source(store.source(sid))

    @app.get("/api/sources/{sid}/preview")
    def source_preview(sid: str):
        source_or_404(sid)
        return file_response(store.root/"sources"/sid/"preview.jpg",media_type="image/jpeg")

    @app.put("/api/sources/{sid}/zones")
    def set_zones(sid: str,body: ZonesUpdate):
        source_or_404(sid)
        store.execute("UPDATE sources SET zones=?,updated_at=? WHERE id=?",(json.dumps([z.model_dump() for z in body.zones],ensure_ascii=False),now(),sid))
        store.audit("zones.updated",sid,{"count":len(body.zones)})
        return store.public_source(store.source(sid))

    @app.post("/api/sources/{sid}/archive")
    def archive(sid: str,archived: bool=True):
        source_or_404(sid)
        if store.one("SELECT id FROM jobs WHERE source_id=? AND status IN ('queued','running','finalizing','stopping')",(sid,)):
            raise HTTPException(409,"Dừng các lượt xử lý của nguồn trước khi lưu trữ.")
        store.execute("UPDATE sources SET archived=?,updated_at=? WHERE id=?",(int(archived),now(),sid))
        store.audit("source.archived" if archived else "source.restored",sid)
        return {"ok":True}

    @app.post("/api/demo")
    @exclusive_operation
    def demo():
        previous=store.one("SELECT * FROM sources WHERE json_extract(metadata,'$.demo_id')=? ORDER BY created_at LIMIT 1",(DEMO["id"],))
        if previous:
            store.execute("UPDATE sources SET archived=0 WHERE id=?",(previous["id"],))
            return store.public_source(store.source(previous["id"]))
        video=ROOT/"data"/DEMO["filename"]
        if not video.is_file():
            raise HTTPException(404,"Chưa có video mẫu. Chạy scripts/download-demo.ps1 hoặc nhập video của bạn.")
        sid=new_id()
        target=store.root/"uploads"/f"{sid}.mp4"
        shutil.copy2(video,target)
        metadata=probe(target,store.root/"sources"/sid/"preview.jpg")
        metadata.update({**DEMO["metadata"],"bytes":target.stat().st_size,"sha256":sha256(target)})
        return store.public_source(store.add_source(DEMO["name"],"video",target,DEMO["location"],DEMO["notes"],metadata,[DEMO["zone"]],sid))

    @app.get("/api/jobs")
    def jobs(source_id: str="",limit: int=Query(60,ge=1,le=200)):
        if source_id:
            return store.all("SELECT * FROM jobs WHERE source_id=? ORDER BY created_at DESC LIMIT ?",(source_id,limit))
        return store.all("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",(limit,))

    @app.post("/api/jobs",status_code=201)
    @exclusive_operation
    def enqueue(body: JobCreate):
        source=source_or_404(body.source_id)
        settings=store.settings()
        if source["archived"]:
            raise HTTPException(409,"Khôi phục nguồn trước khi chạy.")
        if not any(z.get("enabled",True) for z in source["zones"]):
            raise HTTPException(422,"Vẽ và lưu ít nhất một vùng đang bật trước khi chạy.")
        if not source["metadata"].get("width"):
            raise HTTPException(422,"Kiểm tra kết nối và lấy khung hình trước khi chạy camera.")
        if source["kind"] == "video" and not source["metadata"].get("recorded_at") and any(z.get("enabled",True) and z.get("schedule_enabled") for z in source["zones"]):
            raise HTTPException(422,"Nguồn có quy tắc theo giờ. Nhập mốc bắt đầu ghi hình trong thông tin nguồn trước khi chạy.")
        if not shutil.which("ffmpeg"):
            raise HTTPException(422,"Chưa tìm thấy FFmpeg. Cài FFmpeg và mở lại ứng dụng.")
        if not (ROOT/settings.model).is_file():
            raise HTTPException(422,"Thiếu trọng số mô hình đã chọn. Xem hướng dẫn cài đặt.")
        if shutil.disk_usage(store.root).free < 350*1024**2:
            raise HTTPException(422,"Cần ít nhất 350 MB trống để bắt đầu xử lý.")
        jid,stamp=new_id(),now()
        config={"settings":settings.model_dump(),"zones":source["zones"],"source":store.public_source(source),"max_seconds":body.max_seconds}
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT id FROM jobs WHERE source_id=? AND status IN ('queued','running','finalizing','stopping')",(body.source_id,)).fetchone():
                raise HTTPException(409,"Nguồn đã có một lượt đang chờ hoặc đang chạy.")
            db.execute("INSERT INTO jobs(id,source_id,source_name,status,config,created_at,updated_at) VALUES(?,?,?,'queued',?,?,?)",(jid,body.source_id,source["name"],json.dumps(config,ensure_ascii=False),stamp,stamp))
        store.audit("job.queued",jid,{"source_id":body.source_id})
        return store.job(jid)

    @app.get("/api/jobs/{jid}")
    def job(jid: str):
        return job_or_404(jid)

    @app.post("/api/jobs/{jid}/cancel")
    def cancel(jid: str):
        job_or_404(jid)
        if not manager.cancel(jid):
            raise HTTPException(409,"Lượt xử lý đã kết thúc.")
        store.audit("job.cancel_requested",jid)
        return store.job(jid)

    @app.get("/api/jobs/{jid}/preview")
    def job_preview(jid: str):
        current=job_or_404(jid)
        path=store.root/"jobs"/jid/"preview.jpg"
        if not path.exists():
            path=store.root/"sources"/current["source_id"]/"preview.jpg"
        if not path.is_file():
            raise HTTPException(404,"Chưa có khung hình để hiển thị.")
        return Response(path.read_bytes(),media_type="image/jpeg")

    @app.get("/api/jobs/{jid}/video")
    def job_video(jid: str):
        current=job_or_404(jid)
        if current["status"] in ACTIVE:
            raise HTTPException(409,"Video đang được ghi. Xem khung hình cập nhật trong lúc chờ.")
        return file_response(store.root/"jobs"/jid/"annotated.mp4",media_type="video/mp4")

    def event_filter(status="",source_id="",q="",class_name="",start="",end=""):
        clauses,values=[],[]
        for column,value in (("status",status),("source_id",source_id),("class_name",class_name)):
            if value:
                clauses.append(f"{column}=?")
                values.append(value)
        if q:
            clauses.append("(source_name LIKE ? OR zone_name LIKE ? OR id LIKE ?)")
            values.extend([f"%{q}%"]*3)
        for raw,operator in ((start,">="),(end,"<=")):
            if raw:
                try:
                    date.fromisoformat(raw)
                except ValueError:
                    raise HTTPException(422,"Ngày lọc phải có dạng YYYY-MM-DD.")
                clauses.append(f"date(created_at,'localtime'){operator}?")
                values.append(raw)
        return (" WHERE "+" AND ".join(clauses) if clauses else ""),values

    @app.get("/api/events")
    def events(status: str="",source_id: str="",job_id: str="",q: str="",class_name: str="",start: str="",end: str="",page: int=Query(1,ge=1),page_size: int=Query(20,ge=1,le=100)):
        where,values=event_filter(status,source_id,q,class_name,start,end)
        if job_id:
            where+=(" AND " if where else " WHERE ")+"job_id=?"
            values.append(job_id)
        total=store.one("SELECT COUNT(*) AS n FROM events"+where,values)["n"]
        rows=store.all("SELECT * FROM events"+where+" ORDER BY created_at DESC LIMIT ? OFFSET ?",(*values,page_size,(page-1)*page_size))
        return {"items":rows,"total":total,"page":page,"page_size":page_size}

    @app.get("/api/events/{eid}")
    def event_detail(eid: str):
        event=event_or_404(eid)
        event["reviews"]=store.all("SELECT * FROM reviews WHERE event_id=? ORDER BY id DESC",(eid,))
        event["job"]=job_or_404(event["job_id"])
        return event

    @app.post("/api/events/{eid}/review")
    def review(eid: str,body: Review):
        if body.status in {"confirmed","dismissed","resolved"} and not body.note.strip():
            raise HTTPException(422,"Ghi lý do xử lý để lưu cùng hồ sơ.")
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            event=db.execute("SELECT version FROM events WHERE id=?",(eid,)).fetchone()
            if not event:
                raise HTTPException(404,"Không tìm thấy sự kiện.")
            if event["version"] != body.version:
                raise HTTPException(409,"Hồ sơ vừa được cập nhật. Tải lại trước khi ghi quyết định.")
            stamp=now()
            db.execute("UPDATE events SET status=?,version=version+1,updated_at=? WHERE id=?",(body.status,stamp,eid))
            db.execute("INSERT INTO reviews(event_id,status,note,operator,created_at) VALUES(?,?,?,?,?)",(eid,body.status,body.note,store.settings().operator_name,stamp))
        return event_detail(eid)

    @app.get("/api/events/{eid}/media/{kind}")
    def event_media(eid: str,kind: str,download: bool=False):
        event=event_or_404(eid)
        if kind not in {"snapshot","clip","thumbnail"}:
            raise HTTPException(404,"Loại bằng chứng không tồn tại.")
        if kind == "clip" and not event["payload"].get("clip_ready"):
            raise HTTPException(409,"Đang hoàn tất video bằng chứng.")
        base=(store.root/"jobs"/event["job_id"]).resolve()
        path=(base/event["payload"].get(kind,event["payload"]["snapshot"])).resolve()
        if not path.is_relative_to(base):
            raise HTTPException(400,"Đường dẫn bằng chứng không hợp lệ.")
        return file_response(path,f"curb-{eid[:8]}{path.suffix}" if download else None,"video/mp4" if kind == "clip" else "image/jpeg")

    @app.get("/api/overview")
    def overview():
        counts={row["status"]:row["n"] for row in store.all("SELECT status,COUNT(*) n FROM events GROUP BY status")}
        return {"sources":store.one("SELECT COUNT(*) n FROM sources WHERE archived=0")["n"],"active_jobs":store.one("SELECT COUNT(*) n FROM jobs WHERE status IN ('running','finalizing','stopping')")["n"],"queued_jobs":store.one("SELECT COUNT(*) n FROM jobs WHERE status='queued'")["n"],"events":sum(counts.values()),"pending":counts.get("pending",0),"confirmed":counts.get("confirmed",0),"resolved":counts.get("resolved",0),"dismissed":counts.get("dismissed",0),"reviewed":sum(v for k,v in counts.items() if k != "pending"),"processed_hours":round(store.one("SELECT COALESCE(SUM(source_seconds),0) n FROM jobs")["n"]/3600,3),"recent_events":store.all("SELECT * FROM events WHERE status='pending' ORDER BY created_at DESC LIMIT 5")}

    @app.get("/api/reports")
    def reports(start: str="",end: str="",source_id: str=""):
        where,values=event_filter(source_id=source_id,start=start,end=end)
        return {"by_status":store.all("SELECT status label,COUNT(*) value FROM events"+where+" GROUP BY status",values),"by_class":store.all("SELECT class_name label,COUNT(*) value FROM events"+where+" GROUP BY class_name",values),"by_source":store.all("SELECT source_name label,COUNT(*) value FROM events"+where+" GROUP BY source_name ORDER BY value DESC",values),"daily":store.all("SELECT date(created_at,'localtime') label,COUNT(*) value FROM events"+where+" GROUP BY label ORDER BY label",values),"total":store.one("SELECT COUNT(*) n FROM events"+where,values)["n"],"period_basis":"Ngày tạo hồ sơ trên máy này; không phải ngày ghi hình gốc."}

    @app.get("/api/export/events")
    def export_events(format: str="csv",status: str="",source_id: str="",q: str="",class_name: str="",start: str="",end: str=""):
        where,values=event_filter(status,source_id,q,class_name,start,end)
        rows=store.all("SELECT * FROM events"+where+" ORDER BY created_at DESC",values)
        if format == "json":
            for row in rows:
                row["reviews"]=store.all("SELECT * FROM reviews WHERE event_id=? ORDER BY id",(row["id"],))
            return Response(json.dumps({"exported_at":now(),"events":rows},ensure_ascii=False,indent=2),media_type="application/json",headers={"Content-Disposition":"attachment; filename=curb-events.json"})
        if format != "csv":
            raise HTTPException(422,"Chọn CSV hoặc JSON.")
        output=io.StringIO(newline="")
        writer=csv.writer(output)
        writer.writerow(["id","nguon","vung","loai_xe","trang_thai","bat_dau_dung_s","canh_bao_s","thoi_gian_dung_s","tao_luc","nguoi_duyet","ghi_chu"])
        def safe(value):
            text=str(value if value is not None else "")
            return "'"+text if text[:1] in {"=","+","-","@","\t","\r","\n"} else text
        for row in rows:
            last=store.one("SELECT * FROM reviews WHERE event_id=? ORDER BY id DESC LIMIT 1",(row["id"],)) or {}
            p=row["payload"]
            writer.writerow([safe(v) for v in (row["id"],row["source_name"],row["zone_name"],row["class_name"],row["status"],p["stop_start_s"],p["alert_time_s"],p["dwell_s"],row["created_at"],last.get("operator",""),last.get("note",""))])
        return Response("\ufeff"+output.getvalue(),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":"attachment; filename=curb-events.csv"})

    def temporary_zip(prefix):
        descriptor,name=tempfile.mkstemp(prefix=prefix,suffix=".zip",dir=store.root/"backups")
        os.close(descriptor)
        return Path(name)

    def check_export_space(paths):
        required=sum(path.stat().st_size for path in paths)+50*1024**2
        if shutil.disk_usage(store.root).free < required:
            raise HTTPException(422,f"Cần khoảng {round(required/1024**2)} MB trống để tạo gói xuất. Dọn hoặc chuyển thư mục dữ liệu trước khi thử lại.")

    @app.get("/api/jobs/{jid}/export")
    def export_job(jid: str):
        current=job_or_404(jid)
        if current["status"] in ACTIVE:
            raise HTTPException(409,"Chờ lượt xử lý kết thúc trước khi xuất hồ sơ.")
        directory=store.root/"jobs"/jid
        check_export_space([p for p in directory.rglob("*") if p.is_file()])
        target=temporary_zip("evidence-")
        with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
            archive.writestr("job.json",json.dumps(current,ensure_ascii=False,indent=2))
            credit=current["config"]["source"].get("metadata",{})
            if credit.get("attribution"):
                archive.writestr("SOURCE-LICENSE.txt","\n".join(str(credit.get(key,"")) for key in ("attribution","source_url","license_url","modifications"))+"\nCurb overlays: vehicle boxes, track IDs, configured zone and stop timer.\n")
            records=store.all("SELECT * FROM events WHERE job_id=?",(jid,))
            for event in records:
                event["reviews"]=store.all("SELECT * FROM reviews WHERE event_id=? ORDER BY id",(event["id"],))
            archive.writestr("events.json",json.dumps(records,ensure_ascii=False,indent=2))
            if directory.exists():
                for path in directory.rglob("*"):
                    if path.is_file() and path.suffix in {".json",".jpg",".mp4"}:
                        archive.write(path,str(path.relative_to(directory)))
        return FileResponse(target,filename=f"curb-evidence-{jid[:8]}.zip",background=BackgroundTask(target.unlink,missing_ok=True))

    @app.get("/api/storage")
    def storage():
        cutoff=(datetime.now(timezone.utc)-timedelta(days=store.settings().retention_days)).isoformat()
        candidates=store.all("SELECT id,source_name,status,created_at,event_count FROM jobs WHERE created_at<? AND status NOT IN ('queued','running','stopping','finalizing') ORDER BY created_at",(cutoff,))
        total=0
        for job in candidates:
            directory=store.root/"jobs"/job["id"]
            job["bytes"]=sum(p.stat().st_size for p in directory.rglob("*") if p.is_file()) if directory.exists() else 0
            total+=job["bytes"]
        return {"candidates":candidates,"reclaimable_bytes":total,"retention_days":store.settings().retention_days,"free_bytes":shutil.disk_usage(store.root).free}

    @app.post("/api/storage/purge")
    @exclusive_operation
    def purge(body: PurgeRequest):
        allowed={row["id"] for row in storage()["candidates"]}
        if not set(body.job_ids) <= allowed:
            raise HTTPException(409,"Chỉ được dọn các lượt đã kết thúc và hết thời hạn lưu trữ. Tải lại danh sách.")
        base=(store.root/"jobs").resolve()
        targets=[(base/jid).resolve() for jid in body.job_ids]
        if any(not p.is_relative_to(base) or p == base for p in targets):
            raise HTTPException(400,"Thư mục dọn dữ liệu không hợp lệ.")
        for jid,path in zip(body.job_ids,targets):
            if path.exists():
                shutil.rmtree(path)
            store.execute("DELETE FROM jobs WHERE id=?",(jid,))
            store.audit("job.purged",jid)
        return {"deleted":len(targets)}

    @app.get("/api/audit")
    def audit():
        return store.all("SELECT * FROM audit ORDER BY id DESC LIMIT 100")

    @app.get("/api/backup")
    @exclusive_operation
    def backup():
        if store.one("SELECT id FROM jobs WHERE status IN ('running','queued','finalizing','stopping')"):
            raise HTTPException(409,"Dừng hoặc chờ tất cả lượt xử lý trước khi sao lưu.")
        check_export_space([p for folder in ("uploads","sources","jobs") for p in (store.root/folder).rglob("*") if p.is_file()]+[store.path])
        target=temporary_zip("backup-")
        db_copy=target.with_suffix(".sqlite3")
        try:
            with store.connect() as original, closing(sqlite3.connect(db_copy)) as copy:
                original.backup(copy)
                copy.execute("PRAGMA secure_delete=ON")
                for sid,kind,uri in copy.execute("SELECT id,kind,uri FROM sources").fetchall():
                    copy.execute("UPDATE sources SET uri=? WHERE id=?",(f"uploads/{Path(uri).name}" if kind == "video" else "",sid))
                copy.commit()
                copy.execute("VACUUM")
            with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=1) as archive:
                archive.write(db_copy,"curb.sqlite3")
                archive.writestr("README.txt","Curb backup v1. Camera connection addresses are intentionally omitted. Restore to a NEW folder using python -m curb.backup ARCHIVE --destination NEW_FOLDER. Re-enter camera connections after restore.")
                for folder in ("uploads","sources","jobs"):
                    for path in (store.root/folder).rglob("*"):
                        if path.is_file() and path.suffix.lower() in {".mp4",".webm",".avi",".mov",".mkv",".m4v",".jpg",".json"}:
                            archive.write(path,str(path.relative_to(store.root)))
        except Exception:
            target.unlink(missing_ok=True)
            raise
        finally:
            db_copy.unlink(missing_ok=True)
        return FileResponse(target,filename=f"curb-backup-{date.today()}.zip",background=BackgroundTask(target.unlink,missing_ok=True))

    dist=ROOT/"web"/"dist"
    if (dist/"assets").is_dir():
        app.mount("/assets",StaticFiles(directory=dist/"assets"),name="assets")

    @app.get("/")
    def index():
        if (dist/"index.html").is_file():
            return FileResponse(dist/"index.html",headers={"Cache-Control":"no-cache"})
        return JSONResponse({"detail":"Chưa build giao diện. Chạy npm --prefix web ci và npm --prefix web run build."},status_code=503)

    return app
