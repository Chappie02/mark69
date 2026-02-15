"""
Audio recording from USB microphone
Non-blocking with silence detection
"""

import logging
import threading
from typing import Optional
import queue

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("pyaudio not available - audio simulation mode")

from config import (
    AUDIO_SAMPLE_RATE, AUDIO_CHUNK_SIZE, AUDIO_CHANNELS,
    AUDIO_FORMAT, AUDIO_DEVICE_INDEX, MAX_RECORD_DURATION,
    RECORD_TIMEOUT
)

logger = logging.getLogger(__name__)

# =============================================
# AUDIO RECORDER
# =============================================
class AudioRecorder:
    """Records audio from USB microphone"""
    
    def __init__(self):
        """Initialize audio recorder"""
        self.audio: Optional[object] = None
        self.stream: Optional[object] = None
        self._recording = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        
        if PYAUDIO_AVAILABLE:
            self._init_audio()
        else:
            logger.warning("pyaudio not available - recording will not work")
    
    def _init_audio(self) -> None:
        """Initialize PyAudio"""
        try:
            self.audio = pyaudio.PyAudio()
            logger.info("✓ PyAudio initialized")
            
            # List available devices
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['max_input_channels'] > 0:
                    logger.debug(f"  Input {i}: {info['name']}")
        except Exception as e:
            logger.error(f"PyAudio initialization failed: {e}")
            raise
    
    def start_recording(self) -> None:
        """Start recording audio (non-blocking)"""
        if self._recording:
            logger.warning("Already recording")
            return
        
        self._recording = True
        self._audio_queue = queue.Queue()
        
        if self.audio and PYAUDIO_AVAILABLE:
            self._thread = threading.Thread(target=self._recording_thread, daemon=True)
            self._thread.start()
        else:
            logger.warning("[AUDIO SIM] Recording started")
    
    def stop_recording(self) -> Optional[bytes]:
        """
        Stop recording and return audio data
        
        Returns:
            Audio bytes or None if recording failed
        """
        self._recording = False
        
        if self._thread:
            self._thread.join(timeout=2)
        
        # Collect audio from queue
        audio_data = b""
        try:
            while True:
                chunk = self._audio_queue.get_nowait()
                audio_data += chunk
        except queue.Empty:
            pass
        
        if not audio_data:
            logger.warning("No audio recorded")
            return None
        
        logger.info(f"Recording stopped. Total bytes: {len(audio_data)}")
        return audio_data
    
    def _recording_thread(self) -> None:
        """Audio recording thread"""
        try:
            if not self.audio:
                return
            
            # Create audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=AUDIO_CHANNELS,
                rate=AUDIO_SAMPLE_RATE,
                input=True,
                frames_per_buffer=AUDIO_CHUNK_SIZE,
                input_device_index=AUDIO_DEVICE_INDEX,
                frames_per_buffer_cb=None
            )
            
            logger.info(f"Recording stream opened: {AUDIO_SAMPLE_RATE}Hz, {AUDIO_CHANNELS}ch")
            
            self.stream.start_stream()
            chunk_count = 0
            
            while self._recording:
                try:
                    data = self.stream.read(AUDIO_CHUNK_SIZE, exception_on_overflow=False)
                    self._audio_queue.put(data)
                    chunk_count += 1
                except Exception as e:
                    logger.error(f"Stream read error: {e}")
                    break
            
            self.stream.stop_stream()
            self.stream.close()
            logger.info(f"Recording thread finished. Chunks: {chunk_count}")
            
        except Exception as e:
            logger.error(f"Recording thread error: {e}", exc_info=True)
    
    def cleanup(self) -> None:
        """Cleanup audio"""
        self.stop_recording()
        if self.audio:
            try:
                self.audio.terminate()
                logger.info("✓ PyAudio terminated")
            except Exception as e:
                logger.error(f"PyAudio termination failed: {e}")
