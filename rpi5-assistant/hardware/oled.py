"""
SSD1306 OLED display driver (128x64, I2C)
Non-blocking status and animation display
"""

import logging
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

try:
    from luma.core.interface.serial import i2c
    from luma.oled.device import ssd1306
    LUMA_AVAILABLE = True
except ImportError:
    LUMA_AVAILABLE = False
    logging.warning("luma library not available - display simulation mode")

from config import OLED_ADDRESS, OLED_I2C_BUS, OLED_WIDTH, OLED_HEIGHT

logger = logging.getLogger(__name__)

# =============================================
# OLED DISPLAY MANAGER
# =============================================
class OLEDDisplay:
    """Controls SSD1306 OLED display"""
    
    def __init__(self):
        """Initialize OLED display"""
        self.device: Optional[object] = None
        self.width = OLED_WIDTH
        self.height = OLED_HEIGHT
        
        if LUMA_AVAILABLE:
            self._init_display()
        else:
            logger.warning("luma library not available - display will not work")
            self._show_startup_message()
    
    def _init_display(self) -> None:
        """Initialize hardware display connection"""
        try:
            serial = i2c(bus=OLED_I2C_BUS, address=OLED_ADDRESS)
            self.device = ssd1306(serial_interface=serial)
            self.clear()
            logger.info("✓ SSD1306 OLED initialized")
        except Exception as e:
            logger.error(f"OLED initialization failed: {e}")
            raise
    
    def _show_startup_message(self) -> None:
        """Show startup message in simulation mode"""
        logger.info("[OLED SIM] Initializing display...")
    
    def clear(self) -> None:
        """Clear display"""
        if self.device:
            self.device.clear()
        else:
            logger.debug("[OLED SIM] Clear display")
    
    def show_status(self, title: str, subtitle: str = "") -> None:
        """
        Display status message
        
        Args:
            title: Status title (top)
            subtitle: Status subtitle (bottom)
        """
        if self.device:
            self._render_status(title, subtitle)
        else:
            logger.info(f"[OLED SIM] Status: {title} | {subtitle}")
    
    def _render_status(self, title: str, subtitle: str) -> None:
        """Render status to display"""
        try:
            # Create image
            image = Image.new("1", (self.width, self.height), color=0)
            draw = ImageDraw.Draw(image)
            
            # Try to load font, fall back to default
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
                subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
            
            # Draw title
            draw.text((4, 8), title, fill=1, font=title_font)
            
            # Draw subtitle
            draw.text((4, 32), subtitle, fill=1, font=subtitle_font)
            
            # Display
            self.device.display(image)
        except Exception as e:
            logger.error(f"Failed to render status: {e}")
    
    def show_animation_frame(self, frame_data: Image.Image) -> None:
        """
        Display animation frame
        
        Args:
            frame_data: PIL Image to display
        """
        try:
            if self.device:
                # Convert to 1-bit
                frame_data = frame_data.convert("1")
                self.device.display(frame_data)
        except Exception as e:
            logger.error(f"Failed to show animation frame: {e}")
    
    def show_eyes(self, left_pupil: Tuple[int, int], right_pupil: Tuple[int, int]) -> None:
        """
        Display animated eyes
        
        Args:
            left_pupil: (x, y) position of left pupil
            right_pupil: (x, y) position of right pupil
        """
        try:
            image = Image.new("1", (self.width, self.height), color=0)
            draw = ImageDraw.Draw(image)
            
            # Eye parameters
            eye_radius = 6
            pupil_radius = 2
            
            # Left eye
            left_eye_x = 40
            left_eye_y = 32
            draw.ellipse([left_eye_x - eye_radius, left_eye_y - eye_radius,
                          left_eye_x + eye_radius, left_eye_y + eye_radius], outline=1)
            draw.ellipse([left_pupil[0] - pupil_radius, left_pupil[1] - pupil_radius,
                          left_pupil[0] + pupil_radius, left_pupil[1] + pupil_radius], fill=1)
            
            # Right eye
            right_eye_x = 88
            right_eye_y = 32
            draw.ellipse([right_eye_x - eye_radius, right_eye_y - eye_radius,
                          right_eye_x + eye_radius, right_eye_y + eye_radius], outline=1)
            draw.ellipse([right_pupil[0] - pupil_radius, right_pupil[1] - pupil_radius,
                          right_pupil[0] + pupil_radius, right_pupil[1] + pupil_radius], fill=1)
            
            # Display
            self.show_animation_frame(image)
        except Exception as e:
            logger.error(f"Failed to show eyes: {e}")
    
    def cleanup(self) -> None:
        """Cleanup display"""
        try:
            if self.device:
                self.clear()
                logger.info("✓ OLED display cleaned up")
        except Exception as e:
            logger.error(f"OLED cleanup failed: {e}")
