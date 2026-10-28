from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence
import numpy as np
from contracts import FingerState

FINGER_TIPS = (4, 8, 12, 16, 20)
FINGER_BASES = (2, 5, 9, 13, 17)


@dataclass(frozen=True)
class GestureConfig:
    press_fraction: float = 0.65
    release_fraction: float = 0.35
    min_travel: float = 0.08
    lateral_tolerance: float = 0.35
    depth_weight: float = 0.5
    image_aspect_ratio: float = 1.0

    def __post_init__(self):
        values = tuple(vars(self).values())
        if not all(np.isfinite(v) for v in values):
            raise ValueError("Los ajustes deben ser finitos")
        if not 0 <= self.release_fraction < self.press_fraction <= 1:
            raise ValueError("Los umbrales de liberacion y activacion no son validos")
        if min(self.min_travel, self.lateral_tolerance, self.image_aspect_ratio) <= 0 or self.depth_weight < 0:
            raise ValueError("Los ajustes de geometria no son validos")


def invalid_state():
    return FingerState()


def _get(obj, key):
    return obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)


def _collect(hands: Sequence[Any] | None, config: GestureConfig):
    """Coordenadas de cada punta relativas a una palma, sin su propio nudillo.

    Compensa traslacion, escala y giro en la imagen; no mide altura fisica.
    """
    if not hands:
        return None
    found = {}
    for hand in hands:
        side = str(_get(hand, "side")).lower()
        if side not in ("left", "right") or side in found:
            return None
        try:
            points = np.asarray(_get(hand, "points"), dtype=float).copy()
        except (TypeError, ValueError):
            return None
        if points.shape != (21, 3) or not np.isfinite(points).all():
            return None
        points[:, (0, 2)] *= config.image_aspect_ratio
        features = []
        for tip, own_base in zip(FINGER_TIPS, FINGER_BASES):
            anchors = [i for i in (5, 9, 13, 17) if i != own_base]
            across = points[anchors[-1], :2] - points[anchors[0], :2]
            span = np.linalg.norm(across)
            if span < 1e-5:
                return None
            width = span * 12 / (anchors[-1] - anchors[0])
            u = across / span
            v = np.array([-u[1], u[0]])
            if np.dot(points[anchors, :2].mean(axis=0) - points[0, :2], v) < 0:
                v = -v
            if abs(np.dot(points[anchors, :2].mean(axis=0) - points[0, :2], v)) < 1e-5:
                return None
            center = points[[0] + anchors].mean(axis=0)
            delta = (points[tip] - center) / width
            features.append((np.dot(delta[:2], u), np.dot(delta[:2], v), delta[2] * config.depth_weight))
        found[side] = np.asarray(features)
    return found if len(found) == 2 else None


class GestureAnalyzer:
    """Aprende dos poses: extendido en reposo y levantado activo.

    Una referencia por punta evita confundir extendido con levantado.
    La clasificacion necesita ambas manos y no detecta contacto con una mesa.
    """
    def __init__(self, config=GestureConfig()):
        self.config = config
        self.reset()

    def reset(self):
        self.rest = None
        self.raised = None
        self.last_error = "Pulsa C para calibrar los gestos"
        self._pressed = {s: np.zeros(5, dtype=bool) for s in ("left", "right")}
        self._armed = {s: np.zeros(5, dtype=bool) for s in ("left", "right")}

    @property
    def calibrated(self):
        return self.rest is not None and self.raised is not None

    def _capture(self, samples, min_samples):
        if not samples or _collect(samples[-1], self.config) is None:
            self.last_error = "Muestra ambas manos completas y repite C"
            return None
        captures = [_collect(h, self.config) for h in samples]
        captures = [c for c in captures if c is not None]
        if len(captures) < min_samples:
            self.last_error = "Faltan imagenes validas; repite C"
            return None
        result = {}
        noise = {}
        for side in ("left", "right"):
            batch = np.asarray([c[side] for c in captures])
            result[side] = np.median(batch, axis=0)
            noise[side] = np.quantile(np.linalg.norm(batch - result[side], axis=2), .8, axis=0)
        return result, noise

    def save_rest(self, samples, min_samples=5):
        self.reset()
        capture = self._capture(samples, min_samples)
        if capture is None:
            return False
        self.rest, self._rest_noise = capture
        return True

    def save_raised(self, samples, min_samples=5):
        self.raised = None
        if self.rest is None:
            self.last_error = "Primero guarda el reposo con C"
            return False
        capture = self._capture(samples, min_samples)
        if capture is None:
            return False
        raised, noise = capture
        names = ("pulgar", "indice", "medio", "anular", "menique")
        for side in ("left", "right"):
            travel = np.linalg.norm(raised[side] - self.rest[side], axis=1)
            bad = (travel < self.config.min_travel) | (travel <= 3 * np.maximum(noise[side], self._rest_noise[side]))
            if bad.any():
                label = "izquierdo" if side == "left" else "derecho"
                self.last_error = f"Repite C: levanta mas el {names[int(np.flatnonzero(bad)[0])]} {label}"
                return False
        self.raised = raised
        self.last_error = "Calibracion lista: baja los dedos al reposo"
        return True

    def analyze(self, hands):
        current = _collect(hands, self.config)
        if current is None or not self.calibrated:
            for side in self._pressed:
                self._pressed[side][:] = False
                self._armed[side][:] = False
            return invalid_state()
        output = {}
        for side in ("left", "right"):
            stroke = self.raised[side] - self.rest[side]
            delta = current[side] - self.rest[side]
            progress = np.sum(delta * stroke, axis=1) / np.sum(stroke * stroke, axis=1)
            lateral = np.linalg.norm(delta - progress[:, None] * stroke, axis=1)
            inside = lateral <= self.config.lateral_tolerance
            released = (progress <= self.config.release_fraction) & inside
            self._armed[side] |= released
            active = (progress >= self.config.press_fraction) & (progress <= 1.8) & inside
            held = (progress > self.config.release_fraction) & (progress <= 1.8) & inside
            pressed = np.where(self._pressed[side], held, self._armed[side] & active)
            self._armed[side][pressed] = False
            self._pressed[side] = pressed
            output[side] = [bool(v) for v in pressed]
        return FingerState(True, output["left"], output["right"])
