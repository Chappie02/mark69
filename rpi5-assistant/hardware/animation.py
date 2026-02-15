"""
Continuous eye animation loop
Runs in dedicated thread, always active
5-second loop regardless of system state
"""

import logging
import threading
import time
import math
from typing import Optional

from core.state import app_state
from hardware.oled import OLEDDisplay
from config import (
    ANIMATION_LOOP_TIME, ANIMATION_FPS, ANIMATION_FRAME_TIME,
    EYE_CENTER_Y, EYE_LEFT_X, EYE_RIGHT_X, EYE_RADIUS, PUPIL_OFFSET_MAX
)

logger = logging.getLogger(__name__)

# =============================================
# ANIMATION ENGINE
# =============================================
class AnimationEngine:
    """Continuous eye animation in dedicated thread"""
    
    def __init__(self, oled: Optional[OLEDDisplay] = None):
        """
        Initialize animation engine
        
        Args:
            oled: OLEDDisplay instance (can be None for simulation)
        """
        self.oled = oled
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._frame = 0
        self._loop_time = 0.0
    
    def start(self) -> None:
        """Start animation thread"""
        if self._running:
            logger.warning("Animation already running")
            return
        
        self._running = True
        app_state.animation_running = True
        self._thread = threading.Thread(target=self._animation_loop, daemon=True)
        self._thread.start()
        logger.info("✓ Animation engine started")
    
    def stop(self) -> None:
        """Stop animation thread"""
        self._running = False
        app_state.animation_running = False
        
        if self._thread:
            self._thread.join(timeout=2)
        
        logger.info("✓ Animation stopped")
    
    def _animation_loop(self) -> None:
        """Main animation loop (runs in dedicated thread)"""
        loop_start = time.time()
        frame_count = 0
        
        while self._running:
            try:
                frame_start = time.time()
                
                # Calculate position in 5-second loop
                elapsed = time.time() - loop_start
                progress = (elapsed % ANIMATION_LOOP_TIME) / ANIMATION_LOOP_TIME
                
                # Get eye positions for this frame
                left_pupil, right_pupil = self._calculate_eye_positions(progress)
                
                # Render
                if self.oled:
                    self.oled.show_eyes(left_pupil, right_pupil)
                else:
                    logger.debug(f"[ANIM] Frame {frame_count}: L={left_pupil}, R={right_pupil}")
                
                # Update state (non-blocking)
                frame_count += 1
                app_state.set_animation_frame(frame_count)
                
                # Frame rate control
                frame_elapsed = time.time() - frame_start
                sleep_time = max(0, ANIMATION_FRAME_TIME - frame_elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Animation loop error: {e}", exc_info=True)
                time.sleep(0.05)
    
    def _calculate_eye_positions(self, progress: float) -> tuple:
        """
        Calculate pupil positions for given progress in loop
        
        5-second animation:
        - 0.0-0.2:  Eyes centered (1 sec)
        - 0.2-0.4:  Slow shift left (1 sec)
        - 0.4-0.6:  Return to center (1 sec)
        - 0.6-0.8:  Slow shift right (1 sec)
        - 0.8-1.0:  Blink/reset (1 sec)
        
        Args:
            progress: Position in loop (0.0 to 1.0)
            
        Returns:
            Tuple of (left_pupil, right_pupil) as (x, y) tuples
        """
        
        # Determine animation phase
        if progress < 0.2:  # Phase 1: Centered (1 sec)
            offset = 0
        elif progress < 0.4:  # Phase 2: Shift left (1 sec)
            phase_progress = (progress - 0.2) / 0.2
            offset = -math.sin(phase_progress * math.pi) * PUPIL_OFFSET_MAX
        elif progress < 0.6:  # Phase 3: Return center (1 sec)
            phase_progress = (progress - 0.4) / 0.2
            offset = -math.sin((1 - phase_progress) * math.pi) * PUPIL_OFFSET_MAX
        elif progress < 0.8:  # Phase 4: Shift right (1 sec)
            phase_progress = (progress - 0.6) / 0.2
            offset = math.sin(phase_progress * math.pi) * PUPIL_OFFSET_MAX
        else:  # Phase 5: Return center/blink (1 sec)
            phase_progress = (progress - 0.8) / 0.2
            # Blink effect: eyes half-close
            if phase_progress < 0.3:
                offset = math.sin(phase_progress * math.pi) * PUPIL_OFFSET_MAX
            else:
                offset = 0
        
        # Calculate pupil positions (constrained within eye circle)
        left_pupil = (
            EYE_LEFT_X + int(offset),
            EYE_CENTER_Y
        )
        right_pupil = (
            EYE_RIGHT_X + int(offset),
            EYE_CENTER_Y
        )
        
        return left_pupil, right_pupil
