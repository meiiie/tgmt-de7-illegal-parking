"""Run Curb on a declared AI City train subset; score with the legacy local protocol."""
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from curb.media import sha256
from curb.models import Settings, Zone
from curb.store import Store, new_id, now
from curb.worker import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--window", type=int, default=240)
    parser.add_argument("--sample-fps", type=float, default=1)
    parser.add_argument("--device", choices=["cuda","cpu"], default="cuda")
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    selected = [2,9,11,14,33,35,58,62,7]
    labels = []
    for line in (args.train / "train-anomaly-results.txt").read_text().splitlines():
        pieces = line.split()
        if len(pieces) >= 3 and pieces[0].isdigit():
            video, start, end = int(pieces[0]),float(pieces[1]),float(pieces[2])
            if video in selected and start < args.window:
                labels.append({"video":f"{video}.mp4","zone":"all","stop_start_s":start,"stop_end_s":min(end,args.window)})
    settings = Settings(device=args.device,confidence=.25,sample_fps=args.sample_fps,image_size=640,still_window=3,movement_tolerance=.1,lost_grace=4,minimum_area=200,save_annotated=False)
    zone = Zone(id="all",name="all",polygon=[[0,0],[1,0],[1,1],[0,1]],dwell_seconds=20,severity="watch",suppress_congestion=True)
    store = Store(args.out / "data")
    rows, predictions = [], []
    specification = importlib.util.spec_from_file_location("legacy_evaluate",ROOT / "src/evaluate.py")
    evaluator = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(evaluator)
    started = time.perf_counter()
    report = {"dataset":"AI City Challenge 2021 Track 4 TRAIN subset","split":"development; these video IDs were previously used to select settings","selected_video_ids":selected,"window_seconds":args.window,"settings":settings.model_dump(),"zones":[zone.model_dump()],"evaluation_protocol":"src/evaluate.py legacy local temporal matching, tolerance=30 s; NOT official AI City scoring","ground_truth":labels,"ground_truth_file_sha256":sha256(args.train / "train-anomaly-results.txt"),"runs":rows}
    for number in selected:
        path = args.train / f"{number}.mp4"
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            raise RuntimeError(f"Cannot decode {path.name}")
        fps, count = cap.get(cv2.CAP_PROP_FPS),int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        metadata = {"fps":fps,"frames":count,"duration":count/fps,"width":int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),"height":int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),"sha256":sha256(path)}
        cap.release()
        source = store.add_source(path.name,"video",path,metadata=metadata,zones=[zone.model_dump()])
        jid, stamp = new_id(),now()
        config = {"settings":settings.model_dump(),"zones":source["zones"],"source":store.public_source(source),"max_seconds":args.window}
        store.execute("INSERT INTO jobs(id,source_id,source_name,status,config,created_at,updated_at) VALUES(?,?,?,'queued',?,?,?)",(jid,source["id"],source["name"],json.dumps(config),stamp,stamp))
        print(json.dumps({"video":path.name,"phase":"started","source_fps":fps}),flush=True)
        run(store,jid)
        job = store.job(jid)
        events = store.all("SELECT payload FROM events WHERE job_id=?",(jid,))
        current = [{**event["payload"],"video":path.name,"zone":"all"} for event in events]
        predictions.extend(current)
        rows.append({"video":path.name,"source":metadata,"job_id":jid,"metrics":job["metrics"],"score":evaluator.score([g for g in labels if g["video"] == path.name],current,30)})
        report.update({"aggregate_score":evaluator.score(labels,predictions,30),"predictions":predictions,"elapsed_seconds":round(time.perf_counter()-started,3)})
        (args.out / "report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        print(json.dumps(rows[-1]),flush=True)
    manifest = json.loads((store.root / "jobs" / rows[0]["job_id"] / "manifest.json").read_text(encoding="utf-8"))
    report["environment"] = {key:manifest[key] for key in ("git_commit","python","packages","device","precision","seed","model_sha256","code_sha256")}
    frames = sum(row["metrics"]["frames"] for row in rows)
    wall = sum(row["metrics"]["wall_seconds"] for row in rows)
    report["aggregate_performance"] = {"processed_frames":frames,"sum_worker_wall_seconds":round(wall,3),"sampled_frames_per_second":round(frames/wall,3)}
    (args.out / "report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"finished":True,"score":report["aggregate_score"],"performance":report["aggregate_performance"]}),flush=True)


if __name__ == "__main__":
    main()
