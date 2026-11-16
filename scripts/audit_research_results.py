"""Check stored research counts and provenance without rerunning inference."""
import argparse
import ast
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--live-report", type=Path)
    parser.add_argument("--public-output", type=Path)
    args = parser.parse_args()
    table = ROOT / "results/aic21_table.csv"
    with table.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    checks = []
    for row in rows:
        tp, fp, fn = (int(row[name]) for name in ("tp", "fp", "fn"))
        precision, recall = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
        expected = {"precision":precision,"recall":recall,"f1":2 * tp / max(2 * tp + fp + fn, 1)}
        for name, value in expected.items():
            assert abs(float(row[name]) - value) <= .00051, (row["config"], name)
        checks.append({"configuration":row["config"],"tp":tp,"fp":fp,"fn":fn,"metrics_match_counts":True})
    v5 = json.loads((ROOT / "results/de7_v5_results.json").read_text(encoding="utf-8"))
    by_name = {r["config"]:r for r in rows}
    for name, value in v5["aic9"].items():
        row = by_name[f"v5_{name}_aic9_2fps"]
        for metric, number in value["eval"]["raw"].items():
            assert abs(float(row[metric]) - number) <= .00051, (name, metric)
    notebook = ROOT / "kaggle/kernel_v5/de7_v5_diag_aic9.ipynb"
    embedded = {}
    for cell in json.loads(notebook.read_text(encoding="utf-8"))["cells"]:
        if cell["cell_type"] != "code":
            continue
        try:
            tree = ast.parse("".join(cell["source"]))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "write" and node.args):
                continue
            value = node.args[0]
            if isinstance(value, ast.Constant) and isinstance(value.value, str) and "class Reid:" in value.value:
                embedded["pipeline_sha256"] = hashlib.sha256(value.value.encode()).hexdigest()
                embedded["argument_defaults"] = [line.strip() for line in value.value.splitlines() if "ap.add_argument" in line and any(flag in line for flag in ("--imgsz", "--conf", "--half", "--tracker", "--reid_thr", "--min_area", "--stride", "--max_frames"))]
    files = [table, notebook, ROOT / "configs/zones_aic_full.json", ROOT / "src/pipeline.py", ROOT / "src/evaluate.py", ROOT / "results/de7_v4_results.json", ROOT / "results/de7_v5_results.json", ROOT / "results/de7_v6_results.json"]
    report = {"audited_utc":datetime.now(timezone.utc).isoformat(),"source_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"activity":"stored artifact arithmetic and source inspection only; no new AI City inference or official rescoring", "checks":checks,"v5_json_csv_match":True,"v5_settings":v5["settings"],"v5_embedded_source":embedded,"sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    if args.public_output:
        public = {"review_date":"2026-11-14","source_commit":report["source_commit"],"historical_activity":report["activity"],"historical_rows":rows,"historical_arithmetic_checks":checks,"v5_json_csv_match":True,"artifact_sha256":report["sha256"],"v5_embedded_source":embedded}
        if args.live_report:
            live = json.loads(args.live_report.read_text(encoding="utf-8"))
            public["live_trial"] = {key:live[key] for key in ("source","started_utc","finished_utc","requested_seconds","transport","status","metrics","bridge_frames_produced","first_frame_sha256","harness_sha256","accuracy_evaluation","camera_to_alert_latency_measured")}
            public["live_trial"].update({"settings":live["configuration"]["settings"],"zones":live["configuration"]["zones"],"model_sha256":live["manifest"]["model_sha256"],"code_sha256":{key.replace(chr(92),"/"):value for key,value in live["manifest"]["code_sha256"].items()},"python":live["manifest"]["python"].split()[0],"packages":live["manifest"]["packages"],"seed":live["manifest"]["seed"],"camera_clock_visual_observation":{"first_frame":"2026-11-14 12:30:05","last_worker_preview":"2026-11-14 12:30:29","progress_seconds":24,"method":"visual reading of provider timestamp; not synchronized with an independently verified camera clock"}})
            live_log = args.live_report.parent.parent / (args.live_report.parent.name + ".log")
            public["live_trial"]["read_timeout_warning_count"] = live_log.read_text(encoding="utf-8").count("Stream timeout triggered")
        args.public_output.parent.mkdir(parents=True,exist_ok=True)
        args.public_output.write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"rows_checked":len(checks),"v5_json_csv_match":True,"new_ai_city_inference":False}))


if __name__ == "__main__":
    main()
