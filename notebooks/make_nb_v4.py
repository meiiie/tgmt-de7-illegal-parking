"""Sinh kernel v4: SAM 3.1 tren T4 (fp16, prompt 'car', gioi han frame/do phan giai, sanity 5 frame, <=2h, 1 file JSON).
Code src/ duoc nhung truc tiep vao notebook (khong can cap nhat dataset de7-code); weights doc tu dataset de7-weights."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {f: open(f"{ROOT}/src/{f}").read() for f in ("pipeline.py", "evaluate.py")}
ZON = open(f"{ROOT}/configs/zones_aic_full.json").read()
cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s})
md("# Đề 7 — v4: SAM 3.1 trên T4 (fp16) — AIC21 Track 4, cùng eval với baseline\n"
   "Giới hạn: 1 fps (stride 30), 240 s đầu mỗi video, cạnh dài 640 px, chunk 60 frame, det_batch 1, max_objects 8. "
   "Sanity 5 frame với prompt 'car' (thử lại 16 frame vì SAM 3.1 có độ trễ khởi động track), 0 box → dừng. Tổng ≤ 2 h (ngân sách 100 phút cho SAM). "
   "Baseline YOLO26s+ByteTrack (± DINOv3) chạy lại trên đúng cửa sổ này để so sánh công bằng. Kết quả gộp: out/de7_v4_results.json")
code("import os, glob, json, subprocess, zipfile, shutil, time\nT_START=time.time(); os.chdir('/kaggle/working'); os.makedirs('src', exist_ok=True); os.makedirs('configs', exist_ok=True)\n"
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
SEL = [9, 33, 35, 7]          # 3 video co su co trong 240 s dau + 1 video am tinh (cung tap v2/v3)
WIN_S = 240                   # chi danh gia 240 s dau
os.makedirs('aic', exist_ok=True)
for i in SEL:
    with zf.open(vids[f'{i}.mp4']) as s, open(f'aic/{i}.mp4','wb') as d: shutil.copyfileobj(s, d)
GT = [{'video': f'{int(r[0])}.mp4', 'zone': 'all', 'stop_start_s': float(r[1]), 'stop_end_s': min(float(r[2]), WIN_S)}
      for r in rows if int(r[0]) in SEL and float(r[1]) < WIN_S - 20]   # su co phai bat dau truoc (cua so - dwell 20 s)
json.dump(GT, open('aic/gt_win.json','w'), indent=1); print(GT); os.remove(Z)""")
code("""os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True'
import cv2
FPS_SRC = {i: cv2.VideoCapture(f'aic/{i}.mp4').get(cv2.CAP_PROP_FPS) or 30 for i in SEL}
COMMON = '--max_side 640 --zones configs/zones_aic_full.json'
SAM = f'--backend sam3 --sam3_ckpt {SAM3_CKPT} --amp fp16 --prompt car --offload_video --chunk_frames 60 --max_objects 8 --det_batch 1'
CFG = {'sam31_fp16': SAM,   # uu tien SAM 3.1 truoc; baseline re -> sau; SAM+DINOv3 cuoi (bi bo neu het ngan sach)
       'yolo26s_bytetrack': '--backend yolo --model yolo26s.pt --half',
       'yolo26s_bytetrack_dino': f'--backend yolo --model yolo26s.pt --half --reid {DINO}',
       'sam31_fp16_dino': f'{SAM} --reid {DINO}'}
def args_for(i):
    st = max(1, round(FPS_SRC[i]))          # ~1 fps
    return f'--video aic/{i}.mp4 --stride {st} --max_frames {int(WIN_S * FPS_SRC[i])} {COMMON}'
RES = {'settings': {'gpu': torch.cuda.get_device_name(0), 'amp': 'fp16', 'prompt': 'car', 'sample_fps': 1, 'window_s': WIN_S, 'max_side': 640,
                    'chunk_frames': 60, 'det_batch': 1, 'max_objects': 8, 'dwell_s': 20, 'match_tol_s': 30, 'videos': SEL, 'gt': GT}, 'sanity': [], 'runs': {}}
def save(): json.dump(RES, open('out/de7_v4_results.json','w'), indent=1)
os.makedirs('out', exist_ok=True)
# ---- sanity: 5 frame, prompt 'car'; 0 box -> thu 16 frame (tre khoi dong track) -> van 0 thi dung han ----
SAM_OK = False
for n in (5, 16):
    r = subprocess.run(f'python src/pipeline.py {args_for(SEL[0])} {SAM} --sanity {n} --out out/sanity', shell=True, capture_output=True, text=True)
    line = [l for l in r.stdout.splitlines() if l.startswith('SANITY')]
    RES['sanity'].append(json.loads(line[0][7:]) if line else {'frames': n, 'error': r.stderr[-1500:]}); save(); print(RES['sanity'][-1], flush=True)
    if r.returncode == 0: SAM_OK = True; break
    if not line: break   # loi that (OOM/import) -> khong thu lai
if not SAM_OK: print('SANITY FAILED: SAM 3.1 ra 0 box / loi -> bo qua SAM, chi chay baseline')""")
code("""BUDGET_S = float(os.environ.get('BUDGET_S', '6000'))   # tong ~100 phut tinh tu dau kernel, chua toi tran 2 h
for name, extra in CFG.items():
    if name.startswith('sam') and not SAM_OK: continue
    ms, al = [], []
    for i in SEL:
        left = BUDGET_S - (time.time() - T_START)
        if left < 120: print('BUDGET HIT, skip', name, i); continue
        try:
            r = subprocess.run(f'python src/pipeline.py {args_for(i)} {extra} --out out/{name}/{i}', shell=True, capture_output=True, text=True, timeout=left)
        except subprocess.TimeoutExpired: print('TIMEOUT', name, i); continue
        mj = f'out/{name}/{i}/metrics.json'
        if os.path.exists(mj): ms.append(json.load(open(mj))); al += json.load(open(f'out/{name}/{i}/alerts.json'))
        else: print(name, i, r.stderr[-800:])
        print(name, i, ms[-1] if ms and ms[-1]['video'].endswith(f'/{i}.mp4') else 'FAIL', flush=True)
    done = [os.path.basename(m['video']) for m in ms]
    json.dump(al, open(f'out/{name}/all_alerts.json','w')); json.dump([g for g in GT if g['video'] in done], open(f'out/{name}/gt.json','w'))
    ev = json.loads(subprocess.run(f'python src/evaluate.py out/{name}/gt.json out/{name}/all_alerts.json 30 --dedup_iou 0.3', shell=True, capture_output=True, text=True).stdout or '{}')
    nf = sum(m['frames_processed'] for m in ms)
    RES['runs'][name] = {'videos_done': done, 'frames': nf,
        'fps_model': round(nf / max(sum(m['frames_processed'] / max(m['fps_model'], 1e-9) for m in ms), 1e-9), 3) if ms else None,
        'fps_e2e': round(nf / max(sum(m['wall_s'] for m in ms), 1e-9), 3) if ms else None,
        'vram_peak_mb': max(((m['vram_peak_mb'] or 0) for m in ms), default=None), 'eval_dedup0.3': ev, 'per_video': ms}
    save(); print(name, json.dumps({k: v for k, v in RES['runs'][name].items() if k != 'per_video'}), flush=True)
RES['total_wall_s'] = round(time.time() - T_START); save()
shutil.rmtree('aic', ignore_errors=True); shutil.rmtree('weights', ignore_errors=True); shutil.rmtree('out/sanity', ignore_errors=True)
print(open('out/de7_v4_results.json').read()[:4000])""")
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}}, "nbformat": 4, "nbformat_minor": 5}
os.makedirs(f"{ROOT}/kaggle/kernel_v4", exist_ok=True)
json.dump(nb, open(f"{ROOT}/kaggle/kernel_v4/de7_sam31_v4.ipynb", "w"), indent=1, ensure_ascii=False)
json.dump({"id": "holilihu/de7-sam31-v4", "title": "de7-sam31-v4", "code_file": "de7_sam31_v4.ipynb", "language": "python", "kernel_type": "notebook",
           "is_private": True, "enable_gpu": True, "enable_internet": True, "dataset_sources": ["holilihu/de7-weights"],
           "competition_sources": [], "kernel_sources": []}, open(f"{ROOT}/kaggle/kernel_v4/kernel-metadata.json", "w"), indent=1)
