# Parte de Hirano
# Comprueba las notas, las octavas y la reproducción sin usar la cámara.


# SECCIÓN 1: Importar las herramientas de pruebas y los módulos

import itertools
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from audio import AudioPlayer
from contracts import FingerState, MusicState
from music import MusicEngine, combinaciones_musicales, nombre_archivo


# SECCIÓN 2: Comprobar las decisiones musicales

class TestMusic(unittest.TestCase):

    def test_combinaciones_de_dedos(self):
        motor = MusicEngine()
        notas = ("DO", "RE", "MI", "FA", "SOL", "LA", "SI")

        for dedos in itertools.product((False, True), repeat=10):
            estado = FingerState(
                True,
                list(dedos[:5]),
                list(dedos[5:])
            )

            resultado = motor.resolve(estado)
            musicales = dedos[:7]

            esperada = (
                notas[musicales.index(True)]
                if sum(musicales) == 1
                else None
            )

            with self.subTest(dedos=dedos):
                self.assertTrue(resultado.valid)
                self.assertEqual(resultado.note, esperada)
                self.assertEqual(
                    resultado.octave,
                    3 + sum(dedos[7:])
                )

    def test_los_28_nombres(self):
        esperados = {
            f"{letra}{octava}.wav"
            for letra in "CDEFGAB"
            for octava in range(3, 7)
        }

        obtenidos = {
            nombre_archivo(*par)
            for par in combinaciones_musicales()
        }

        self.assertEqual(obtenidos, esperados)

    def test_perdida_de_manos(self):
        resultado = MusicEngine().resolve(
            FingerState(valid=False)
        )

        self.assertFalse(resultado.valid)
        self.assertIsNone(resultado.note)
        self.assertIsNone(resultado.octave)

    def test_datos_incorrectos(self):
        casos = [
            None,
            FingerState(True, [], []),
            FingerState(
                True,
                [1, False, False, False, False],
                [False] * 5
            )
        ]

        for estado in casos:
            with self.subTest(estado=estado):
                self.assertFalse(
                    MusicEngine().resolve(estado).valid
                )

    def test_nota_y_octava_incorrectas(self):
        casos = [
            ("DO#", 4),
            ("DO", 2),
            ("RE", True),
            ("MI", 4.0)
        ]

        for nota, octava in casos:
            with self.subTest(nota=nota, octava=octava):
                with self.assertRaises(ValueError):
                    nombre_archivo(nota, octava)


# SECCIÓN 3: Comprobar el audio con un reproductor simulado

class TestAudio(unittest.TestCase):

    def test_activaciones_silencio_y_cierre(self):
        mixer = Mock()
        mixer.get_init.side_effect = [None, (44100, -16, 2)]
        mixer.Sound.side_effect = lambda **opciones: Mock()

        pygame_simulado = types.SimpleNamespace(
            mixer=mixer,
            error=RuntimeError
        )

        with patch.dict(
            sys.modules,
            {"pygame": pygame_simulado}
        ):
            with patch("audio.Path.is_file", return_value=True):
                reproductor = AudioPlayer()

                try:
                    canal = mixer.find_channel.return_value

                    self.assertEqual(mixer.Sound.call_count, 28)

                    # Repetir el gesto no debe reiniciar la nota.
                    for _ in range(300):
                        reproductor.update(
                            MusicState(True, "RE", 4)
                        )

                    self.assertEqual(canal.play.call_count, 1)

                    # Cambiar de octava produce otra pulsación.
                    reproductor.update(MusicState(True, "RE", 5))
                    self.assertEqual(canal.play.call_count, 2)

                    # Soltar permite volver a tocar la misma nota.
                    reproductor.update(MusicState(valid=True))
                    reproductor.update(MusicState(True, "RE", 5))
                    self.assertEqual(canal.play.call_count, 3)

                    # Perder las manos detiene el sonido.
                    paradas = canal.stop.call_count
                    reproductor.update(MusicState(valid=False))

                    self.assertEqual(
                        canal.stop.call_count,
                        paradas + 1
                    )

                finally:
                    reproductor.close()

                reproductor.close()

                mixer.init.assert_called_once()
                mixer.quit.assert_called_once()

    def test_audios_faltantes(self):
        with patch("audio.Path.is_file", return_value=False):
            with self.assertRaisesRegex(
                FileNotFoundError,
                "C3.wav"
            ):
                AudioPlayer()


# SECCIÓN 4: Ejecutar las pruebas

if __name__ == "__main__":
    unittest.main()