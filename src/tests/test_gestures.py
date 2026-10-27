import math
import unittest
from types import SimpleNamespace

from gestures import analyze, FingerState
from stabilizer import Stabilizer

PIVOT = (0.5, 0.8)


def make_points(fingers, mirror=False, angle=0.0):
    """Mano sintetica vertical. fingers = [pulgar, indice, medio, anular, menique]."""
    p = [(0.0, 0.0)] * 21
    p[0] = (0.5, 0.8)
    p[1], p[2] = (0.46, 0.74), (0.40, 0.68)
    if fingers[0]:
        p[3], p[4] = (0.34, 0.62), (0.28, 0.57)
    else:
        p[3], p[4] = (0.47, 0.64), (0.53, 0.62)
    for i, x in enumerate((0.43, 0.48, 0.53, 0.58)):
        b = 5 + 4 * i
        p[b] = (x, 0.55)
        if fingers[i + 1]:
            p[b + 1], p[b + 2], p[b + 3] = (x, 0.47), (x, 0.41), (x, 0.36)
        else:
            p[b + 1], p[b + 2], p[b + 3] = (x, 0.47), (x, 0.53), (x, 0.60)
    out = []
    c, s = math.cos(angle), math.sin(angle)
    for x, y in p:
        if mirror:
            x = 1.0 - x
        dx, dy = x - PIVOT[0] if not mirror else x - (1.0 - PIVOT[0]), y - PIVOT[1]
        cx = (1.0 - PIVOT[0]) if mirror else PIVOT[0]
        out.append((cx + dx * c - dy * s, PIVOT[1] + dx * s + dy * c, 0.0))
    return out


def hand(side, fingers, **kw):
    return SimpleNamespace(side=side, points=make_points(fingers, mirror=(side == "Left"), **kw))


ALL = [True] * 5
NONE = [False] * 5


class TestAnalyze(unittest.TestCase):
    def test_all_extended(self):
        s = analyze([hand("Left", ALL), hand("Right", ALL)])
        self.assertTrue(s.valid)
        self.assertEqual(s.left, ALL)
        self.assertEqual(s.right, ALL)

    def test_all_flexed_is_valid(self):
        s = analyze([hand("Left", NONE), hand("Right", NONE)])
        self.assertTrue(s.valid)
        self.assertEqual(s.left, NONE)
        self.assertEqual(s.right, NONE)

    def test_each_finger_individually(self):
        for i in range(5):
            f = [j == i for j in range(5)]
            for side_l, side_r in (("Left", "Right"), ("Right", "Left")):
                s = analyze([hand(side_l, f), hand(side_r, NONE)])
                self.assertTrue(s.valid)
                got = s.left if side_l == "Left" else s.right
                self.assertEqual(got, f, f"dedo {i}")

    def test_thumbs_both_sides(self):
        s = analyze([hand("Left", [True, False, False, False, False]),
                     hand("Right", [True, False, False, False, False])])
        self.assertEqual(s.left[0], True)
        self.assertEqual(s.right[0], True)

    def test_rotation_invariant(self):
        f = [True, True, False, True, False]
        for ang in (0.5, 1.57, 3.14, -1.0):
            s = analyze([hand("Left", f, angle=ang), hand("Right", f, angle=ang)])
            self.assertEqual(s.left, f)
            self.assertEqual(s.right, f)

    def test_missing_hands_invalid(self):
        self.assertFalse(analyze([]).valid)
        self.assertFalse(analyze(None).valid)
        self.assertFalse(analyze([hand("Left", ALL)]).valid)
        self.assertFalse(analyze([hand("Right", ALL)]).valid)

    def test_invalid_is_not_all_flexed(self):
        s = analyze([hand("Left", NONE)])
        self.assertFalse(s.valid)

    def test_duplicate_or_unknown_side_invalid(self):
        self.assertFalse(analyze([hand("Left", ALL), hand("Left", ALL)]).valid)
        self.assertFalse(analyze([hand("Left", ALL), SimpleNamespace(side="X", points=make_points(ALL))]).valid)

    def test_bad_points_invalid(self):
        bad = SimpleNamespace(side="Right", points=make_points(ALL)[:20])
        self.assertFalse(analyze([hand("Left", ALL), bad]).valid)
        nan = make_points(ALL)
        nan[8] = (float("nan"), 0.0, 0.0)
        self.assertFalse(analyze([hand("Left", ALL), SimpleNamespace(side="Right", points=nan)]).valid)
        flat = SimpleNamespace(side="Right", points=[(0.5, 0.5, 0.0)] * 21)
        self.assertFalse(analyze([hand("Left", ALL), flat]).valid)

    def test_accepts_dicts(self):
        h = [{"side": "Left", "points": make_points(ALL)},
             {"side": "Right", "points": make_points(NONE)}]
        s = analyze(h)
        self.assertTrue(s.valid)
        self.assertEqual(s.left, ALL)
        self.assertEqual(s.right, NONE)


def fs(valid=True, left=None, right=None):
    return FingerState(valid=valid, left=list(left or NONE), right=list(right or NONE))


class TestStabilizer(unittest.TestCase):
    A = [True, False, False, False, False]
    B = [False, True, False, False, False]

    def test_needs_window_to_change(self):
        st = Stabilizer(window_ms=100)
        self.assertFalse(st.update(fs(left=self.A), 0).valid)
        self.assertFalse(st.update(fs(left=self.A), 50).valid)
        out = st.update(fs(left=self.A), 100)
        self.assertTrue(out.valid)
        self.assertEqual(out.left, self.A)

    def test_brief_glitch_ignored(self):
        st = Stabilizer(window_ms=100)
        st.update(fs(left=self.A), 0)
        st.update(fs(left=self.A), 100)
        self.assertEqual(st.update(fs(left=self.B), 133).left, self.A)
        self.assertEqual(st.update(fs(left=self.A), 166).left, self.A)
        self.assertEqual(st.update(fs(left=self.A), 400).left, self.A)

    def test_sustained_change_accepted(self):
        st = Stabilizer(window_ms=100)
        st.update(fs(left=self.A), 0)
        st.update(fs(left=self.A), 100)
        st.update(fs(left=self.B), 133)
        self.assertEqual(st.update(fs(left=self.B), 200).left, self.A)
        self.assertEqual(st.update(fs(left=self.B), 233).left, self.B)

    def test_invalid_is_immediate_silence(self):
        st = Stabilizer(window_ms=100)
        st.update(fs(left=self.A), 0)
        st.update(fs(left=self.A), 100)
        out = st.update(fs(valid=False), 133)
        self.assertFalse(out.valid)
        # al volver, debe reestabilizarse
        self.assertFalse(st.update(fs(left=self.A), 166).valid)
        self.assertTrue(st.update(fs(left=self.A), 266).valid)

    def test_timestamps_must_increase(self):
        st = Stabilizer()
        st.update(fs(), 10)
        with self.assertRaises(ValueError):
            st.update(fs(), 10)

    def test_returns_copies(self):
        st = Stabilizer(window_ms=0)
        out = st.update(fs(left=self.A), 0)
        out.left[0] = False
        self.assertEqual(st.update(fs(left=self.A), 1).left, self.A)


if __name__ == "__main__":
    unittest.main()