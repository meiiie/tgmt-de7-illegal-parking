import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from curb.api import DEMO, create_app
from curb.backup import restore
from curb.store import now
from curb.instance import InstanceLock


ZONE={"id":"street","name":"Lề đường","polygon":[[0,0],[1,0],[1,1],[0,1]],"dwell_seconds":5}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="curb-test-")
        self.root=Path(self.temp.name)
        self.model_root=self.root/"model-fixture"
        self.model_root.mkdir()
        (self.model_root/"yolo26s.pt").write_bytes(b"unit-test-presence-only")
        self.root_patch=patch("curb.api.ROOT",self.model_root)
        self.ffmpeg_patch=patch("curb.api.shutil.which",return_value="ffmpeg")
        self.root_patch.start()
        self.ffmpeg_patch.start()
        self.app=create_app(self.root/"data",start_worker=False)
        self.client=TestClient(self.app)
        self.store=self.app.state.store
        fixture=self.store.root/"uploads/test.mp4"
        fixture.write_bytes(b"unit-test-fixture")
        self.source=self.store.add_source("Đoạn đường A","video",fixture,metadata={"width":100,"height":100,"duration":10},zones=[ZONE])

    def tearDown(self):
        self.client.close()
        self.ffmpeg_patch.stop()
        self.root_patch.stop()
        self.temp.cleanup()

    def job(self):
        response=self.client.post("/api/jobs",json={"source_id":self.source["id"]})
        self.assertEqual(response.status_code,201,response.text)
        return response.json()

    def event(self):
        job=self.job()
        return self.store.add_event(job,{"zone_name":"Lề đường","zone_id":"street","class_name":"car","severity":"restricted","stop_start_s":0,"alert_time_s":5,"dwell_s":5,"snapshot":"evidence/x.jpg","clip":"evidence/x.mp4","bbox":[0,0,20,20]})

    def test_source_secrets_never_returned(self):
        body={"name":"Camera","url":"rtsp://operator:unit-test-secret@localhost:8554/live"}
        response=self.client.post("/api/sources/camera",json=body)
        self.assertEqual(response.status_code,201)
        self.assertNotIn("unit-test-secret",response.text)
        self.assertNotIn("rtsp",self.client.get("/api/sources").text)

    def test_desktop_cpu_capability(self):
        with patch.dict("os.environ", {"CURB_EDITION": "Desktop · CPU"}):
            health = self.client.get("/api/health").json()
            self.assertEqual(health["edition"], "Desktop · CPU")
            self.assertFalse(health["cuda_supported"])
            settings = self.client.get("/api/settings").json()
            settings["device"] = "cuda"
            self.assertEqual(self.client.put("/api/settings", json=settings).status_code, 422)
            settings["device"] = "cpu"
            self.assertEqual(self.client.put("/api/settings", json=settings).status_code, 200)

    def test_diagnostics_excludes_operational_and_personal_data(self):
        self.client.post("/api/sources/camera",json={"name":"Private camera","url":"rtsp://operator:unit-test-secret@localhost:8554/live"})
        response=self.client.get("/api/diagnostics")
        self.assertEqual(response.status_code,200)
        self.assertIn("attachment",response.headers["content-disposition"])
        for forbidden in ("unit-test-secret","Private camera",str(self.store.root),"operator_name","storage_path"):
            self.assertNotIn(forbidden,response.text)
        self.assertEqual(response.json()["product"]["version"],self.client.get("/api/health").json()["version"])

    def test_new_demo_preserves_legacy_and_restores_only_current_version(self):
        self.store.execute("UPDATE sources SET metadata=? WHERE id=?", (json.dumps({"demo": True}), self.source["id"]))
        media = self.model_root / "data" / DEMO["filename"]
        media.parent.mkdir()
        media.write_bytes(b"demo-probe-fixture")
        with patch("curb.api.probe", return_value={"width":1280,"height":720,"fps":5,"duration":30}):
            response = self.client.post("/api/demo")
        self.assertEqual(response.status_code, 200, response.text)
        demo = response.json()
        self.assertNotEqual(demo["id"], self.source["id"])
        self.assertEqual(demo["metadata"]["demo_id"], DEMO["id"])
        self.assertEqual(demo["zones"][0]["dwell_seconds"], 20)
        self.client.post(f"/api/sources/{demo['id']}/archive")
        restored = self.client.post("/api/demo").json()
        self.assertEqual(restored["id"], demo["id"])
        self.assertFalse(restored["archived"])
        self.assertEqual(len(self.client.get("/api/sources").json()), 2)
        self.assertEqual(self.store.source(self.source["id"])["metadata"], {"demo":True})
        job = self.client.post("/api/jobs", json={"source_id":demo["id"]}).json()
        self.client.post(f"/api/jobs/{job['id']}/cancel")
        exported = self.client.get(f"/api/jobs/{job['id']}/export")
        self.assertEqual(exported.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(exported.content)) as archive:
            credit = archive.read("SOURCE-LICENSE.txt").decode("utf-8")
            self.assertIn("MERL", credit)
            self.assertIn("https://creativecommons.org/licenses/by-sa/4.0/", credit)

    def test_queue_duplicate_cancel_archive(self):
        job=self.job()
        self.assertEqual(self.client.post("/api/jobs",json={"source_id":self.source["id"]}).status_code,409)
        self.assertEqual(self.client.post(f"/api/sources/{self.source['id']}/archive").status_code,409)
        self.assertEqual(self.client.post(f"/api/jobs/{job['id']}/cancel").json()["status"],"cancelled")
        self.assertEqual(self.client.post(f"/api/sources/{self.source['id']}/archive").status_code,200)
        self.assertEqual(self.client.get("/api/sources").json(),[])
        self.assertEqual(len(self.client.get("/api/sources?archived=true").json()),1)

    def test_zone_validation_and_snapshot(self):
        job=self.job()
        new={**ZONE,"dwell_seconds":60}
        self.assertEqual(self.client.put(f"/api/sources/{self.source['id']}/zones",json={"zones":[new]}).status_code,200)
        self.assertEqual(self.store.job(job["id"])["config"]["zones"][0]["dwell_seconds"],5)
        invalid={**ZONE,"polygon":[[0,0],[1,1],[0,1],[1,0]]}
        self.assertEqual(self.client.put(f"/api/sources/{self.source['id']}/zones",json={"zones":[invalid]}).status_code,422)

    def test_review_audit_conflict_and_export(self):
        event=self.event()
        url=f"/api/events/{event['id']}/review"
        self.assertEqual(self.client.post(url,json={"status":"dismissed","version":0}).status_code,422)
        response=self.client.post(url,json={"status":"dismissed","note":"Xe chờ đèn đỏ","version":0})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()["reviews"][0]["note"],"Xe chờ đèn đỏ")
        self.assertEqual(self.client.post(url,json={"status":"confirmed","note":"test","version":0}).status_code,409)
        self.assertEqual(self.client.get("/api/events?status=pending").json()["total"],0)
        self.assertIn("Xe chờ đèn đỏ",self.client.get("/api/export/events").text)
        self.assertEqual(self.client.get("/api/reports").json()["total"],1)

    def test_origin_host_and_missing_media(self):
        self.assertEqual(self.client.post("/api/demo",headers={"origin":"https://untrusted.example"}).status_code,403)
        self.assertEqual(self.client.get("/api/sources",headers={"host":"untrusted.example"}).status_code,400)
        self.assertEqual(self.client.get("/api/events/missing/media/snapshot").status_code,404)
        self.assertEqual(self.client.get("/api/events?start=bad").status_code,422)

    def test_upload_invalid_rolls_back(self):
        with patch("curb.api.probe",side_effect=ValueError("Video không hợp lệ")):
            response=self.client.post("/api/sources/upload",data={"name":"test"},files={"file":("bad.mp4",b"not a video","video/mp4")})
        self.assertEqual(response.status_code,422)
        self.assertEqual([p.name for p in (self.store.root/"uploads").iterdir()],["test.mp4"])

    def test_backup_restore_and_omitted_credentials(self):
        self.client.post("/api/sources/camera",json={"name":"Camera","url":"rtsp://user:unique-camera-password@localhost/live"})
        result=self.client.get("/api/backup")
        self.assertEqual(result.status_code,200)
        with zipfile.ZipFile(io.BytesIO(result.content)) as archive:
            self.assertNotIn(b"unique-camera-password",archive.read("curb.sqlite3"))
        backup=self.root/"backup.zip"
        backup.write_bytes(result.content)
        target=restore(backup,self.root/"restored")
        restored=create_app(target,start_worker=False).state.store
        self.assertEqual(len(restored.all("SELECT * FROM sources")),2)
        self.assertEqual(restored.one("SELECT uri FROM sources WHERE kind='camera'")["uri"],"")
        with self.assertRaises(ValueError):
            restore(backup,target)

    def test_restore_rejects_traversal(self):
        backup=self.root/"bad.zip"
        with zipfile.ZipFile(backup,"w") as archive:
            archive.writestr("curb.sqlite3",b"")
            archive.writestr("../outside.txt",b"no")
        with self.assertRaises(ValueError):
            restore(backup,self.root/"destination")
        self.assertFalse((self.root/"outside.txt").exists())

    def test_restart_recovers_active_job(self):
        job=self.job()
        self.store.update_job(job["id"],status="running")
        self.app.state.manager.start()
        self.app.state.manager.close()
        self.assertEqual(self.store.job(job["id"])["status"],"interrupted")

    def test_purge_rejects_active_and_recent_jobs(self):
        job=self.job()
        response=self.client.post("/api/storage/purge",json={"job_ids":[job["id"]]})
        self.assertEqual(response.status_code,409)
        self.assertIsNotNone(self.store.job(job["id"]))

    def test_schedule_rejects_video_without_timestamp(self):
        self.client.put(f"/api/sources/{self.source['id']}/zones",json={"zones":[{**ZONE,"schedule_enabled":True}]})
        self.assertEqual(self.client.post("/api/jobs",json={"source_id":self.source["id"]}).status_code,422)
        self.client.put(f"/api/sources/{self.source['id']}",json={"name":"Đoạn đường A","recorded_at":"2026-11-08T10:00"})
        self.assertEqual(self.client.post("/api/jobs",json={"source_id":self.source["id"]}).status_code,201)

    def test_data_directory_single_instance(self):
        lock=InstanceLock(self.root/"locked")
        try:
            with self.assertRaises(RuntimeError):
                InstanceLock(self.root/"locked")
        finally:
            lock.close()
        second=InstanceLock(self.root/"locked")
        second.close()

    def test_job_filter_and_zero_csv_time(self):
        event=self.event()
        record=self.store.one("SELECT job_id FROM events WHERE id=?",(event["id"],))
        self.assertEqual(self.client.get("/api/events?job_id="+record["job_id"]).json()["total"],1)
        self.assertEqual(self.client.get("/api/events?job_id=missing").json()["total"],0)
        self.assertIn(",pending,0,5,5,",self.client.get("/api/export/events").text)

    def test_missing_runtime_prerequisites_are_reported(self):
        with patch("curb.api.shutil.which",return_value=None):
            self.assertEqual(self.client.post("/api/jobs",json={"source_id":self.source["id"]}).status_code,422)
        (self.model_root/"yolo26s.pt").unlink()
        self.assertEqual(self.client.post("/api/jobs",json={"source_id":self.source["id"]}).status_code,422)


if __name__ == "__main__":
    unittest.main()
