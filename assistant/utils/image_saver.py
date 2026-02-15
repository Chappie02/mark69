"""
Save captured images to /images with timestamp.
"""

from datetime import datetime
from pathlib import Path

from assistant.config import IMAGES_DIR


def save_capture(image_array) -> Path:
    """
    image_array: numpy array (from Picamera2) or PIL Image.
    Returns path to saved file.
    """
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = IMAGES_DIR / f"capture_{stamp}.jpg"
    try:
        from PIL import Image
        if hasattr(image_array, "shape"):
            # numpy
            img = Image.fromarray(image_array)
        else:
            img = image_array
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(path, "JPEG", quality=90)
        return path
    except Exception:
        path = IMAGES_DIR / f"capture_{stamp}.png"
        try:
            from PIL import Image
            img = Image.fromarray(image_array) if hasattr(image_array, "shape") else image_array
            img.save(path, "PNG")
            return path
        except Exception:
            raise
