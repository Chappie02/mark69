"""
Vision — YOLOv8 Object Detection using ultralytics.
"""

import logging
import os

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
YOLO_MODEL = os.path.join(MODELS_DIR, "yolo.pt")


class ObjectDetector:
    """YOLOv8 object detection on Pi Camera frames."""

    def __init__(self):
        self._model = None
        self._camera = None
        self._load_model()

    def _load_model(self):
        """Load the YOLOv8 model."""
        try:
            from ultralytics import YOLO

            if not os.path.exists(YOLO_MODEL):
                logger.error("YOLO model not found at %s", YOLO_MODEL)
                return

            self._model = YOLO(YOLO_MODEL)
            logger.info("YOLOv8 model loaded from %s", YOLO_MODEL)
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", e)

    def detect(self):
        """
        Capture an image and run object detection.

        Returns:
            List of detected label strings, or empty list on failure.
        """
        if self._model is None:
            logger.error("YOLO model not loaded — cannot detect")
            return []

        try:
            # Capture image from Pi Camera
            image = self._capture_image()
            if image is None:
                return []

            # Run inference (CPU)
            results = self._model(image, verbose=False)

            labels = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    label = result.names[class_id]
                    confidence = float(box.conf[0])
                    labels.append(label)
                    logger.info("Detected: %s (%.2f)", label, confidence)

            return labels

        except Exception as e:
            logger.error("Object detection failed: %s", e)
            return []

    def capture_image_to_file(self, save_path):
        """
        Capture an image and save it to a file.

        Args:
            save_path: Path where the image will be saved.

        Returns:
            True if successful, False otherwise.
        """
        try:
            image = self._capture_image()
            if image is None:
                return False

            from PIL import Image

            if not isinstance(image, Image.Image):
                image = Image.fromarray(image)

            image.save(save_path)
            logger.info("Image saved to %s", save_path)
            return True

        except Exception as e:
            logger.error("Image capture/save failed: %s", e)
            return False

    def _capture_image(self):
        """Capture a single frame from Pi Camera."""
        try:
            from picamera2 import Picamera2

            if self._camera is None:
                self._camera = Picamera2()
                config = self._camera.create_still_configuration(
                    main={"size": (640, 480)}
                )
                self._camera.configure(config)
                self._camera.start()
                # Allow camera to warm up
                import time
                time.sleep(0.5)

            frame = self._camera.capture_array()
            logger.debug("Camera frame captured: %s", frame.shape)
            return frame

        except Exception as e:
            logger.error("Camera capture failed: %s", e)
            return None

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
