"""Pruebas de integración sin abrir cámara, ventana ni dispositivo de audio."""
from contextlib import ExitStack
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

import numpy as np

import main as app
import ui
from contracts import HandObservation
from test_gestures import hand, hands


class TestMainIntegration(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.frame = np.zeros((330, 640, 3), dtype=np.uint8)
        self.frame[:, :320] = (255, 0, 0)
        self.frame[:, 320:] = (0, 0, 255)
        self.original = self.frame.copy()
        self.camera = Mock()
        self.camera.read.return_value = self.frame
        self.tracker = Mock()
        self.tracker.detect.return_value = []
        self.player = Mock()
        self.camera_class = self.stack.enter_context(patch.object(app, 'Camera', return_value=self.camera))
        self.tracker_class = self.stack.enter_context(patch.object(app, 'HandTracker', return_value=self.tracker))
        self.player_class = self.stack.enter_context(patch.object(app, 'AudioPlayer', return_value=self.player))
        self.show = self.stack.enter_context(patch.object(app, 'mostrar_pantalla'))
        self.key = self.stack.enter_context(patch.object(app.cv2, 'waitKey', return_value=27))
        self.visible = self.stack.enter_context(patch.object(app.cv2, 'getWindowProperty', return_value=1))
        self.destroy = self.stack.enter_context(patch.object(app.cv2, 'destroyAllWindows'))
        self.stack.enter_context(patch.object(app, 'monotonic_ns', return_value=0))
        self.stack.enter_context(patch.object(app, 'VENTANA_ESTABILIDAD_MS', 0))
        self.stack.enter_context(patch('builtins.print'))

    def assert_closed(self):
        self.camera.close.assert_called_once_with()
        self.tracker.close.assert_called_once_with()
        self.player.close.assert_called_once_with()
        self.destroy.assert_called_once_with()

    def test_calibration_then_note_release_and_hand_loss(self):
        # C, 5 s reposo, 5 s levantados, vuelta al reposo y RE4.
        times = [0,4000,4300,4600,4800,5000,9000,9300,9600,9800,10000,10100,10200,10300,10400]
        observations = ([hands()] * 6 + [hands(range(5),range(5))] * 5 +
                        [hands(), hands((1,), (2,)), hands(), []])
        self.tracker.detect.side_effect = observations
        self.key.side_effect = [ord('c')] + [-1] * (len(times)-2) + [27]
        with patch.object(app, 'monotonic_ns', side_effect=[t*1_000_000 for t in times]):
            app.main()
        states = [call.args[0] for call in self.player.update.call_args_list]
        self.assertTrue(all(s.note is None for s in states[:12]))
        self.assertIn(('RE',4), [(s.note,s.octave) for s in states])
        self.assertIsNone(states[-2].note)
        self.assertFalse(states[-1].valid)
        self.assertIn('ambas manos', states[-1].reason)
        for call in self.tracker.detect.call_args_list:
            self.assertIs(call.args[0], self.frame)
        np.testing.assert_array_equal(self.frame, self.original)
        self.assert_closed()

    def test_uncalibrated_hands_never_play(self):
        self.tracker.detect.return_value = hands((1,))
        app.main()
        self.assertFalse(self.player.update.call_args.args[0].valid)
        self.assertIsNone(self.player.update.call_args.args[0].note)
        self.assert_closed()

    def test_failed_calibration_stays_muted(self):
        times=[0,5000]
        self.key.side_effect=[ord('c'),27]
        with patch.object(app, 'monotonic_ns', side_effect=[t*1_000_000 for t in times]):
            app.main()
        self.assertTrue(all(call.args[0].note is None for call in self.player.update.call_args_list))
        self.assertIn('repite C', self.player.update.call_args.args[0].reason)
        self.assert_closed()

    def test_escape_closes_every_resource(self):
        app.main()
        self.assertEqual(self.camera.read.call_count, 1)
        self.assert_closed()

    def test_window_x_closes_every_resource(self):
        self.key.return_value = -1
        self.visible.return_value = 0
        app.main()
        self.assertEqual(self.camera.read.call_count, 1)
        self.assert_closed()

    def test_camera_read_failure_silences_and_closes(self):
        self.camera.read.return_value = None
        app.main()
        self.tracker.detect.assert_not_called()
        self.assertFalse(self.player.update.call_args.args[0].valid)
        self.show.assert_not_called()
        self.assert_closed()

    def test_tracker_initialization_failure_releases_camera(self):
        self.tracker_class.side_effect = RuntimeError('modelo no disponible')
        with self.assertRaisesRegex(RuntimeError, 'modelo'):
            app.main()
        self.camera.close.assert_called_once_with()
        self.player_class.assert_not_called()
        self.destroy.assert_called_once_with()

    def test_audio_initialization_failure_releases_camera_and_tracker(self):
        self.player_class.side_effect = RuntimeError('audio no disponible')
        with self.assertRaisesRegex(RuntimeError, 'audio'):
            app.main()
        self.camera.close.assert_called_once_with()
        self.tracker.close.assert_called_once_with()
        self.destroy.assert_called_once_with()

    def test_processing_failure_closes_every_resource(self):
        self.tracker.detect.side_effect = RuntimeError('fallo de procesamiento')
        with self.assertRaisesRegex(RuntimeError, 'procesamiento'):
            app.main()
        self.assert_closed()


class TestCameraPresentation(unittest.TestCase):
    def test_mirror_is_visual_only(self):
        frame = np.zeros((330, 640, 3), dtype=np.uint8)
        frame[:, :320] = (255, 0, 0)
        frame[:, 320:] = (0, 0, 255)
        original = frame.copy()
        for mirror in (False, True):
            with self.subTest(mirror=mirror), patch.object(ui, 'ESPEJO', mirror):
                screen = ui.crear_pantalla(frame=frame)
                expected_left = (0, 0, 255) if mirror else (255, 0, 0)
                self.assertEqual(tuple(screen[300, 70]), expected_left)
                np.testing.assert_array_equal(frame, original)

    def test_labels_keep_identity_and_follow_mirrored_points(self):
        hands = [HandObservation('Left', [(0.15, 0.6, 0.0)] * 21),
                 HandObservation('Right', [(0.8, 0.6, 0.0)] * 21)]
        positions = {}
        for mirror in (False, True):
            with patch.object(ui, 'ESPEJO', mirror), patch.object(ui, 'escribir_texto') as write:
                screen = np.zeros((700, 1100, 3), dtype=np.uint8)
                ui._dibujar_camara(screen, np.zeros((330, 640, 3), dtype=np.uint8), hands)
                self.assertEqual([call.args[1] for call in write.call_args_list], ['Izquierda', 'Derecha'])
                positions[mirror] = write.call_args_list[0].args[2][0]
        self.assertGreater(positions[True], positions[False])
        self.assertEqual(hands[0].side, 'Left')
        self.assertEqual(hands[0].points[0][0], 0.15)

    def test_camera_preserves_aspect_ratio(self):
        frame = np.full((720, 1280, 3), (11, 22, 33), dtype=np.uint8)
        screen = ui.crear_pantalla(frame=frame)
        matches = np.flatnonzero(np.all(screen[400] == (11, 22, 33), axis=1))
        self.assertEqual(len(matches), round(1280 * 330 / 720))
        self.assertEqual(matches[0], 60 + (640 - len(matches)) // 2)


if __name__ == '__main__':
    unittest.main()
