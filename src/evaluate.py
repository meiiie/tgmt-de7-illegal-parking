"""Danh gia muc su kien.
GT json [{"video","zone","stop_start_s","stop_end_s"}]; pred = alerts.json cua pipeline.
--dedup_iou: gop cac canh bao cung video co bbox IoU >= nguong (cung mot xe/su co dung yen, ID bi doi) -> giu canh bao som nhat.
--min_area: bo canh bao co bbox nho hon (px^2) (xe qua xa).
TP neu cung video+zone va alert_time trong [stop_start, stop_end + tol]. Bao cao P/R/F1, MAE thoi diem bat dau dung, do tre canh bao."""
import argparse, json, numpy as np

def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    u = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - i
    return i / u if u > 0 else 0

def filter_alerts(pr, dedup_iou=0.0, min_area=0):
    pr = [p for p in pr if (p["bbox"][2]-p["bbox"][0]) * (p["bbox"][3]-p["bbox"][1]) >= min_area]
    if dedup_iou <= 0: return pr
    keep = []
    for p in sorted(pr, key=lambda e: e["alert_time_s"]):
        if not any(k["video"] == p["video"] and iou(k["bbox"], p["bbox"]) >= dedup_iou for k in keep): keep.append(p)
    return keep

def score(gt, pr, tol=30.0):
    used, tp, errs, lat = set(), 0, [], []
    for p in sorted(pr, key=lambda e: e["alert_time_s"]):
        for i, g in enumerate(gt):
            if i in used or g["video"] != p["video"] or g["zone"] != p["zone"]: continue
            if g["stop_start_s"] <= p["alert_time_s"] <= g["stop_end_s"] + tol:
                used.add(i); tp += 1; errs.append(abs(p["stop_start_s"] - g["stop_start_s"])); lat.append(p["alert_time_s"] - g["stop_start_s"]); break
    P = tp / max(len(pr), 1); R = tp / max(len(gt), 1)
    return {"tp": tp, "fp": len(pr) - tp, "fn": len(gt) - tp, "precision": round(P, 3), "recall": round(R, 3),
            "f1": round(2*P*R/max(P+R, 1e-9), 3), "start_mae_s": round(float(np.mean(errs)), 2) if errs else None,
            "mean_alert_latency_s": round(float(np.mean(lat)), 2) if lat else None}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("gt"); ap.add_argument("pred"); ap.add_argument("tol", nargs="?", type=float, default=30)
    ap.add_argument("--dedup_iou", type=float, default=0.0); ap.add_argument("--min_area", type=float, default=0)
    a = ap.parse_args()
    gt, pr = json.load(open(a.gt)), json.load(open(a.pred))
    print(json.dumps(score(gt, filter_alerts(pr, a.dedup_iou, a.min_area), a.tol)))
