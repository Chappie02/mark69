"""
YOLOv8 object detection with Picamera2
CPU-based inference
"""

import logging
from typing import Optional, List, Dict, Any
import os
from datetime import datetime

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logging.warning("ultralytics not available - YOLO simulation mode")

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    logging.warning("picamera2 not available - camera simulation mode")

from config import (
    YOLO_MODEL, YOLO_CONFIDENCE_THRESHOLD, YOLO_IOU_THRESHOLD,
    YOLO_DEVICE, CAMERA_WIDTH, CAMERA_HEIGHT,
    IMAGES_DIR, MODELS_DIR
)

logger = logging.getLogger(__name__)

# =============================================
# YOLO DETECTOR
# =============================================
class YOLODetector:
    """YOLOv8 object detection with camera"""
    
    def __init__(self):
        """Initialize YOLO and camera"""
        self.model: Optional[object] = None
        self.camera: Optional[object] = None
        
        if YOLO_AVAILABLE:
            self._load_model()
        
        if PICAMERA_AVAILABLE:
            self._init_camera()
    
    def _load_model(self) -> None:
        """Load YOLOv8 model"""
        try:
            logger.info(f"Loading YOLO model: {YOLO_MODEL}...")
            self.model = YOLO(YOLO_MODEL)
            
            # Move to device
            self.model.to(YOLO_DEVICE)
            
            logger.info(f"✓ YOLO model loaded: {YOLO_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
    
    def _init_camera(self) -> None:
        """Initialize Picamera2"""
        try:
            logger.info("Initializing Picamera2...")
            self.camera = Picamera2()
            
            # Configure camera
            config = self.camera.create_preview_configuration(
                main={"size": (CAMERA_WIDTH, CAMERA_HEIGHT), "format": "RGB888"}
            )
            self.camera.configure(config)
            self.camera.start()
            
            logger.info(f"✓ Camera initialized: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            self.camera = None
    
    def capture_image(self) -> Optional[str]:
        """
        Capture image from camera
        
        Returns:
            Path to saved image or None
        """
        try:
            if not self.camera and not PICAMERA_AVAILABLE:
                logger.warning("[CAMERA SIM] Capturing image...")
                # Simulate with a placeholder filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = IMAGES_DIR / f"image_{timestamp}.jpg"
                path.parent.mkdir(parents=True, exist_ok=True)
                # Create dummy file
                path.touch()
                return str(path)
            
            if not self.camera:
                logger.error("Camera not initialized")
                return None
            
            # Capture frame
            logger.info("Capturing frame...")
            frame = self.camera.capture_array()
            
            # Save to disk
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"image_{timestamp}.jpg"
            filepath = IMAGES_DIR / filename
            
            # Convert RGB to BGR for cv2
            import cv2
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(filepath), frame_bgr)
            
            logger.info(f"Image saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Image capture failed: {e}", exc_info=True)
            return None
    
    def detect(self, image_path: str) -> List[Dict[str, Any]]:
        """
        Run YOLO detection on image
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detection dicts with keys: name, confidence, box
        """
        try:
            if not self.model and not YOLO_AVAILABLE:
                logger.warning("[YOLO SIM] Running detection...")
                return [{"name": "test_object", "confidence": 0.95}]
            
            if not self.model:
                logger.error("YOLO model not loaded")
                return []
            
            if not os.path.exists(image_path):
                logger.error(f"Image not found: {image_path}")
                return []
            
            logger.info(f"Running YOLO inference on {image_path}...")
            
            # Run inference
            results = self.model(
                image_path,
                conf=YOLO_CONFIDENCE_THRESHOLD,
                iou=YOLO_IOU_THRESHOLD,
                device=YOLO_DEVICE,
                verbose=False
            )
            
            # Parse detections
            detections = []
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls)
                    confidence = float(box.conf)
                    class_name = result.names[cls_id]
                    
                    detection = {
                        "name": class_name,
                        "confidence": confidence,
                        "box": {
                            "x1": float(box.xyxy[0][0]),
                            "y1": float(box.xyxy[0][1]),
                            "x2": float(box.xyxy[0][2]),
                            "y2": float(box.xyxy[0][3])
                        }
                    }
                    detections.append(detection)
                    logger.info(f"  Detected: {class_name} ({confidence:.2%})")
            
            logger.info(f"Detection complete: {len(detections)} objects")
            return detections
            
        except Exception as e:
            logger.error(f"Detection failed: {e}", exc_info=True)
            return []
    
    def get_detection_summary(self, image_path: str, detections: List[Dict]) -> str:
        """
        Generate text summary of detections for RAG storage
        
        Args:
            image_path: Path to image
            detections: List of detections
            
        Returns:
            Text summary
        """
        timestamp = datetime.now().isoformat()
        summary = f"[{timestamp}] Image: {os.path.basename(image_path)}\n"
        summary += "Detected objects:\n"
        
        for det in detections:
            name = det.get("name", "Unknown")
            conf = det.get("confidence", 0)
            summary += f"- {name} ({conf:.0%} confidence)\n"
        
        return summary
    
    def cleanup(self) -> None:
        """Cleanup camera"""
        try:
            if self.camera:
                self.camera.stop()
                logger.info("✓ Camera stopped")
        except Exception as e:
            logger.error(f"Camera cleanup failed: {e}")
