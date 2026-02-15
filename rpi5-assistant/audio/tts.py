"""
Text-to-Speech using pyttsx3 or espeak
Offline synthesis, plays through USB speaker
"""

import logging
from typing import Optional
import subprocess
import os

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available - TTS simulation mode")

from config import TTS_RATE, TTS_VOLUME, TTS_VOICE_INDEX, AUDIO_OUTPUT_DEVICE

logger = logging.getLogger(__name__)

# =============================================
# TEXT-TO-SPEECH
# =============================================
class TextToSpeech:
    """Converts text to speech using pyttsx3"""
    
    def __init__(self):
        """Initialize TTS engine"""
        self.engine: Optional[object] = None
        self.use_espeak = False
        
        if PYTTSX3_AVAILABLE:
            self._init_pyttsx3()
        else:
            # Try espeak as fallback
            if self._check_espeak():
                self.use_espeak = True
                logger.info("Using espeak for TTS")
            else:
                logger.warning("No TTS backend available - speech will not work")
    
    def _init_pyttsx3(self) -> None:
        """Initialize pyttsx3"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', TTS_RATE)
            self.engine.setProperty('volume', TTS_VOLUME)
            
            # Try to set voice
            voices = self.engine.getProperty('voices')
            if len(voices) > TTS_VOICE_INDEX:
                self.engine.setProperty('voice', voices[TTS_VOICE_INDEX].id)
            
            logger.info(f"✓ pyttsx3 initialized (rate={TTS_RATE}, volume={TTS_VOLUME})")
        except Exception as e:
            logger.error(f"pyttsx3 initialization failed: {e}")
            raise
    
    def _check_espeak(self) -> bool:
        """Check if espeak is available"""
        try:
            result = subprocess.run(['which', 'espeak'], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def speak(self, text: str) -> bool:
        """
        Speak text
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        try:
            if not text:
                logger.warning("Empty text for TTS")
                return False
            
            logger.info(f"Speaking: {text[:50]}...")
            
            if self.engine:
                # pyttsx3
                self.engine.say(text)
                self.engine.runAndWait()
                logger.info("Speech playback complete")
                return True
            
            elif self.use_espeak:
                # espeak fallback
                try:
                    subprocess.run(
                        ['espeak', '-s', str(TTS_RATE), text],
                        capture_output=True,
                        timeout=30
                    )
                    logger.info("Speech playback complete (espeak)")
                    return True
                except Exception as e:
                    logger.error(f"espeak failed: {e}")
                    return False
            
            else:
                logger.warning("[TTS SIM] Speaking: {text}")
                return True
                
        except Exception as e:
            logger.error(f"TTS failed: {e}", exc_info=True)
            return False
    
    def cleanup(self) -> None:
        """Cleanup TTS engine"""
        if self.engine:
            try:
                self.engine.stop()
                logger.info("✓ TTS engine stopped")
            except Exception as e:
                logger.error(f"TTS cleanup failed: {e}")
