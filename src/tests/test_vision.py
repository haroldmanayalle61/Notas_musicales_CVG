import unittest
from pathlib import Path

import numpy as np

from vision import HandTracker


class TestVision(unittest.TestCase):

    def test_modelo_existe(self):
        ruta_modelo = (
            Path(__file__).resolve().parent.parent
            / "models"
            / "hand_landmarker.task"
        )
        self.assertTrue(ruta_modelo.is_file())

    def test_sin_manos(self):
        tracker = HandTracker()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        hands = tracker.detect(frame, 1)
        self.assertEqual(hands, [])
        tracker.close()

    def test_maximo_dos_manos(self):
        tracker = HandTracker()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        hands = tracker.detect(frame, 2)
        self.assertLessEqual(len(hands), 2)
        tracker.close()


if __name__ == "__main__":
    unittest.main()