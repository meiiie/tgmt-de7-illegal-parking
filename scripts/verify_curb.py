"""Run real local inference and API workflows; never substitutes for camera accuracy evaluation."""
import argparse
import io
import json
import re
import subprocess
import threading
import time
import zipfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import cv2
import httpx


ROOT=Path(__file__).resolve().parents[1]
ZONE={"id":"test-road","name":"Kiểm thử · xe chờ đèn","polygon":[[.132,.43],[.235,.43],[.235,.62],[.132,.62]],"dwell_seconds":5,"enabled":True,"severity":"watch","classes":["car","motorcycle","bus","truck"],"suppress_congestion":True}


class ReplayCamera:
    def __init__(self, video):
        cap=cv2.VideoCapture(str(video))
        frames=[]
        index=0
        while True:
            ok,frame=cap.read()
            if not ok:
                break
            if index%4 == 0:
                frames.append(cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,80])[1].tobytes())
            index+=1
        cap.release()
        self.running=True
        owner=self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type","multipart/x-mixed-replace; boundary=frame")
                self.end_headers()
                i=0
                try:
                    while owner.running:
                        frame=frames[i%len(frames)]
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "+str(len(frame)).encode()+b"\r\n\r\n"+frame+b"\r\n")
                        self.wfile.flush()
                        i+=1
                        time.sleep(.125)
                except (ConnectionError,OSError):
                    pass

            def log_message(self,*args):
                pass

        self.server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.url=f"http://127.0.0.1:{self.server.server_port}/live"

    def close(self):
        self.running=False
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--base-url",default="http://127.0.0.1:8765")
    parser.add_argument("--report",type=Path,default=ROOT/"outputs/rebuild-2026-11-08/verification.json")
    args=parser.parse_args()
    client=httpx.Client(base_url=args.base_url,trust_env=False,timeout=40)
    report={"created_at":datetime.now(timezone.utc).isoformat(),"kind":"local integration and real inference; HTTP camera is a replay fixture, not a physical RTSP camera","checks":[],"jobs":[]}
    created_sources=[]
    camera=None

    def check(name,passed,details=None):
        report["checks"].append({"name":name,"passed":bool(passed),"details":details})
        print(json.dumps({"check":name,"passed":bool(passed)},ensure_ascii=False),flush=True)
        if not passed:
            raise AssertionError(name)

    def ok(response,expected=200):
        if response.status_code != expected:
            raise AssertionError(f"HTTP {response.status_code}: {response.text[:300]}")
        return response.json()

    def wait(jid,predicate=None,timeout=160):
        deadline=time.monotonic()+timeout
        last=None
        while time.monotonic()<deadline:
            job=ok(client.get(f"/api/jobs/{jid}"))
            if job["status"] != last:
                print(json.dumps({"job":jid[:8],"status":job["status"],"frames":job["frames"]}),flush=True)
                last=job["status"]
            if predicate and predicate(job):
                return job
            if job["status"] not in {"queued","running","finalizing","stopping"}:
                return job
            time.sleep(.5)
        raise TimeoutError("Job did not reach expected state")

    try:
        front=client.get("/")
        check("frontend_served",front.status_code==200)
        assets=re.findall(r'(?:src|href)="(/assets/[^\"]+)"',front.text)
        check("frontend_assets_served",len(assets)>=2 and all(client.get(path).status_code==200 for path in assets),assets)
        video=ROOT/"data/gaithersburg_20s.mp4"
        with video.open("rb") as stream:
            source=ok(client.post("/api/sources/upload",data={"name":"[Kiểm thử] Video đường phố","location":"Gaithersburg · video CC BY 4.0"},files={"file":(video.name,stream,"video/mp4")}),201)
        created_sources.append(source["id"])
        check("upload_validated",source["metadata"]["width"]==854 and source["has_preview"])
        ok(client.put(f"/api/sources/{source['id']}/zones",json={"zones":[ZONE]}))
        start=time.perf_counter()
        job=ok(client.post("/api/jobs",json={"source_id":source["id"]}),201)
        check("duplicate_job_rejected",client.post("/api/jobs",json={"source_id":source["id"]}).status_code==409)
        job=wait(job["id"])
        job["observed_request_to_complete_s"]=round(time.perf_counter()-start,3)
        report["jobs"].append(job)
        check("real_video_complete",job["status"]=="completed" and job["frames"]==100 and job["event_count"]>=1,job["metrics"])
        events=ok(client.get("/api/events",params={"job_id":job["id"]}))["items"]
        event=events[0]
        check("event_time",4.9 <= event["payload"]["alert_time_s"] <= 5.3,event["payload"])
        for kind in ("snapshot","thumbnail","clip"):
            response=client.get(f"/api/events/{event['id']}/media/{kind}")
            check(f"evidence_{kind}",response.status_code==200 and len(response.content)>1000,{"bytes":len(response.content)})
        response=client.get(f"/api/events/{event['id']}/media/clip",headers={"Range":"bytes=0-127"})
        check("video_range_playback",response.status_code==206 and len(response.content)==128)
        data_path=Path(ok(client.get("/api/health"))["storage_path"])
        for name,path in (("annotated",data_path/"jobs"/job["id"]/"annotated.mp4"),("clip",data_path/"jobs"/job["id"]/event["payload"]["clip"])):
            result=subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=codec_name,pix_fmt,nb_frames,duration,width,height","-of","json",str(path)],capture_output=True,text=True,check=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            info=json.loads(result.stdout)["streams"][0]
            decoded=cv2.VideoCapture(str(path))
            frame_count=0
            while decoded.read()[0]:
                frame_count+=1
            decoded.release()
            check(f"{name}_decoded",info["codec_name"]=="h264" and frame_count==int(info["nb_frames"]),{**info,"decoded_frames":frame_count})
        review=ok(client.post(f"/api/events/{event['id']}/review",json={"status":"dismissed","note":"Kiểm thử vận hành: xe trong video mẫu đang chờ đèn đỏ, không dùng làm bằng chứng vi phạm.","version":event["version"]}))
        check("review_persisted",review["status"]=="dismissed" and len(review["reviews"])==1)
        check("stale_review_rejected",client.post(f"/api/events/{event['id']}/review",json={"status":"pending","version":event["version"]}).status_code==409)
        csv_response=client.get("/api/export/events",params={"source_id":source["id"]})
        check("filtered_csv_export",csv_response.status_code==200 and "Kiểm thử vận hành" in csv_response.text)
        response=client.get(f"/api/jobs/{job['id']}/export")
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            check("evidence_zip",all(name in archive.namelist() for name in ("manifest.json","metrics.json","events.json","annotated.mp4")),{"entries":len(archive.namelist())})
        invalid=client.post("/api/sources/upload",data={"name":"Video lỗi"},files={"file":("broken.mp4",b"invalid","video/mp4")})
        check("corrupt_video_rejected",invalid.status_code==422)
        camera=ReplayCamera(video)
        camera_source=ok(client.post("/api/sources/camera",json={"name":"[Kiểm thử] Camera HTTP phát lại","url":camera.url}),201)
        created_sources.append(camera_source["id"])
        camera_source=ok(client.post(f"/api/sources/{camera_source['id']}/probe"))
        check("camera_probe",camera_source["metadata"]["width"]==854)
        ok(client.put(f"/api/sources/{camera_source['id']}/zones",json={"zones":[ZONE]}))
        camera_job=ok(client.post("/api/jobs",json={"source_id":camera_source["id"],"max_seconds":10}),201)
        camera_job=wait(camera_job["id"])
        report["jobs"].append(camera_job)
        check("camera_processing",camera_job["status"]=="completed" and camera_job["frames"]>20,camera_job["metrics"])
        camera_events=ok(client.get("/api/events",params={"job_id":camera_job["id"]}))["items"]
        check("camera_event_created",len(camera_events)>0)
        for event in camera_events:
            path=data_path/"jobs"/camera_job["id"]/event["payload"]["clip"]
            result=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)],capture_output=True,text=True,check=True,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
            clip_seconds=float(json.loads(result.stdout)["format"]["duration"])
            clock_seconds=event["payload"]["clip_end_s"]-event["payload"]["clip_start_s"]
            check("camera_clip_clock_preserved",abs(clip_seconds-clock_seconds)<=.25,{"encoded_seconds":clip_seconds,"source_clock_seconds":clock_seconds})
        cancel_job=ok(client.post("/api/jobs",json={"source_id":camera_source["id"]}),201)
        wait(cancel_job["id"],lambda current:current["frames"]>=5)
        ok(client.post(f"/api/jobs/{cancel_job['id']}/cancel"))
        cancelled=wait(cancel_job["id"])
        report["jobs"].append(cancelled)
        check("running_camera_cancelled",cancelled["status"]=="cancelled" and cancelled["frames"]>=5)
        lost_job=ok(client.post("/api/jobs",json={"source_id":camera_source["id"]}),201)
        wait(lost_job["id"],lambda current:current["frames"]>=5)
        camera.close()
        camera=None
        lost=wait(lost_job["id"],timeout=75)
        report["jobs"].append(lost)
        check("camera_disconnect_reported",lost["status"]=="failed" and bool(lost["error"]),{"error":lost["error"]})
        backup=client.get("/api/backup",timeout=60)
        with zipfile.ZipFile(io.BytesIO(backup.content)) as archive:
            check("full_backup_download",backup.status_code==200 and "curb.sqlite3" in archive.namelist(),{"bytes":len(backup.content),"entries":len(archive.namelist())})
        report["passed"]=True
    except Exception as exc:
        report["passed"]=False
        report["failure"]=f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if camera:
            camera.close()
        for sid in created_sources:
            client.post(f"/api/sources/{sid}/archive")
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        client.close()


if __name__ == "__main__":
    main()
