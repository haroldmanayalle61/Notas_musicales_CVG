from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence

import numpy as np

try:
    from contracts import FingerState
except ImportError:
    @dataclass
    class FingerState:
        valid: bool = False
        left: List[bool] = field(default_factory=lambda: [False] * 5)
        right: List[bool] = field(default_factory=lambda: [False] * 5)

FINGER_NAMES = ("pulgar", "indice", "medio", "anular", "menique")

WRIST = 0
THUMB_IP, THUMB_TIP = 3, 4
INDEX_MCP, MIDDLE_MCP, PINKY_MCP = 5, 9, 17

FINGER_JOINTS = ((6, 8), (10, 12), (14, 16), (18, 20))


@dataclass(frozen=True)
class GestureConfig:
    finger_ratio: float = 1.10
    thumb_ratio: float = 1.10
    thumb_spread: float = 0.60
    min_palm_size: float = 1e-3


DEFAULT_CONFIG = GestureConfig()


def invalid_state() -> FingerState:
    return FingerState(valid=False, left=[False] * 5, right=[False] * 5)


def _get(obj: Any, name: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def _to_xy(points: Any) -> Optional[np.ndarray]:
    if points is None:
        return None
    try:
        arr = np.asarray(points, dtype=float)
    except (TypeError, ValueError):
        return None
    if arr.ndim != 2 or arr.shape[0] != 21 or arr.shape[1] < 2:
        return None
    arr = arr[:, :2]
    if not np.all(np.isfinite(arr)):
        return None
    return arr


def _dist(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def classify_hand(xy: np.ndarray, config: GestureConfig = DEFAULT_CONFIG
                  ) -> Optional[List[bool]]:
    if _dist(xy[WRIST], xy[MIDDLE_MCP]) < config.min_palm_size:
        return None
    palm_width = _dist(xy[INDEX_MCP], xy[PINKY_MCP])
    if palm_width < config.min_palm_size:
        return None

    tip_far = _dist(xy[THUMB_TIP], xy[PINKY_MCP])
    ip_far = _dist(xy[THUMB_IP], xy[PINKY_MCP])
    spread = _dist(xy[THUMB_TIP], xy[INDEX_MCP]) / palm_width
    thumb = (tip_far > ip_far * config.thumb_ratio) and (spread > config.thumb_spread)

    states = [bool(thumb)]

    for pip, tip in FINGER_JOINTS:
        d_tip = _dist(xy[tip], xy[WRIST])
        d_pip = _dist(xy[pip], xy[WRIST])
        states.append(bool(d_tip > d_pip * config.finger_ratio))
    return states


def analyze(hands: Optional[Sequence[Any]], config: GestureConfig = DEFAULT_CONFIG) -> FingerState:
    
    if not hands:
        return invalid_state()

    found = {}
    for hand in hands:
        side = _get(hand, "side")
        if side is None:
            return invalid_state()
        key = str(side).strip().lower()
        if key not in ("left", "right") or key in found:
            return invalid_state()
        xy = _to_xy(_get(hand, "points"))
        if xy is None:
            return invalid_state()
        found[key] = xy

    if "left" not in found or "right" not in found:
        return invalid_state()

    left = classify_hand(found["left"], config)
    right = classify_hand(found["right"], config)
    if left is None or right is None:
        return invalid_state()
    return FingerState(valid=True, left=left, right=right)