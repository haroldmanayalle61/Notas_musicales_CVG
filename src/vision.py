from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision as mp_vision

from contracts import HandObservation


class HandTracker:
    def __init__(self):
        # Ruta del modelo entrenado: models/hand_landmarker.task
        model_path = (
            Path(__file__).resolve().parent
            / "models"
            / "hand_landmarker.task"
        )

        model_data = model_path.read_bytes()

        # Configuración del detector: 2 manos, confianza mínima 0.5.
        options = mp_vision.HandLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_buffer=model_data),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.landmarker = mp_vision.HandLandmarker.create_from_options(options)


    def detect(self, frame_bgr, timestamp_ms):
        # MediaPipe entiende RGB; OpenCV entrega BGR.
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        result = self.landmarker.detect_for_video(image, timestamp_ms)

        hands = []

        for i in range(len(result.hand_landmarks)):
            landmarks = result.hand_landmarks[i]
            categories = result.handedness[i]

            side = categories[0].category_name

            points = [
                (float(point.x), float(point.y), float(point.z))
                for point in landmarks
            ]

            hands.append(HandObservation(side=side, points=points))

        return hands


    def close(self):
        # Libera el detector.
        self.landmarker.close()