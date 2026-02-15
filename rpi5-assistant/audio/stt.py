"""
Speech-to-Text using faster-whisper
Offline, CPU-based transcription
"""

import logging
from typing import Optional
import numpy as np
import io

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    logging.warning("faster-whisper not available - STT simulation mode")

from config import (
    STT_MODEL, STT_DEVICE, STT_COMPUTE_TYPE,
    AUDIO_SAMPLE_RATE
)

logger = logging.getLogger(__name__)

# =============================================
# SPEECH-TO-TEXT
# =============================================
class SpeechToText:
    """Converts audio to text using faster-whisper"""
    
    def __init__(self):
        """Initialize STT model"""
        self.model: Optional[object] = None
        
        if FASTER_WHISPER_AVAILABLE:
            self._init_model()
        else:
            logger.warning("faster-whisper not available - STT will not work")
    
    def _init_model(self) -> None:
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model: {STT_MODEL}...")
            self.model = WhisperModel(
                model_size_or_path=STT_MODEL,
                device=STT_DEVICE,
                compute_type=STT_COMPUTE_TYPE,
                local_files_only=True  # Offline mode
            )
            logger.info(f"✓ Whisper model loaded: {STT_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            logger.info("Make sure to download the model first:")
            logger.info(f"  from faster_whisper import WhisperModel")
            logger.info(f"  WhisperModel('{STT_MODEL}')")
            raise
    
    def transcribe(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio bytes to text
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM at 16kHz)
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            if not self.model:
                logger.error("Model not loaded")
                return None
            
            logger.info(f"Transcribing audio ({len(audio_data)} bytes)...")
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            segments, info = self.model.transcribe(
                audio_array,
                language="en",
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False
            )
            
            # Collect text
            text = ""
            for segment in segments:
                text += segment.text + " "
            
            text = text.strip()
            logger.info(f"Transcription complete: {text}")
            
            return text if text else None
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            return None
