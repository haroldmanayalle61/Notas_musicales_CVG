import cv2

class Camera:
    def __init__(self, index: int = 0):
        self._capture = cv2.VideoCapture(index)

        # Si la cámara no se abre, paramos con error.
        if not self._capture.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara {index}.")

        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def read(self):
        """Devuelve un frame BGR, o None si la lectura falla."""
        success, frame = self._capture.read()

        # Si la lectura falla, devolvemos None para que el bucle se detenga.
        if not success or frame is None or frame.size == 0:
            return None
        return frame

    def close(self):
        """Libera la cámara. Se puede llamar más de una vez."""
        self._capture.release()