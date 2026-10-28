from __future__ import annotations

from typing import Optional, Tuple

from contracts import FingerState

from gestures import invalid_state


def _key(state: FingerState) -> Tuple:
    if not state.valid:
        return (False,)
    return (True, tuple(bool(v) for v in state.left), tuple(bool(v) for v in state.right))


def _copy(state: FingerState) -> FingerState:
    if not state.valid:
        return invalid_state()
    return FingerState(valid=True, left=[bool(v) for v in state.left],
                       right=[bool(v) for v in state.right])


class Stabilizer:
    def __init__(self, window_ms: int = 100) -> None:
        if window_ms < 0:
            raise ValueError("window_ms no puede ser negativo")
        self.window_ms = window_ms
        self.reset()

    def reset(self) -> None:
        self._stable: FingerState = invalid_state()
        self._candidate_key: Optional[Tuple] = None
        self._candidate: Optional[FingerState] = None
        self._since: int = 0
        self._last_ts: Optional[int] = None

    def update(self, state: FingerState, timestamp_ms: int) -> FingerState:
        if self._last_ts is not None and timestamp_ms <= self._last_ts:
            raise ValueError("timestamp_ms debe ser creciente")
        self._last_ts = timestamp_ms

        if not state.valid:
            self._stable = invalid_state()
            self._candidate_key = None
            self._candidate = None
            return invalid_state()

        key = _key(state)
        if key == _key(self._stable):
            self._candidate_key = None
            self._candidate = None
            return _copy(self._stable)

        if key != self._candidate_key:
            self._candidate_key = key
            self._candidate = _copy(state)
            self._since = timestamp_ms

        if timestamp_ms - self._since >= self.window_ms:
            self._stable = self._candidate
            self._candidate_key = None
            self._candidate = None
        return _copy(self._stable)