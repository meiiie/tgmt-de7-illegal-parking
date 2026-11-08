import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NO_WINDOW = getattr(subprocess,"CREATE_NO_WINDOW",0)


def sha256(path):
    digest = hashlib.sha256()
    with open(path,"rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def probe(uri, output: Path):
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run([sys.executable,"-m","curb.media",str(output)],input=json.dumps({"uri":str(uri)}),text=True,capture_output=True,timeout=22,cwd=ROOT,creationflags=NO_WINDOW)
        result = json.loads(proc.stdout) if proc.returncode == 0 else {}
        if not result.get("width"):
            raise ValueError("Không đọc được hình ảnh. Kiểm tra tệp, địa chỉ camera, tài khoản hoặc kết nối rồi thử lại.")
        return result
    except (subprocess.TimeoutExpired,json.JSONDecodeError) as exc:
        raise ValueError("Nguồn không phản hồi trong 22 giây. Kiểm tra camera hoặc thử video khác.") from exc


class VideoEncoder:
    def __init__(self, path, width, height, fps):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.closed = False
        self.proc = subprocess.Popen(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","rawvideo","-pix_fmt","bgr24","-s",f"{width}x{height}","-r",str(fps),"-i","pipe:0","-an","-vf","pad=ceil(iw/2)*2:ceil(ih/2)*2","-c:v","libx264","-preset","ultrafast","-crf","25","-pix_fmt","yuv420p","-movflags","+faststart",str(path)],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=NO_WINDOW)

    def write(self, frame):
        try:
            self.proc.stdin.write(frame.tobytes())
        except (BrokenPipeError,OSError) as exc:
            raise RuntimeError("Không ghi được video bằng chứng. Kiểm tra FFmpeg và dung lượng ổ đĩa.") from exc

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.proc.stdin.close()
        try:
            code = self.proc.wait(timeout=40)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
            raise RuntimeError("FFmpeg không hoàn tất video trong thời gian cho phép.")
        if code:
            raise RuntimeError("FFmpeg không thể hoàn tất video bằng chứng.")


class TimedVideoEncoder:
    """Resample irregular camera timestamps without accelerating evidence playback."""

    def __init__(self,path,width,height,fps):
        self.encoder=VideoEncoder(path,width,height,fps)
        self.step=1/fps
        self.next_time=None
        self.previous=None

    def write_at(self,frame,t):
        if self.next_time is None:
            self.next_time=t
            self.previous=frame.copy()
        while self.next_time <= t+1e-6:
            self.encoder.write(self.previous)
            self.next_time+=self.step
        self.previous=frame.copy()

    def close(self):
        self.encoder.close()


def probe_main():
    os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
    os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS","rtsp_transport;tcp")
    import cv2
    uri = json.loads(sys.stdin.read())["uri"]
    cap = cv2.VideoCapture(uri,cv2.CAP_FFMPEG,[cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,10000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,8000])
    try:
        ok, frame = cap.read()
        if not ok:
            sys.exit(2)
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if 0 < fps < 241 else 25.0
        count = max(0,int(cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        h,w = frame.shape[:2]
        if max(h,w) > 1280:
            frame = cv2.resize(frame,(round(w*1280/max(h,w)),round(h*1280/max(h,w))))
        if not cv2.imwrite(sys.argv[1],frame):
            sys.exit(3)
        print(json.dumps({"width":w,"height":h,"fps":round(fps,4),"frames":count,"duration":round(count/fps,3) if count else None}))
    finally:
        cap.release()


if __name__ == "__main__":
    probe_main()
