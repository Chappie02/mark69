"""
YOLO object detection using ultralytics, optimized for Raspberry Pi 5.
Saves original and annotated images.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

from assistant.config import (
    YOLO_MODEL_PATH,
    YOLO_CONFIDENCE,
    YOLO_IOU_THRESHOLD,
    YOLO_IMAGE_SIZE,
    IMAGES_DIR,
)

logger = logging.getLogger(__name__)


class YOLODetector:
    """Ultralytics YOLO detector, Pi-optimized (nano model, small imgsz)."""

    def __init__(self) -> None:
        self._model = None
        self._initialized = False

    def init(self) -> bool:
        """Load YOLO model. Returns True on success."""
        try:
            from ultralytics import YOLO

            self._model = YOLO(YOLO_MODEL_PATH)
            self._initialized = True
            logger.info("YOLO model loaded: %s", YOLO_MODEL_PATH)
            return True
        except Exception as e:
            logger.exception("YOLO init failed: %s", e)
            self._initialized = False
            return False

    def detect(
        self,
        image_path: Path,
        save_annotated: bool = True,
        conf: float = YOLO_CONFIDENCE,
        iou: float = YOLO_IOU_THRESHOLD,
        imgsz: int = YOLO_IMAGE_SIZE,
    ) -> Tuple[List[str], Optional[Path]]:
        """
        Run detection on image at image_path.
        Returns (list of detected class labels, path to annotated image or None).
        Annotated image is saved beside original with _annotated suffix.
        """
        if not self._initialized or self._model is None:
            logger.warning("YOLO not initialized")
            return [], None

        image_path = Path(image_path)
        if not image_path.exists():
            logger.warning("Image not found: %s", image_path)
            return [], None

        try:
            results = self._model.predict(
                source=str(image_path),
                conf=conf,
                iou=iou,
                imgsz=imgsz,
                verbose=False,
                stream=False,
            )
            labels = []
            annotated_path = None

            for r in results:
                if r.boxes is not None:
                    for box in r.boxes:
                        cls_id = int(box.cls.item())
                        name = r.names[cls_id]
                        labels.append(name)
                if save_annotated and r.orig_img is not None:
                    ann = r.plot()
                    stem = image_path.stem
                    annotated_path = image_path.parent / f"{stem}_annotated.jpg"
                    import cv2
                    cv2.imwrite(str(annotated_path), ann)
                    break

            labels = list(dict.fromkeys(labels))  # unique, order preserved
            logger.info("YOLO detected: %s", labels)
            return labels, annotated_path
        except Exception as e:
            logger.exception("YOLO detect failed: %s", e)
            return [], None

    def cleanup(self) -> None:
        self._model = None
        self._initialized = False
        logger.info("YOLO cleanup done")
