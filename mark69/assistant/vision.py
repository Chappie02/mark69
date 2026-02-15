"""
Vision: Picamera2 capture + YOLOv8 object detection (CPU).
Returns list of detected class labels; handles no-detection gracefully.
"""

import os
from typing import Any, List, Optional, Tuple

from .config import YOLO_MODEL_PATH, YOLO_CONFIDENCE, CAMERA_RESOLUTION, CAMERA_FRAMERATE

_camera = None
_yolo_model = None


def _get_camera():
    global _camera
    if _camera is not None:
        return _camera
    try:
        from picamera2 import Picamera2
        _camera = Picamera2()
        config = _camera.create_preview_configuration(
            main={"size": CAMERA_RESOLUTION, "format": "RGB888"}
        )
        _camera.configure(config)
        _camera.start()
        return _camera
    except Exception:
        return None


def _get_yolo():
    global _yolo_model
    if _yolo_model is not None:
        return _yolo_model
    try:
        from ultralytics import YOLO
        path = YOLO_MODEL_PATH
        if not os.path.isfile(path):
            # Let YOLO download yolov8n.pt on first use
            path = "yolov8n.pt"
        _yolo_model = YOLO(path)
        return _yolo_model
    except Exception:
        return None


def capture_image_as_array():
    """Capture one frame; returns numpy array (H, W, 3) or None."""
    cam = _get_camera()
    if cam is None:
        return None
    try:
        return cam.capture_array()
    except Exception:
        return None


def detect_objects(image_array: Any) -> List[str]:
    """
    Run YOLOv8 on image array (H, W, 3). Returns list of detected class names.
    Empty list if no detections or error.
    """
    model = _get_yolo()
    if model is None or image_array is None:
        return []
    try:
        results = model(image_array, conf=YOLO_CONFIDENCE, verbose=False)
        labels = []
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    name = model.names.get(cls_id, f"class_{cls_id}")
                    if name and name not in labels:
                        labels.append(name)
        return labels
    except Exception:
        return []


def capture_and_detect() -> Tuple[Optional[Any], List[str]]:
    """
    Capture one frame and run detection.
    Returns (image_array_or_none, list_of_class_names).
    """
    img = capture_image_as_array()
    if img is None:
        return None, []
    labels = detect_objects(img)
    return img, labels


def save_image(image_array: Any, directory: str, prefix: str = "capture") -> Optional[str]:
    """Save image to directory with timestamp; returns path or None."""
    if image_array is None:
        return None
    try:
        from datetime import datetime
        from PIL import Image
        import numpy as np
        os.makedirs(directory, exist_ok=True)
        name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        path = os.path.join(directory, name)
        Image.fromarray(image_array).save(path)
        return path
    except Exception:
        return None


def stop_camera() -> None:
    global _camera
    if _camera is not None:
        try:
            _camera.stop()
        except Exception:
            pass
        _camera = None
