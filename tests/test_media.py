import unittest
from unittest.mock import patch

import numpy as np

from curb.media import TimedVideoEncoder


class MediaTests(unittest.TestCase):
    def test_irregular_samples_preserve_clip_clock(self):
        with patch("curb.media.VideoEncoder") as encoder:
            clip=TimedVideoEncoder("test.mp4",10,10,5)
            frame=np.zeros((10,10,3),dtype=np.uint8)
            for timestamp in (0,.3,.9,1.6,2.0):
                clip.write_at(frame,timestamp)
            clip.close()
            self.assertEqual(encoder.return_value.write.call_count,11)
            encoder.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
