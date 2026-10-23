import json
cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s})
md("# Đề 7 — Phát hiện & cảnh báo xe dừng/đỗ trái phép: SAM 3.1 + DINOv3 vs YOLO26+ByteTrack\n"
   "Chạy được trên Kaggle (GPU T4) hoặc Colab. Trọng số chỉ đọc từ /kaggle/input (dataset holilihu/de7-weights: SAM 3.1 + DINOv3), không tải HF, không dùng Secrets. "
   "Trên Kaggle của tác giả, trọng số lấy từ dataset riêng `de7-weights` nên không cần token.")
code("""import os, sys, subprocess, json, glob, shutil
IN_KAGGLE = os.path.exists('/kaggle')
WORK = '/kaggle/working' if IN_KAGGLE else '/content'
os.chdir(WORK)
!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
!pip -q install "git+https://github.com/facebookresearch/sam3.git@7f473cf" ultralytics lap "transformers>=4.56" einops decord pycocotools 2>&1 | tail -2
import torch; print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))""")
code("""# Code + du lieu: Kaggle -> dataset de7-code; Colab -> git/zip tu Drive (tu chinh duong dan)
_c = glob.glob('/kaggle/input/**/src/pipeline.py', recursive=True)
CODE = os.path.dirname(os.path.dirname(_c[0])) if _c else '/content/de7'
print('CODE', CODE)
for d in ['src', 'configs', 'data']:
    if os.path.exists(f'{CODE}/{d}') and not os.path.exists(d): shutil.copytree(f'{CODE}/{d}', d)
_w = glob.glob('/kaggle/input/**/sam31_sha256.txt', recursive=True)
WDIR = os.path.dirname(_w[0]) if _w else '/nonexistent'
print('WDIR', WDIR)
if os.path.exists(WDIR):
    import hashlib
    os.makedirs('weights', exist_ok=True); SAM3_CKPT = 'weights/sam3.1_multiplex.pt'
    if not os.path.exists(SAM3_CKPT):
        subprocess.run(f'cat {WDIR}/sam31_part_* > {SAM3_CKPT}', shell=True, check=True)
    print('sha256 ok:', open(f'{WDIR}/sam31_sha256.txt').read().strip() == subprocess.check_output(['sha256sum', SAM3_CKPT]).decode()[:64])
    for r in ['dinov3-vits16-pretrain-lvd1689m', 'dinov3-vitb16-pretrain-lvd1689m']:
        os.makedirs(f'weights/{r}', exist_ok=True)
        for f in glob.glob(f'{WDIR}/{r}__*'):
            dst = f'weights/{r}/' + os.path.basename(f).split('__', 1)[1]
            if not os.path.exists(dst): os.symlink(f, dst)
    DINO = 'weights/dinov3-vits16-pretrain-lvd1689m'
else:
    raise SystemExit('Thieu dataset holilihu/de7-weights (Kaggle) — notebook khong tai tu HF')
print(SAM3_CKPT, DINO)""")
code("""os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
VID = 'data/gaithersburg_480p.webm'; Z = 'configs/zones_gaithersburg.json'
STRIDE = 3   # 30 fps -> 10 fps
def run(name, args):
    cmd = f'python src/pipeline.py --video {VID} --zones {Z} --stride {STRIDE} --out out/{name} --save_video {args}'
    print('>>>', name, flush=True); r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print('\\n'.join([l for l in r.stdout.splitlines() if l.startswith(('ALERT','METRICS'))][-6:]))
    if r.returncode:
        err = r.stderr.splitlines(); print('\\n'.join([l for l in err if 'sam3/' in l or 'pipeline.py' in l][-12:] + err[-3:]))
    return r.returncode == 0
run('yolo26n_bytetrack', '--backend yolo --model yolo26n.pt --tracker bytetrack.yaml')
run('yolo26s_botsort', '--backend yolo --model yolo26s.pt --tracker botsort.yaml')
run('yolo26s_bytetrack_dino', f'--backend yolo --model yolo26s.pt --reid {DINO}')
# SAM 3.1 tren T4 16GB: thu cau hinh giam dan VRAM (offload frames ra CPU, chunk ngan, it object)
SAM = f'--backend sam3 --sam3_ckpt {SAM3_CKPT} --amp bf16 --offload_video'
for ch, mo, db in [(150, 16, 2), (150, 16, 1), (60, 8, 1)]:
    tag = f'sam31_c{ch}_o{mo}_b{db}'
    if run(tag, f'{SAM} --chunk_frames {ch} --max_objects {mo} --det_batch {db}'):
        run(tag + '_dino', f'{SAM} --chunk_frames {ch} --max_objects {mo} --det_batch {db} --reid {DINO}'); break""")
code("""import csv
rows = [json.load(open(p)) for p in sorted(glob.glob('out/*/metrics.json'))]
keys = ['backend','model','tracker','reid','device','amp','stride','frames_processed','fps_model','fps_end2end','vram_peak_mb','n_alerts','jam_frames','reid_merges']
with open('out/metrics_table.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); w.writeheader(); [w.writerow(r) for r in rows]
print(open('out/metrics_table.csv').read())""")
nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open("notebooks/de7_sam31_dinov3.ipynb", "w"), indent=1, ensure_ascii=False)
