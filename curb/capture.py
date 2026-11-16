import threading
import time


class LatestFrameBuffer:
    """Bounded live-frame handoff: a slow consumer receives the newest frame."""

    def __init__(self):
        self.changed = threading.Condition()
        self.sequence = 0
        self.frame = None
        self.received_at = 0.0
        self.closed = False

    def publish(self, frame):
        with self.changed:
            if self.closed:
                return
            self.frame = frame
            self.received_at = time.monotonic()
            self.sequence += 1
            self.changed.notify_all()

    def take(self, after, timeout):
        with self.changed:
            self.changed.wait_for(lambda: self.sequence > after or self.closed, timeout=timeout)
            if self.sequence <= after or self.closed:
                return None
            return self.sequence, self.received_at, self.frame

    def close(self):
        with self.changed:
            self.closed = True
            self.frame = None
            self.changed.notify_all()


class LatestVideoCapture:
    def __init__(self, uri, read_timeout=5):
        import cv2

        self.timeout = read_timeout
        self.buffer = LatestFrameBuffer()
        self.last_sequence = 0
        self.last_frame_age = 0.0
        self.max_frame_age = 0.0
        self.read_timeouts = 0
        self.skipped_frames = 0
        self.cap = cv2.VideoCapture(uri, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,8000,cv2.CAP_PROP_READ_TIMEOUT_MSEC,int(read_timeout*1000)])
        self.opened = self.cap.isOpened()
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) if self.opened else 0
        self.stop = threading.Event()
        self.thread = None
        if self.opened:
            self.thread = threading.Thread(target=self._receive, daemon=True)
            self.thread.start()

    def _receive(self):
        try:
            while not self.stop.is_set():
                ok, frame = self.cap.read()
                if not ok:
                    break
                self.buffer.publish(frame)
        finally:
            self.cap.release()
            self.buffer.close()

    def isOpened(self):
        return self.opened

    def get(self, prop):
        import cv2

        return self.fps if prop == cv2.CAP_PROP_FPS else 0

    def read(self):
        value = self.buffer.take(self.last_sequence, self.timeout)
        if value is None:
            self.read_timeouts += 1
            return False, None
        sequence, received_at, frame = value
        self.skipped_frames += max(0, sequence-self.last_sequence-1)
        self.last_sequence = sequence
        self.last_frame_age = time.monotonic()-received_at
        self.max_frame_age = max(self.max_frame_age, self.last_frame_age)
        return True, frame

    def release(self):
        self.stop.set()
        self.buffer.close()
        if self.thread:
            self.thread.join(timeout=self.timeout+1)
        else:
            self.cap.release()
