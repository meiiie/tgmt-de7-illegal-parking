import json
cells=[]
def md(s): cells.append({"cell_type":"markdown","metadata":{},"source":s})
def code(s): cells.append({"cell_type":"code","metadata":{},"execution_count":None,"outputs":[],"source":s})
md("# Đề 7 — Đánh giá mức sự kiện trên AI City Challenge 2021 Track 4 (Traffic Anomaly: crash/stalled vehicle)\nNguồn dữ liệu: https://www.aicitychallenge.org/2021-track4-download/ (tải công khai). Baseline YOLO26s+ByteTrack vs SAM 3.1 (+DINOv3).")
code("""import os, glob, json, subprocess, zipfile, shutil, random
os.chdir('/kaggle/working')
!pip -q install gdown "git+https://github.com/facebookresearch/sam3.git@7f473cf" ultralytics lap "transformers>=4.56" einops decord pycocotools 2>&1 | tail -1
_c = glob.glob('/kaggle/input/**/src/pipeline.py', recursive=True); CODE = os.path.dirname(os.path.dirname(_c[0]))
for d in ['src','configs']:
    if not os.path.exists(d): shutil.copytree(f'{CODE}/{d}', d)
WDIR = os.path.dirname(glob.glob('/kaggle/input/**/sam31_sha256.txt', recursive=True)[0])
os.makedirs('weights', exist_ok=True); SAM3_CKPT='weights/sam3.1_multiplex.pt'
if not os.path.exists(SAM3_CKPT): subprocess.run(f'cat {WDIR}/sam31_part_* > {SAM3_CKPT}', shell=True, check=True)
r='dinov3-vits16-pretrain-lvd1689m'; os.makedirs(f'weights/{r}', exist_ok=True)
for f in glob.glob(f'{WDIR}/{r}__*'):
    dst=f'weights/{r}/'+os.path.basename(f).split('__',1)[1]
    if not os.path.exists(dst): os.symlink(f,dst)
DINO=f'weights/{r}'
!df -h /tmp /kaggle/working | cat""")
code("""Z='/tmp/aic21.zip'
if not os.path.exists(Z): subprocess.run(f'gdown --fuzzy "https://drive.google.com/file/d/1gsR4pIEiWK7htPmIjiZjXetaa1X-T-Am/view" -O {Z}', shell=True)
zf = zipfile.ZipFile(Z); names = zf.namelist(); print(len(names)); print([n for n in names if not n.endswith('.mp4')][:40]); print(names[:10])""")
code("""gtf = [n for n in names if n.endswith('train-anomaly-results.txt')]; print(gtf)
gt_lines = zf.read(gtf[0]).decode().split(); print(gt_lines[:30])
rows = [l.split() for l in zf.read(gtf[0]).decode().splitlines() if len(l.split()) >= 3 and l.split()[0].isdigit()]
vids = {n.split('/')[-1]: n for n in names if n.endswith('.mp4') and 'train' in n.lower()}
print(len(vids), list(vids)[:5])
pos = sorted({int(r[0]) for r in rows}); neg = [i for i in range(1, 101) if i not in pos and f'{i}.mp4' in vids]
random.seed(0); sel_pos = pos[:6]; sel_neg = random.sample(neg, 3); SEL = sel_pos + sel_neg; print('pos', sel_pos, 'neg', sel_neg)
os.makedirs('aic', exist_ok=True)
for i in SEL:
    with zf.open(vids[f'{i}.mp4']) as s, open(f'aic/{i}.mp4','wb') as d: shutil.copyfileobj(s, d)
GT = [{'video': f'{int(r[0])}.mp4', 'zone': 'all', 'stop_start_s': float(r[1]), 'stop_end_s': float(r[2])} for r in rows if int(r[0]) in SEL]
json.dump(GT, open('aic/gt.json','w'), indent=1); print(GT)
import cv2; os.makedirs('out/thumbs', exist_ok=True)
for i in SEL:  # anh khung hinh de ve ROI lan/le offline
    c = cv2.VideoCapture(f'aic/{i}.mp4'); c.set(1, 300); ok, f = c.read()
    if ok: cv2.imwrite(f'out/thumbs/{i}.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 85])""")
code("""os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
STRIDE=15  # 30 fps -> 2 fps
CFG={'yolo26s_bytetrack': '--backend yolo --model yolo26s.pt',
     'yolo26s_bytetrack_dino': f'--backend yolo --model yolo26s.pt --reid {DINO}',
     'sam31_dino': f'--backend sam3 --sam3_ckpt {SAM3_CKPT} --amp bf16 --offload_video --chunk_frames 150 --max_objects 8 --det_batch 1 --reid {DINO}'}
import time
T0=time.time(); BUDGET_S=float(os.environ.get('BUDGET_S','6000'))   # ~100 phut, duoi tran 2h
SAM_SEL = sel_pos[:3] + sel_neg[:1]
# 1) bang FPS/VRAM tren Gaithersburg (ngan) cho SAM 3.1 va SAM 3.1+DINOv3
for name,args in [('g_sam31', CFG['sam31_dino'].replace(f' --reid {DINO}','')), ('g_sam31_dino', CFG['sam31_dino'])]:
    cmd=f'python src/pipeline.py --video {CODE}/data/gaithersburg_480p.webm --zones configs/zones_gaithersburg.json --stride 3 --out out/{name} {args}'
    r=subprocess.run(cmd,shell=True,capture_output=True,text=True)
    print(name, [l[:400] for l in r.stdout.splitlines() if l.startswith(('METRICS','SAM3'))] or '\\n'.join([l for l in r.stderr.splitlines() if 'sam3/' in l or 'Error' in l][-8:]), flush=True)
# 2) AIC21: baseline tren ca 9 video, SAM tren 4 video (gioi han thoi gian)
RUN_BASELINE = False  # baseline da co ket qua (v2, results/aic21_table.csv)
for name,args in CFG.items():
    if name.startswith('yolo') and not RUN_BASELINE: continue
    vids_run = SAM_SEL if name.startswith('sam') else SEL
    for i in vids_run:
        if time.time()-T0 > BUDGET_S: print('BUDGET HIT, skip', name, i); continue
        cmd=f'python src/pipeline.py --video aic/{i}.mp4 --zones configs/zones_aic_full.json --stride {STRIDE} --out out/{name}/{i} {args}'
        r=subprocess.run(cmd,shell=True,capture_output=True,text=True)
        print(name, i, [l[:300] for l in r.stdout.splitlines() if l.startswith('METRICS')] or r.stderr[-600:], flush=True)
    al=[]; [al.extend(json.load(open(p))) for p in glob.glob(f'out/{name}/*/alerts.json')]
    json.dump(al, open(f'out/{name}/all_alerts.json','w'))
    done=[int(os.path.basename(os.path.dirname(p))) for p in glob.glob(f'out/{name}/*/metrics.json')]
    json.dump([g for g in GT if int(g['video'].split('.')[0]) in done], open(f'out/{name}/gt_subset.json','w'))
    print(name, 'EVAL', subprocess.run(f'python src/evaluate.py out/{name}/gt_subset.json out/{name}/all_alerts.json 30', shell=True, capture_output=True, text=True).stdout, flush=True)
""")
code("""import csv
rows=[]
for name in CFG:
    ms=[json.load(open(p)) for p in glob.glob(f'out/{name}/*/metrics.json')]
    ev=json.loads(subprocess.run(f'python src/evaluate.py out/{name}/gt_subset.json out/{name}/all_alerts.json 30', shell=True, capture_output=True, text=True).stdout or '{}')
    if ms: rows.append({'config':name,'videos':len(ms),'frames':sum(m['frames_processed'] for m in ms),'fps_model':round(sum(m['frames_processed'] for m in ms)/sum(m['frames_processed']/max(m['fps_model'],1e-9) for m in ms),2),
                 'fps_e2e':round(sum(m['frames_processed'] for m in ms)/sum(m['wall_s'] for m in ms),2),'vram_peak_mb':max((m['vram_peak_mb'] or 0) for m in ms),**ev})
with open('out/aic_table.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys()) if rows else ['config']); w.writeheader(); [w.writerow(r) for r in rows]
print(open('out/aic_table.csv').read()); shutil.rmtree('aic', ignore_errors=True)""")
nb={"cells":cells,"metadata":{"kernelspec":{"name":"python3","display_name":"Python 3"}},"nbformat":4,"nbformat_minor":5}
json.dump(nb,open("notebooks/de7_aic21_eval.ipynb","w"),indent=1,ensure_ascii=False)
