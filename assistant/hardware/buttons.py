"""
Three-speed dial switch: K1 (PTT), K2 (Object Detection), K3 (Capture).
BCM: K1=17, K2=27, K3=22. Active LOW, pull_up=True.
Runs in dedicated thread; emits events to event_bus.
"""

import threading
from typing import Optional

from assistant.config import GPIO_K1_PTT, GPIO_K2_DETECT, GPIO_K3_CAPTURE
from assistant.core.event_bus import EventBus, Event


def _safe_button(pin: int, name: str):
    """Create Button only if gpiozero available (RPi)."""
    try:
        from gpiozero import Button
        return Button(pin, pull_up=True)
    except Exception:
        return None


class ButtonManager:
    """Listens to K1/K2/K3 and emits events. Non-blocking thread."""

    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._k1 = _safe_button(GPIO_K1_PTT, "K1")
        self._k2 = _safe_button(GPIO_K2_DETECT, "K2")
        self._k3 = _safe_button(GPIO_K3_CAPTURE, "K3")
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        if self._k1 is None:
            while not self._stop.wait(1.0):
                pass
            return
        # gpiozero when_active/when_deactivated run in their own thread
        self._k1.when_pressed = lambda: self._bus.emit(Event.K1_PRESSED, {})
        self._k1.when_released = lambda: self._bus.emit(Event.K1_RELEASED, {})
        self._k2.when_pressed = lambda: self._bus.emit(Event.K2_PRESSED, {})
        self._k3.when_pressed = lambda: self._bus.emit(Event.K3_PRESSED, {})
        while not self._stop.wait(0.5):
            pass
