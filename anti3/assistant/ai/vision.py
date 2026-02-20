"""
Vision — Camera capture and YOLOv8 object detection.
Uses system-installed picamera2 (not pip-installed).
"""

import logging
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

# Use system-installed picamera2
sys.path.append("/usr/lib/python3/dist-packages")

try:
    from picamera2 import Picamera2
except Exception:
    Picamera2 = None

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
YOLO_MODEL = os.path.join(MODELS_DIR, "yolo.pt")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "images")


class ObjectDetector:
    """Camera capture and YOLOv8 object detection."""

    def __init__(self):
        os.makedirs(IMAGE_DIR, exist_ok=True)

        self._camera = None
        try:
            if Picamera2 is None:
                raise RuntimeError("Picamera2 not available.")
            self._camera = Picamera2()
            self._camera.configure(self._camera.create_still_configuration())
            self._camera.start()
            logger.info("Pi Camera initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize camera: %s", e)
            self._camera = None

        self._model = None
        try:
            if YOLO is None:
                raise RuntimeError("ultralytics YOLO not available.")
            if not os.path.exists(YOLO_MODEL):
                raise RuntimeError(f"YOLO model not found at {YOLO_MODEL}")
            self._model = YOLO(YOLO_MODEL)
            logger.info("YOLOv8 model loaded from %s", YOLO_MODEL)
        except Exception as e:
            logger.exception("Failed to load YOLO model: %s", e)
            self._model = None

    def _capture_image(self) -> Optional[str]:
        """Capture an image and save to disk."""
        if self._camera is None:
            logger.error("Camera not available.")
            return None
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(IMAGE_DIR, f"capture_{ts}.jpg")
            self._camera.capture_file(path)
            logger.info("Captured image: %s", path)
            return path
        except Exception:
            logger.exception("Failed to capture image.")
            return None

    def capture_and_save_image(self) -> Optional[str]:
        """Feature 2 — Capture and save image only."""
        return self._capture_image()

    def detect_first_object(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Feature 1 — Capture image and run YOLO detection.
        Returns (image_path, first_label) or (None, None).
        """
        image_path = self._capture_image()
        if image_path is None:
            return None, None

        if self._model is None:
            logger.error("YOLO model not available.")
            return image_path, None

        try:
            logger.info("Running YOLO detection...")
            results = self._model(image_path, verbose=False)

            if not results:
                logger.info("YOLO returned no results.")
                return image_path, None

            r = results[0]
            if r.boxes is None or len(r.boxes) == 0:
                logger.info("No objects detected in image.")
                return image_path, None

            box = r.boxes[0]
            cls_idx = int(box.cls[0].item())
            label = r.names.get(cls_idx, str(cls_idx))
            logger.info("Detected object: %s", label)
            return image_path, label

        except Exception:
            logger.exception("YOLO detection failed.")
            return image_path, None

    def cleanup(self):
        """Release camera resources."""
        try:
            if self._camera:
                self._camera.stop()
                self._camera.close()
                self._camera = None
                logger.info("Camera released")
        except Exception as e:
            logger.error("Camera cleanup error: %s", e)
