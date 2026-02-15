"""
Object detection with YOLOv8 (ultralytics). CPU inference.
Input: image path or numpy array from Picamera2.
Returns top detection label or None.
"""

from pathlib import Path
from typing import Optional

from assistant.config import YOLO_MODEL_PATH, YOLO_CONF_THRESH, YOLO_IOU_THRESH


class VisionEngine:
    """YOLOv8 detector. Load model once; detect from image."""

    def __init__(self) -> None:
        self._model = None
        self._loaded = False

    def load(self) -> bool:
        path = Path(YOLO_MODEL_PATH)
        if not path.exists():
            return False
        try:
            from ultralytics import YOLO
            self._model = YOLO(str(path))
            self._loaded = True
            return True
        except Exception:
            return False

    def detect_top(self, image_input) -> Optional[str]:
        """
        image_input: path (str/Path) or numpy array (HWC).
        Returns class name of highest-confidence detection, or None.
        """
        if not self._loaded and not self.load():
            return None
        try:
            results = self._model(
                image_input,
                conf=YOLO_CONF_THRESH,
                iou=YOLO_IOU_THRESH,
                verbose=False,
            )
            if not results or len(results) == 0:
                return None
            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return None
            # Top confidence
            confs = boxes.conf.cpu().numpy()
            classes = boxes.cls.cpu().numpy()
            idx = confs.argmax()
            class_id = int(classes[idx])
            names = results[0].names
            return names.get(class_id, "object")
        except Exception:
            return None
