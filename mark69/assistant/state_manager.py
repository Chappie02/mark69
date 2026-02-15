"""
State machine for the robot assistant.
States drive OLED animation and button/LLM/vision behavior.
"""

import threading
from enum import Enum
from typing import Callable, Optional


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    DETECTING = "detecting"
    SUCCESS = "success"
    ERROR = "error"


class StateManager:
    """Thread-safe state manager with optional listeners."""

    def __init__(self) -> None:
        self._state = State.IDLE
        self._lock = threading.Lock()
        self._listeners: list[Callable[[State], None]] = []

    @property
    def state(self) -> State:
        with self._lock:
            return self._state

    def set_state(self, new_state: State) -> None:
        with self._lock:
            old = self._state
            self._state = new_state
        if old != new_state:
            for cb in self._listeners:
                try:
                    cb(new_state)
                except Exception:
                    pass

    def add_listener(self, callback: Callable[[State], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[State], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)

    def is_idle(self) -> bool:
        return self.state == State.IDLE

    def is_busy(self) -> bool:
        return self.state not in (State.IDLE, State.SUCCESS, State.ERROR)
