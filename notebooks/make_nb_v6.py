"""Kernel v6 (SAM 3.1 box prompt). Template from v5: (A) SAM 3.1 tren 1 cua so AIC ngan, dump track tung frame, so sanh khong-stitch vs stitch(IoU+DINOv3) de kiem tra gia thuyet
'ID doi o ranh gioi chunk -> 0 canh bao'; (B) YOLO26s+ByteTrack (+DINOv3) tren ca 9 video AIC21 nhu bang v2 (F1 0.471). 1 file JSON."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = {f: open(f"{ROOT}/src/{f}").read() for f in ("pipeline.py", "evaluate.py")}
ZON = open(f"{ROOT}/configs/zones_aic_full.json").read()
cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s})
md("# Đề 7 — v6: SAM 3.1 với prompt box YOLO26s + text, 800 px, 32 đối tượng\nKết quả gộp: out/de7_v6_results.json")
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
BUDGET_S = float(os.environ.get('BUDGET_S', '6000'))
RES = {'settings': {'gpu': torch.cuda.get_device_name(0), 'videos': SEL, 'gt': GT}, 'sam_diag': {}, 'win9': {}}
def save(): json.dump(RES, open('out/de7_v6_results.json','w'), indent=1)
def run(cmd, tmo):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=max(tmo, 1))
    except subprocess.TimeoutExpired: return None
def track_stats(p):
    R = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    if not R: return {'rows': 0}
    fr = sorted({int(x['frame']) for x in R})
    return {'rows': len(R), 'frames_with_dets': len(fr), 'raw_ids': len({x['raw_id'] for x in R}), 'ids': len({x['id'] for x in R}),
            'still_rows': sum(x['still'] == '1' for x in R), 'max_dwell_s': max(float(x['dwell']) for x in R),
            'mean_dets_per_frame': round(len(R) / max(len(fr), 1), 2)}
def stopped_car(p, g):
    # SAM co bam xe dung trong su co khong: track dung yen (still=1) co t trong [start, end]
    R = list(csv.DictReader(open(p))) if os.path.exists(p) else []
    S = [x for x in R if x['still'] == '1' and g['stop_start_s'] <= float(x['t']) <= g['stop_end_s']]
    return {'still_rows_in_event': len(S), 'max_dwell_in_event_s': max((float(x['dwell']) for x in S), default=0), 'ids': sorted({x['id'] for x in S})[:10]}
FPSV = {i: cv2.VideoCapture(f'aic/{i}.mp4').get(cv2.CAP_PROP_FPS) or 30 for i in SEL}
WIN = 240
def win_args(i): return f'--video aic/{i}.mp4 --stride {round(FPSV[i])} --max_frames {int(WIN*FPSV[i])} --max_side 800 --zones configs/zones_aic_full.json'
SAM = f'--backend sam3 --sam3_ckpt {SAM3_CKPT} --amp fp16 --prompt car --offload_video --chunk_frames 60 --max_objects 32 --det_batch 1 --dump_tracks'
SAMBOX = SAM + ' --box_prompt yolo26s.pt'
RES['settings'].update(sam=SAM, sambox=SAMBOX, window_s=WIN, sample_fps=1)
# ---- sanity 5 frame (text + box) ----
r = run(f'python src/pipeline.py {win_args(35)} {SAMBOX} --sanity 5 --out out/sanity', 900)
RES['sanity'] = [l for l in (r.stdout if r else '').splitlines() if l.startswith('SANITY')] or (r.stderr[-1500:] if r else 'timeout'); save(); print(RES['sanity'], flush=True)
SAM_OK = bool(r) and r.returncode == 0
GTW = [dict(g, stop_end_s=min(g['stop_end_s'], WIN)) for g in GT if g['stop_start_s'] < WIN - 20]
g35 = [g for g in GTW if g['video'] == '35.mp4']; json.dump(g35, open('out/gt35.json','w'))
# ---- A) video 35: text-only vs text+box (800 px, 32 obj) ----
for name, extra in ([('sam31_text_800_32', SAM), ('sam31_textbox_800_32', SAMBOX)] if SAM_OK else []):
    left = BUDGET_S - (time.time() - T_START)
    if left < 600: print('BUDGET HIT', name); continue
    r = run(f'python src/pipeline.py {win_args(35)} {extra} --out out/{name}', min(left - 60, 2400))
    m = json.load(open(f'out/{name}/metrics.json')) if os.path.exists(f'out/{name}/metrics.json') else {'error': (r.stderr[-1500:] if r else 'timeout')}
    ev = json.loads(subprocess.run(f'python src/evaluate.py out/gt35.json out/{name}/alerts.json 30 --dedup_iou 0.3', shell=True, capture_output=True, text=True).stdout or '{}') if 'error' not in m else {}
    RES['sam_diag'][name] = {'metrics': m, 'eval_dedup0.3': ev, 'tracks': track_stats(f'out/{name}/tracks.csv'),
                             'stopped_car': [stopped_car(f'out/{name}/tracks.csv', g) for g in g35]}; save()
    print(name, json.dumps(RES['sam_diag'][name])[:1500], flush=True)""")
code("""# ---- B) 9 video, 240 s dau, 1 fps: YOLO26s+ByteTrack (re) roi SAM 3.1 text+box neu con ngan sach; video duong tinh truoc ----
ORDER = [i for i in SEL if any(g['video'] == f'{i}.mp4' for g in GTW)] + [i for i in SEL if not any(g['video'] == f'{i}.mp4' for g in GTW)]
CFG = {'yolo26s_bytetrack': '--backend yolo --model yolo26s.pt'}
if SAM_OK: CFG['sam31_textbox_800_32'] = SAMBOX
for name, args in CFG.items():
    ms, al = [], []
    for i in ORDER:
        left = BUDGET_S - (time.time() - T_START)
        if left < 300: print('BUDGET HIT', name, i); continue
        d = f'out/win9_{name}/{i}'
        if name.startswith('sam') and i == 35 and os.path.exists(f'out/{name}/metrics.json'): d = f'out/{name}'  # tai su dung ket qua phan A
        else: r = run(f'python src/pipeline.py {win_args(i)} {args} --out {d}', left - 60)
        if os.path.exists(f'{d}/metrics.json'): ms.append(json.load(open(f'{d}/metrics.json'))); al += json.load(open(f'{d}/alerts.json'))
        print(name, i, 'ok' if os.path.exists(f'{d}/metrics.json') else 'FAIL', flush=True)
    done = [os.path.basename(m['video']) for m in ms]; os.makedirs(f'out/win9_{name}', exist_ok=True)
    json.dump(al, open(f'out/win9_{name}/all_alerts.json','w')); json.dump([g for g in GTW if g['video'] in done], open(f'out/win9_{name}/gt.json','w'))
    ev = json.loads(subprocess.run(f'python src/evaluate.py out/win9_{name}/gt.json out/win9_{name}/all_alerts.json 30 --dedup_iou 0.3', shell=True, capture_output=True, text=True).stdout or '{}')
    nf = sum(m['frames_processed'] for m in ms)
    RES['win9'][name] = {'videos_done': done, 'n_events': len([g for g in GTW if g['video'] in done]), 'frames': nf,
        'fps_model': round(nf / max(sum(m['frames_processed'] / max(m['fps_model'], 1e-9) for m in ms), 1e-9), 3) if ms else None,
        'fps_e2e': round(nf / max(sum(m['wall_s'] for m in ms), 1e-9), 3) if ms else None,
        'vram_peak_mb': max(((m['vram_peak_mb'] or 0) for m in ms), default=None), 'eval_dedup0.3': ev}
    save(); print(name, json.dumps(RES['win9'][name]), flush=True)
RES['total_wall_s'] = round(time.time() - T_START); save()
shutil.rmtree('aic', ignore_errors=True); shutil.rmtree('weights', ignore_errors=True); shutil.rmtree('out/sanity', ignore_errors=True)
for p in glob.glob('out/**/evidence/*.mp4', recursive=True): os.remove(p)
print(open('out/de7_v6_results.json').read()[:5000])""")
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}}, "nbformat": 4, "nbformat_minor": 5}
os.makedirs(f"{ROOT}/kaggle/kernel_v6", exist_ok=True)
json.dump(nb, open(f"{ROOT}/kaggle/kernel_v6/de7_v6_sam_boxprompt.ipynb", "w"), indent=1, ensure_ascii=False)
json.dump({"id": "holilihu/de7-v6-sam-boxprompt", "title": "de7-v6-sam-boxprompt", "code_file": "de7_v6_sam_boxprompt.ipynb", "language": "python", "kernel_type": "notebook",
           "is_private": True, "enable_gpu": True, "enable_internet": True, "dataset_sources": ["holilihu/de7-weights"],
           "competition_sources": [], "kernel_sources": []}, open(f"{ROOT}/kaggle/kernel_v6/kernel-metadata.json", "w"), indent=1)
