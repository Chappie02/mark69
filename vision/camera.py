"""
Camera capture using Picamera2.
Saves images to project images/ directory.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from assistant.config import IMAGES_DIR, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FRAMERATE

logger = logging.getLogger(__name__)


class CameraCapture:
    """Picamera2 wrapper for single image capture."""

    def __init__(self) -> None:
        self._camera = None
        self._initialized = False

    def init(self) -> bool:
        """Initialize Picamera2. Returns True on success."""
        try:
            from picamera2 import Picamera2

            self._camera = Picamera2()
            config = self._camera.create_still_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"},
                controls={"FrameRate": CAMERA_FRAMERATE},
            )
            self._camera.configure(config)
            self._camera.start()
            self._initialized = True
            logger.info("Picamera2 initialized %sx%s", CAMERA_WIDTH, CAMERA_HEIGHT)
            return True
        except Exception as e:
            logger.exception("Camera init failed: %s", e)
            self._initialized = False
            return False

    def capture(self, save_path: Optional[Path] = None) -> Optional[Path]:
        """
        Capture one frame and save as JPEG.
        If save_path is None, generates a timestamped path in IMAGES_DIR.
        Returns path to saved file or None on failure.
        """
        if not self._initialized or self._camera is None:
            logger.warning("Camera not initialized")
            return None
        try:
            if save_path is None:
                name = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
                save_path = IMAGES_DIR / name
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            self._camera.capture_file(str(save_path))
            logger.info("Captured image: %s", save_path)
            return save_path
        except Exception as e:
            logger.exception("Capture failed: %s", e)
            return None

    def capture_array(self) -> Optional[Tuple[any, Tuple[int, int]]]:
        """Capture and return (numpy array RGB, (width, height)). For YOLO."""
        if not self._initialized or self._camera is None:
            return None
        try:
            arr = self._camera.capture_array()
            if arr is not None:
                return (arr, (arr.shape[1], arr.shape[0]))
            return None
        except Exception as e:
            logger.exception("Capture array failed: %s", e)
            return None

    def cleanup(self) -> None:
        """Stop and release camera."""
        if self._camera is not None:
            try:
                self._camera.stop()
            except Exception:
                pass
            self._camera = None
        self._initialized = False
        logger.info("Camera cleanup done")
