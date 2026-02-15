"""
Main application entry point
Orchestrates all subsystems with threading
"""

import logging
import time
import signal
import sys
from pathlib import Path

from config import LOG_LEVEL, LOG_FILE, PROJECT_ROOT
from core.controller import Controller
from core.state import app_state, SystemState
from hardware.animation import AnimationEngine

# =============================================
# LOGGER SETUP
# =============================================
def setup_logging() -> None:
    """Configure logging"""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Create logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    try:
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not create log file: {e}")

# =============================================
# MAIN APPLICATION
# =============================================
class MultimodalAssistant:
    """Main application class"""
    
    def __init__(self):
        """Initialize application"""
        self.controller: Controller = None
        self.animation: AnimationEngine = None
        self._running = False
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """
        Initialize all subsystems
        
        Returns:
            True if successful
        """
        try:
            self.logger.info("=" * 60)
            self.logger.info("RPi5 Multimodal AI Assistant")
            self.logger.info("=" * 60)
            
            # Initialize controller
            self.controller = Controller()
            if not self.controller.initialize():
                self.logger.error("Failed to initialize controller")
                return False
            
            # Initialize animation
            self.animation = AnimationEngine(self.controller.oled)
            self.animation.start()
            
            # Start button manager
            if self.controller.button_manager:
                self.controller.button_manager.start()
            
            self.logger.info("✓ All subsystems ready!")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {e}", exc_info=True)
            return False
    
    def run(self) -> None:
        """Run main event loop"""
        self._running = True
        self.logger.info("Starting main event loop...")
        self.logger.info("Press Ctrl+C to stop")
        
        loop_count = 0
        
        try:
            while self._running:
                try:
                    # Process controller events
                    self.controller.run_event_loop()
                    
                    # Small sleep to prevent CPU spinning
                    time.sleep(0.1)
                    
                    # Periodic status
                    loop_count += 1
                    if loop_count % 50 == 0:  # Every ~5 seconds
                        state = app_state.get_system_state()
                        self.logger.debug(f"Loop alive. State: {state.value}")
                
                except Exception as e:
                    self.logger.error(f"Event loop error: {e}", exc_info=True)
                    time.sleep(0.5)
        
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Gracefully shutdown all subsystems"""
        self.logger.info("Shutting down application...")
        self._running = False
        
        # Stop animation
        if self.animation:
            self.animation.stop()
        
        # Shutdown controller
        if self.controller:
            self.controller.shutdown()
        
        self.logger.info("=" * 60)
        self.logger.info("✓ Application shutdown complete")
        self.logger.info("=" * 60)

# =============================================
# SIGNAL HANDLERS
# =============================================
def signal_handler(sig, frame):
    """Handle signals gracefully"""
    logging.getLogger(__name__).info(f"Signal {sig} received")
    sys.exit(0)

# =============================================
# ENTRY POINT
# =============================================
def main():
    """Main entry point"""
    # Setup logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run application
    app = MultimodalAssistant()
    
    if app.initialize():
        try:
            app.run()
        except KeyboardInterrupt:
            pass
        finally:
            app.shutdown()
    else:
        logger.error("Failed to initialize application")
        sys.exit(1)

if __name__ == "__main__":
    main()
