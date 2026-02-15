"""
Simple in-process event bus for decoupling components.
Animation and hardware react to events; processing publishes them.
"""

from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, List


class Event(str, Enum):
    STATE_CHANGED = "state_changed"
    K1_PRESSED = "k1_pressed"
    K1_RELEASED = "k1_released"
    K2_PRESSED = "k2_pressed"
    K3_PRESSED = "k3_pressed"
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    STT_RESULT = "stt_result"
    LLM_START = "llm_start"
    LLM_TOKEN = "llm_token"
    LLM_END = "llm_end"
    TTS_START = "tts_start"
    TTS_END = "tts_end"
    DETECTION_START = "detection_start"
    DETECTION_RESULT = "detection_result"
    CAPTURE_SAVED = "capture_saved"


class EventBus:
    """Thread-safe pub/sub. Handlers run in caller thread."""

    def __init__(self):
        self._handlers: Dict[Event, List[Callable[[dict], None]]] = {
            e: [] for e in Event
        }
        self._lock = Lock()

    def subscribe(self, event: Event, handler: Callable[[dict], None]) -> None:
        with self._lock:
            self._handlers[event].append(handler)

    def unsubscribe(self, event: Event, handler: Callable[[dict], None]) -> None:
        with self._lock:
            if handler in self._handlers[event]:
                self._handlers[event].remove(handler)

    def emit(self, event: Event, data: dict[str, Any] | None = None) -> None:
        with self._lock:
            handlers = list(self._handlers[event])
        payload = data or {}
        for h in handlers:
            try:
                h(payload)
            except Exception:
                pass
