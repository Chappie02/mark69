"""
Capture from Raspberry Pi Camera via Picamera2.
Returns numpy array (HWC) for YOLO or save.
"""

from typing import Optional

import numpy as np


class Camera:
    """Picamera2 wrapper. Capture single frame."""

    def __init__(self) -> None:
        self._camera = None
        self._configured = False

    def init(self) -> bool:
        try:
            from picamera2 import Picamera2
            self._camera = Picamera2()
            self._camera.configure(self._camera.create_preview_configuration(
                main={"size": (640, 480), "format": "RGB888"}
            ))
            self._camera.start()
            self._configured = True
            return True
        except Exception:
            self._camera = None
            return False

    def capture(self) -> Optional[np.ndarray]:
        if not self._configured and not self.init():
            return None
        try:
            return self._camera.capture_array()
        except Exception:
            return None

    def close(self) -> None:
        if self._camera is not None:
            try:
                self._camera.stop()
            except Exception:
                pass
            self._camera = None
        self._configured = False
