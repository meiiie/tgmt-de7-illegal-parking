"""Kernel v5: (A) SAM 3.1 tren 1 cua so AIC ngan, dump track tung frame, so sanh khong-stitch vs stitch(IoU+DINOv3) de kiem tra gia thuyet
'ID doi o ranh gioi chunk -> 0 canh bao'; (B) YOLO26s+ByteTrack (+DINOv3) tren ca 9 video AIC21 nhu bang v2 (F1 0.471). 1 file JSON."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {f: open(f"{ROOT}/src/{f}").read() for f in ("pipeline.py", "evaluate.py")}
ZON = open(f"{ROOT}/configs/zones_aic_full.json").read()
cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s})
md("# Đề 7 — v5: chẩn đoán SAM 3.1 (dump track + nối ID qua chunk) và baseline đủ 9 video AIC21\nKết quả gộp: out/de7_v5_results.json")
code("import os, glob, json, subprocess, zipfile, shutil, time, random, csv\nT_START=time.time(); os.chdir('/kaggle/working'); os.makedirs('src', exist_ok=True); os.makedirs('configs', exist_ok=True); os.makedirs('out', exist_ok=True)\n"
     + "".join(f"open('src/{f}','w').write({s!r})\n" for f, s in SRC.items())
     + f"open('configs/zones_aic_full.json','w').write({ZON!r})\n")
code("""!pip -q install gdown "git+https://github.com/facebookresearch/sam3.git@7f473cf" ultralytics lap "transformers>=4.56" einops decord pycocotools 2>&1 | tail -1
WDIR = os.path.dirname(glob.glob('/kaggle/input/**/sam31_sha256.txt', recursive=True)[0])
os.makedirs('weights', exist_ok=True); SAM3_CKPT='weights/sam3.1_multiplex.pt'
if not os.path.exists(SAM3_CKPT): subprocess.run(f'cat {WDIR}/sam31_part_* > {SAM3_CKPT}', shell=True, check=True)
r='dinov3-vits16-pretrain-lvd1689m'; os.makedirs(f'weights/{r}', exist_ok=True)
for f in glob.glob(f'{WDIR}/{r}__*'):
    dst=f'weights/{r}/'+os.path.basename(f).split('__',1)[1]
    if not os.path.exists(dst): os.symlink(f,dst)
DINO=f'weights/{r}'
import torch; print(torch.__version__, torch.cuda.get_device_name(0))""")
code("""Z='/tmp/aic21.zip'
if not os.path.exists(Z): subprocess.run(f'gdown --fuzzy "https://drive.google.com/file/d/1gsR4pIEiWK7htPmIjiZjXetaa1X-T-Am/view" -O {Z}', shell=True)
zf = zipfile.ZipFile(Z); names = zf.namelist()
gtf = [n for n in names if n.endswith('train-anomaly-results.txt')][0]
rows = [l.split() for l in zf.read(gtf).decode().splitlines() if len(l.split()) >= 3 and l.split()[0].isdigit()]
vids = {n.split('/')[-1]: n for n in names if n.endswith('.mp4') and 'train' in n.lower()}
# cung tap 9 video nhu v2 (make_nb_aic.py): 6 duong tinh dau + 3 am tinh random.seed(0)
pos = sorted({int(r[0]) for r in rows}); neg = [i for i in range(1, 101) if i not in pos and f'{i}.mp4' in vids]
random.seed(0); sel_pos = pos[:6]; sel_neg = random.sample(neg, 3); SEL = sel_pos + sel_neg; print('SEL', SEL)
os.makedirs('aic', exist_ok=True)
for i in SEL:
    with zf.open(vids[f'{i}.mp4']) as s, open(f'aic/{i}.mp4','wb') as d: shutil.copyfileobj(s, d)
GT = [{'video': f'{int(r[0])}.mp4', 'zone': 'all', 'stop_start_s': float(r[1]), 'stop_end_s': float(r[2])} for r in rows if int(r[0]) in SEL]
json.dump(GT, open('aic/gt.json','w'), indent=1); print(GT); os.remove(Z)""")
code("""os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
import cv2
BUDGET_S = float(os.environ.get('BUDGET_S', '6300'))
RES = {'settings': {'gpu': torch.cuda.get_device_name(0), 'videos': SEL, 'gt': GT}, 'sam_diag': {}, 'aic9': {}}
def save(): json.dump(RES, open('out/de7_v5_results.json','w'), indent=1)
def run(cmd, tmo):
    try: r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=tmo); return r
    except subprocess.TimeoutExpired: return None
def track_stats(p):
    R = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    if not R: return {'rows': 0}
    fr = sorted({int(x['frame']) for x in R})
    return {'rows': len(R), 'frames_with_dets': len(fr), 'raw_ids': len({x['raw_id'] for x in R}), 'ids': len({x['id'] for x in R}),
            'still_rows': sum(x['still'] == '1' for x in R), 'max_dwell_s': max(float(x['dwell']) for x in R),
            'mean_dets_per_frame': round(len(R) / max(len(fr), 1), 2)}
# ---- A) SAM 3.1: video 35 (su co 106-185 s), 240 s dau, 1 fps, chunk 60; khong stitch vs stitch IoU+DINOv3 ----
V = 35; fps = cv2.VideoCapture(f'aic/{V}.mp4').get(cv2.CAP_PROP_FPS) or 30
SAMA = (f'--video aic/{V}.mp4 --stride {round(fps)} --max_frames {int(240*fps)} --max_side 640 --zones configs/zones_aic_full.json '
        f'--backend sam3 --sam3_ckpt {SAM3_CKPT} --amp fp16 --prompt car --offload_video --chunk_frames 60 --max_objects 8 --det_batch 1 --dump_tracks')
RES['settings']['sam'] = SAMA
r = run(f'python src/pipeline.py {SAMA} --sanity 5 --out out/sanity', 900)
RES['sanity'] = [l for l in (r.stdout if r else '').splitlines() if l.startswith('SANITY')] or (r.stderr[-1500:] if r else 'timeout'); save(); print(RES['sanity'])
gt35 = [g for g in GT if g['video'] == f'{V}.mp4' and g['stop_start_s'] < 220]
for g in gt35: g['stop_end_s'] = min(g['stop_end_s'], 240)
json.dump(gt35, open('out/gt35.json','w'))
for name, extra in [('sam31_nostitch', ''), ('sam31_stitch_dino', f'--stitch --reid {DINO}')]:
    left = BUDGET_S - (time.time() - T_START)
    if left < 300: print('BUDGET HIT', name); continue
    r = run(f'python src/pipeline.py {SAMA} {extra} --out out/{name}', min(left - 60, 2400))
    m = json.load(open(f'out/{name}/metrics.json')) if os.path.exists(f'out/{name}/metrics.json') else {'error': (r.stderr[-1500:] if r else 'timeout')}
    ev = json.loads(subprocess.run(f'python src/evaluate.py out/gt35.json out/{name}/alerts.json 30 --dedup_iou 0.3', shell=True, capture_output=True, text=True).stdout or '{}') if 'error' not in m else {}
    RES['sam_diag'][name] = {'metrics': m, 'eval_dedup0.3': ev, 'tracks': track_stats(f'out/{name}/tracks.csv')}; save()
    print(name, json.dumps(RES['sam_diag'][name]), flush=True)
shutil.rmtree('weights', ignore_errors=True)""")
code("""# ---- B) 9 video AIC21, 2 fps (stride 15), ca khung hinh, dwell 20 s, nhu v2; eval tho va dedup IoU 0.3 ----
CFG = {'yolo26s_bytetrack': '--backend yolo --model yolo26s.pt', 'yolo26s_bytetrack_dino': f'--backend yolo --model yolo26s.pt --reid {DINO}'}
if not os.path.exists(DINO + '/config.json'):   # weights da xoa o tren -> tao lai symlink DINOv3
    os.makedirs(DINO, exist_ok=True)
    for f in glob.glob(f'{WDIR}/dinov3-vits16-pretrain-lvd1689m__*'): os.symlink(f, f'{DINO}/' + os.path.basename(f).split('__',1)[1])
for name, args in CFG.items():
    ms, al = [], []
    for i in SEL:
        left = BUDGET_S - (time.time() - T_START)
        if left < 120: print('BUDGET HIT', name, i); continue
        r = run(f'python src/pipeline.py --video aic/{i}.mp4 --zones configs/zones_aic_full.json --stride 15 --out out/{name}/{i} {args}', left)
        if os.path.exists(f'out/{name}/{i}/metrics.json'): ms.append(json.load(open(f'out/{name}/{i}/metrics.json'))); al += json.load(open(f'out/{name}/{i}/alerts.json'))
        else: print(name, i, (r.stderr[-800:] if r else 'timeout'))
    done = [os.path.basename(m['video']) for m in ms]; os.makedirs(f'out/{name}', exist_ok=True)
    json.dump(al, open(f'out/{name}/all_alerts.json','w')); json.dump([g for g in GT if g['video'] in done], open(f'out/{name}/gt.json','w'))
    ev = {k: json.loads(subprocess.run(f'python src/evaluate.py out/{name}/gt.json out/{name}/all_alerts.json 30 {a}', shell=True, capture_output=True, text=True).stdout or '{}')
          for k, a in [('raw', ''), ('dedup0.3', '--dedup_iou 0.3')]}
    nf = sum(m['frames_processed'] for m in ms)
    RES['aic9'][name] = {'videos_done': done, 'frames': nf,
        'fps_model': round(nf / max(sum(m['frames_processed'] / max(m['fps_model'], 1e-9) for m in ms), 1e-9), 2) if ms else None,
        'fps_e2e': round(nf / max(sum(m['wall_s'] for m in ms), 1e-9), 2) if ms else None,
        'vram_peak_mb': max(((m['vram_peak_mb'] or 0) for m in ms), default=None), 'eval': ev}
    save(); print(name, json.dumps(RES['aic9'][name]), flush=True)
RES['total_wall_s'] = round(time.time() - T_START); save()
shutil.rmtree('aic', ignore_errors=True); shutil.rmtree('out/sanity', ignore_errors=True)
for p in glob.glob('out/**/evidence/*.mp4', recursive=True): os.remove(p)
print(open('out/de7_v5_results.json').read()[:5000])""")
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}}, "nbformat": 4, "nbformat_minor": 5}
os.makedirs(f"{ROOT}/kaggle/kernel_v5", exist_ok=True)
json.dump(nb, open(f"{ROOT}/kaggle/kernel_v5/de7_v5_diag_aic9.ipynb", "w"), indent=1, ensure_ascii=False)
json.dump({"id": "holilihu/de7-v5-diag-aic9", "title": "de7-v5-diag-aic9", "code_file": "de7_v5_diag_aic9.ipynb", "language": "python", "kernel_type": "notebook",
           "is_private": True, "enable_gpu": True, "enable_internet": True, "dataset_sources": ["holilihu/de7-weights"],
           "competition_sources": [], "kernel_sources": []}, open(f"{ROOT}/kaggle/kernel_v5/kernel-metadata.json", "w"), indent=1)
