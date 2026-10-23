"""Danh gia muc su kien: GT json [{"video","zone","stop_start_s","stop_end_s"}]; pred = alerts.json.
TP neu cung video+zone va alert_time nam trong [stop_start, stop_end + tol]. Bao cao P/R/F1, MAE stop_start (dwell error), do tre canh bao."""
import json, sys, numpy as np
gt, pr = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])); tol = float(sys.argv[3]) if len(sys.argv) > 3 else 5
used, tp, errs, lat = set(), 0, [], []
for p in sorted(pr, key=lambda e: e["alert_time_s"]):
    for i, g in enumerate(gt):
        if i in used or g["video"] != p["video"] or g["zone"] != p["zone"]: continue
        if g["stop_start_s"] <= p["alert_time_s"] <= g["stop_end_s"] + tol:
            used.add(i); tp += 1; errs.append(abs(p["stop_start_s"] - g["stop_start_s"])); lat.append(p["alert_time_s"] - g["stop_start_s"]); break
P = tp / max(len(pr), 1); R = tp / max(len(gt), 1)
print(json.dumps({"tp": tp, "fp": len(pr) - tp, "fn": len(gt) - tp, "precision": round(P, 3), "recall": round(R, 3),
                  "f1": round(2*P*R/max(P+R, 1e-9), 3), "start_mae_s": round(float(np.mean(errs)), 2) if errs else None,
                  "mean_alert_latency_s": round(float(np.mean(lat)), 2) if lat else None}))
