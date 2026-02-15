"""
Central state machine. All state transitions happen only here.
States: IDLE, LISTENING, THINKING, DETECTING, SPEAKING, SUCCESS, ERROR.
"""

from enum import Enum
from threading import Lock
from typing import Callable, Optional

from .event_bus import EventBus, Event


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    DETECTING = "detecting"
    SPEAKING = "speaking"
    SUCCESS = "success"
    ERROR = "error"


class StateManager:
    """Single source of truth for assistant state. Thread-safe."""

    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
        self._state = State.IDLE
        self._lock = Lock()
        self._listeners: list[Callable[[State, State], None]] = []

    @property
    def state(self) -> State:
        with self._lock:
            return self._state

    def set_state(self, new_state: State, payload: Optional[dict] = None) -> None:
        """Transition to new state. Emits event and notifies listeners."""
        with self._lock:
            old = self._state
            if old == new_state:
                return
            self._state = new_state

        self._event_bus.emit(Event.STATE_CHANGED, {"old": old, "new": new_state, **(payload or {})})
        for cb in self._listeners:
            try:
                cb(old, new_state)
            except Exception:
                pass

    def add_listener(self, callback: Callable[[State, State], None]) -> None:
        self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[State, State], None]) -> None:
        if callback in self._listeners:
            self._listeners.remove(callback)
