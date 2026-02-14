"""Vision module: camera and YOLO detection."""

from .camera import CameraCapture
from .yolo_detect import YOLODetector

__all__ = ["CameraCapture", "YOLODetector"]
