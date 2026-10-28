import unittest
from types import SimpleNamespace
import numpy as np
from contracts import FingerState
from gestures import GestureAnalyzer, GestureConfig
from stabilizer import Stabilizer
from music import MusicEngine

NONE = [False] * 5


def hand(side, active=(), lift=.08):
    p = np.zeros((21, 3))
    p[:] = (.5, .7, 0)
    p[0] = (.5, .85, 0)
    p[1:5] = [( .4,.7,0),(.35,.65,0),(.3,.6,0),(.25,.55,0)]
    for i, x in enumerate((.4,.47,.54,.61)):
        base = 5 + i * 4
        p[base:base+4] = [(x,.6,0),(x,.5,0),(x,.42,0),(x,.35,0)]
    for i in active:
        tip = (4,8,12,16,20)[i]
        p[tip, 2] -= lift
        p[tip, 1] += lift / 3
    if side == 'Left':
        p[:, 0] = 1 - p[:, 0]
    return SimpleNamespace(side=side, points=p.tolist())


def hands(left=(), right=(), **kwargs):
    return [hand('Left', left, **kwargs), hand('Right', right, **kwargs)]


class TestLiftGestures(unittest.TestCase):
    def setUp(self):
        self.a = GestureAnalyzer()
        self.assertTrue(self.a.save_rest([hands()] * 5))
        self.assertTrue(self.a.save_raised([hands(range(5), range(5))] * 5))
        self.a.analyze(hands())

    def test_extended_rest_is_silent(self):
        state = self.a.analyze(hands())
        self.assertTrue(state.valid)
        self.assertEqual(state.left, NONE)
        self.assertIsNone(MusicEngine().resolve(state).note)

    def test_each_finger_in_each_hand(self):
        for side in ('left', 'right'):
            for i in range(5):
                self.a.analyze(hands())
                state = self.a.analyze(hands(**{side: (i,)}))
                self.assertEqual(getattr(state, side), [j == i for j in range(5)])
                self.assertEqual(getattr(state, 'right' if side == 'left' else 'left'), NONE)

    def test_note_and_octave_use_raised_fingers(self):
        state = self.a.analyze(hands((1,), (2,)))
        music = MusicEngine().resolve(state)
        self.assertEqual((music.note, music.octave), ('RE', 4))
        self.assertIsNone(MusicEngine().resolve(self.a.analyze(hands())).note)

    def test_must_return_to_rest_after_calibration(self):
        self.a.reset()
        self.a.save_rest([hands()] * 5)
        self.a.save_raised([hands(range(5), range(5))] * 5)
        self.assertEqual(self.a.analyze(hands((1,))).left, NONE)
        self.a.analyze(hands())
        self.assertTrue(self.a.analyze(hands((1,))).left[1])

    def test_translation_scale_and_rotation_of_whole_hand_do_not_play(self):
        changed = hands()
        for h in changed:
            p = np.asarray(h.points)
            p *= 1.2
            angle = .4
            matrix = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
            p[:, :2] = p[:, :2] @ matrix.T + (.05, -.03)
            h.points = p.tolist()
        result = self.a.analyze(changed)
        self.assertEqual(result.left, NONE)
        self.assertEqual(result.right, NONE)

    def test_small_movement_does_not_play(self):
        self.assertEqual(self.a.analyze(hands((1,), lift=.01)).left, NONE)

    def test_hysteresis_and_repeated_press(self):
        self.assertTrue(self.a.analyze(hands((1,))).left[1])
        self.assertTrue(self.a.analyze(hands((1,), lift=.04)).left[1])
        self.assertFalse(self.a.analyze(hands((1,), lift=.02)).left[1])
        self.assertTrue(self.a.analyze(hands((1,))).left[1])

    def test_missing_hand_stops_and_requires_return_to_rest(self):
        self.assertTrue(self.a.analyze(hands((1,))).left[1])
        self.assertFalse(self.a.analyze([hand('Left')]).valid)
        self.assertFalse(self.a.analyze(hands((1,))).left[1])
        self.a.analyze(hands())
        self.assertTrue(self.a.analyze(hands((1,))).left[1])

    def test_no_calibration_is_invalid(self):
        self.assertFalse(GestureAnalyzer().analyze(hands()).valid)

    def test_invalid_input_is_silent(self):
        bad = hands()
        bad[0].points[8] = (float('nan'),0,0)
        for value in ([], None, bad, [hand('Left'),hand('Left')], [hand('X'),hand('Right')]):
            self.assertFalse(self.a.analyze(value).valid)

    def test_incomplete_or_unchanged_calibration_rejected(self):
        a = GestureAnalyzer()
        self.assertFalse(a.save_rest([hands()] * 4))
        self.assertTrue(a.save_rest([hands()] * 5))
        self.assertFalse(a.save_raised([hands()] * 5))
        self.assertFalse(a.calibrated)

    def test_unclear_noisy_calibration_is_rejected(self):
        a = GestureAnalyzer()
        a.save_rest([hands()] * 5)
        unstable = [hands(range(5), range(5), lift=v) for v in (.02,.14,.02,.14,.08)]
        self.assertFalse(a.save_raised(unstable))
        self.assertFalse(a.calibrated)

    def test_dictionary_observations_and_reset(self):
        observation = [vars(h) for h in hands((2,))]
        self.assertTrue(self.a.analyze(observation).left[2])
        self.a.reset()
        self.assertFalse(self.a.analyze(observation).valid)

    def test_configuration_validation(self):
        for kwargs in ({'press_fraction':.2, 'release_fraction':.5}, {'min_travel':0}, {'depth_weight':float('nan')}):
            with self.assertRaises(ValueError):
                GestureConfig(**kwargs)


class TestStabilizer(unittest.TestCase):
    def test_brief_change_ignored_and_loss_immediate(self):
        st = Stabilizer(100)
        rest = FingerState(True)
        raised = FingerState(True, [False,True,False,False,False], NONE)
        self.assertFalse(st.update(rest, 0).valid)
        self.assertTrue(st.update(rest, 100).valid)
        self.assertFalse(st.update(raised, 110).left[1])
        self.assertFalse(st.update(rest, 150).left[1])
        st.update(raised, 200)
        self.assertTrue(st.update(raised, 300).left[1])
        self.assertFalse(st.update(FingerState(), 301).valid)

    def test_timestamps_and_copy(self):
        st = Stabilizer(0)
        state = FingerState(True)
        result = st.update(state, 0)
        result.left[0] = True
        self.assertFalse(st.update(state, 1).left[0])
        with self.assertRaises(ValueError):
            st.update(state, 1)
