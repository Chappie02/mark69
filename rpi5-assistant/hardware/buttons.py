"""
Button handling with event callbacks
Supports three buttons with active-LOW GPIO
"""

import logging
import threading
import time
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
    RPI_AVAILABLE = True
except ImportError:
    RPI_AVAILABLE = False
    logging.warning("RPi.GPIO not available - button simulation mode")

from config import (
    GPIO_MODE, BUTTON_K1, BUTTON_K2, BUTTON_K3,
    BUTTON_ACTIVE_LOW, BUTTON_POLL_INTERVAL
)

logger = logging.getLogger(__name__)

# =============================================
# BUTTON MANAGER
# =============================================
class ButtonManager:
    """Manages button input with debouncing"""
    
    def __init__(self, callback: Callable[[str, bool], None]):
        """
        Initialize button manager
        
        Args:
            callback: Function called on button state change: callback(button_name, pressed)
        """
        self.callback = callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._button_states = {"K1": False, "K2": False, "K3": False}
        self._debounce_time = 0.02  # 20ms debounce
        self._last_change_time = {"K1": 0, "K2": 0, "K3": 0}
        
        if RPI_AVAILABLE:
            self._init_gpio()
        else:
            logger.warning("RPi.GPIO not available - buttons will not work")
    
    def _init_gpio(self) -> None:
        """Initialize GPIO for buttons"""
        try:
            GPIO.setmode(GPIO.BCM if GPIO_MODE == "BCM" else GPIO.BOARD)
            GPIO.setwarnings(False)
            
            # Set up buttons as inputs with pull-up
            for pin in [BUTTON_K1, BUTTON_K2, BUTTON_K3]:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            logger.info("✓ GPIO buttons initialized")
        except Exception as e:
            logger.error(f"GPIO initialization failed: {e}")
            raise
    
    def _get_button_state(self, pin: int) -> bool:
        """
        Read button state
        
        Args:
            pin: GPIO pin number
            
        Returns:
            True if button pressed, False otherwise
        """
        if not RPI_AVAILABLE:
            return False
        
        try:
            state = GPIO.input(pin)
            # Invert if active LOW
            if BUTTON_ACTIVE_LOW:
                state = not state
            return state
        except Exception as e:
            logger.error(f"Failed to read GPIO {pin}: {e}")
            return False
    
    def start(self) -> None:
        """Start button polling thread"""
        if self._running:
            logger.warning("Button manager already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("Button polling thread started")
    
    def stop(self) -> None:
        """Stop button polling thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        
        # Cleanup GPIO
        if RPI_AVAILABLE:
            try:
                GPIO.cleanup()
            except Exception as e:
                logger.error(f"GPIO cleanup failed: {e}")
        
        logger.info("✓ Button manager stopped")
    
    def _poll_loop(self) -> None:
        """Main polling loop"""
        while self._running:
            try:
                self._poll_buttons()
                time.sleep(BUTTON_POLL_INTERVAL)
            except Exception as e:
                logger.error(f"Button polling error: {e}", exc_info=True)
                time.sleep(0.1)
    
    def _poll_buttons(self) -> None:
        """Poll all buttons and detect state changes"""
        current_time = time.time()
        button_pins = {"K1": BUTTON_K1, "K2": BUTTON_K2, "K3": BUTTON_K3}
        
        for button_name, pin in button_pins.items():
            # Read current state
            new_state = self._get_button_state(pin)
            old_state = self._button_states[button_name]
            
            # Check for state change with debounce
            if new_state != old_state:
                time_since_change = current_time - self._last_change_time[button_name]
                
                if time_since_change >= self._debounce_time:
                    # State change confirmed
                    self._button_states[button_name] = new_state
                    self._last_change_time[button_name] = current_time
                    
                    # Call callback
                    logger.debug(f"Button {button_name}: {new_state}")
                    self.callback(button_name, new_state)
    
    def get_state(self, button: str) -> bool:
        """Get current button state"""
        return self._button_states.get(button, False)
