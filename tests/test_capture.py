import threading
import unittest

from curb.capture import LatestFrameBuffer


class LiveBufferTests(unittest.TestCase):
    def test_slow_consumer_gets_latest_frame_without_replaying_backlog(self):
        buffer = LatestFrameBuffer()
        for frame in ("first", "second", "latest"):
            buffer.publish(frame)
        sequence, received_at, frame = buffer.take(0, .01)
        self.assertEqual((sequence, frame), (3, "latest"))
        self.assertGreater(received_at, 0)
        self.assertIsNone(buffer.take(sequence, .01))
        buffer.publish("new")
        self.assertEqual(buffer.take(sequence, .01)[2], "new")

    def test_close_wakes_waiting_consumer_without_returning_stale_frame(self):
        buffer = LatestFrameBuffer()
        buffer.publish("stale")
        result = []
        waiting = threading.Thread(target=lambda: result.append(buffer.take(1, 3)))
        waiting.start()
        buffer.close()
        waiting.join(timeout=1)
        self.assertFalse(waiting.is_alive())
        self.assertEqual(result, [None])


if __name__ == "__main__":
    unittest.main()
