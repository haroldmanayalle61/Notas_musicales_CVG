from contextlib import ExitStack
from math import ceil
from time import monotonic_ns
import cv2
from audio import AudioPlayer
from camera import Camera
from config import (
    CAMARA_INDICE, ESPERA_MS, NOMBRE_VENTANA, TECLA_SALIR,
    VENTANA_ESTABILIDAD_MS, TECLA_CALIBRAR, CALIBRACION_SEGUNDOS,
    CALIBRACION_MUESTREO_MS, CALIBRACION_MIN_MUESTRAS,
    GESTO_ACTIVACION, GESTO_LIBERACION, GESTO_RECORRIDO_MINIMO,
    GESTO_TOLERANCIA_LATERAL, PESO_PROFUNDIDAD,
)
from contracts import MusicState
from gestures import GestureAnalyzer, GestureConfig, invalid_state
from music import MusicEngine
from stabilizer import Stabilizer
from ui import crear_pantalla, mostrar_pantalla
from vision import HandTracker


def main():
    with ExitStack() as resources:
        resources.callback(cv2.destroyAllWindows)
        camera = Camera(index=CAMARA_INDICE)
        resources.callback(camera.close)
        tracker = HandTracker()
        resources.callback(tracker.close)
        player = AudioPlayer()
        resources.callback(player.close)
        stabilizer = Stabilizer(window_ms=VENTANA_ESTABILIDAD_MS)
        engine = MusicEngine()
        analyzer = None
        image_shape = None
        deadline = None
        phase = None
        samples = []
        message = "Pulsa C: calibra reposo y dedos levantados"
        last_timestamp = -1

        while True:
            frame = camera.read()
            if frame is None:
                player.update(MusicState(reason="Fallo de lectura de la camara"))
                print("No se pudo leer la camara. Revisa su conexion.")
                break
            shape = frame.shape[:2]
            if shape != image_shape:
                analyzer = GestureAnalyzer(GestureConfig(
                    press_fraction=GESTO_ACTIVACION,
                    release_fraction=GESTO_LIBERACION,
                    min_travel=GESTO_RECORRIDO_MINIMO,
                    lateral_tolerance=GESTO_TOLERANCIA_LATERAL,
                    depth_weight=PESO_PROFUNDIDAD,
                    image_aspect_ratio=shape[1] / shape[0],
                ))
                image_shape = shape
                deadline = phase = None
                samples = []
                stabilizer.reset()
                message = "Pulsa C: calibra reposo y dedos levantados"

            # El detector recibe el original; solo la interfaz muestra un espejo.
            now = max(last_timestamp + 1, monotonic_ns() // 1_000_000)
            last_timestamp = now
            hands = tracker.detect(frame, now)
            if deadline is not None:
                if now >= deadline - CALIBRACION_MUESTREO_MS:
                    samples.append((now, hands))
                samples = [(t, h) for t, h in samples if t >= now - CALIBRACION_MUESTREO_MS]
                if now >= deadline:
                    capture = [h for _, h in samples]
                    save = analyzer.save_rest if phase == "reposo" else analyzer.save_raised
                    success = save(capture, CALIBRACION_MIN_MUESTRAS)
                    samples = []
                    stabilizer.reset()
                    if success and phase == "reposo":
                        phase = "levantados"
                        deadline = now + CALIBRACION_SEGUNDOS * 1000
                    else:
                        phase = deadline = None
                        message = analyzer.last_error

            fingers = invalid_state()
            counter = None
            if deadline is not None:
                counter = max(1, ceil((deadline - now) / 1000))
                instruction = "Dedos extendidos en reposo" if phase == "reposo" else "Levanta los dedos; palmas quietas"
                music = MusicState(reason=f"{instruction}: {counter} s")
            elif not analyzer.calibrated:
                music = MusicState(reason=message)
            else:
                raw = analyzer.analyze(hands)
                fingers = stabilizer.update(raw, now)
                music = engine.resolve(fingers)
                if not raw.valid:
                    music.reason = "Muestra ambas manos completas"
                elif not fingers.valid:
                    music.reason = "Estabilizando la deteccion"

            player.update(music)
            mostrar_pantalla(crear_pantalla(
                nota=music.note, octava=music.octave, estado=music.reason,
                frame=frame, hands=hands, fingers=fingers,
                calibrado=analyzer.calibrated, contador=counter,
            ))
            key = cv2.waitKey(ESPERA_MS) & 0xFF
            if key == TECLA_SALIR:
                break
            if key == TECLA_CALIBRAR:
                analyzer.reset()
                stabilizer.reset()
                phase = "reposo"
                deadline = now + CALIBRACION_SEGUNDOS * 1000
                samples = []
                player.update(MusicState(reason="Calibrando"))
            try:
                if cv2.getWindowProperty(NOMBRE_VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except cv2.error:
                break


if __name__ == "__main__":
    main()
