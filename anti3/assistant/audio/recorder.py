"""
Audio Recorder — Captures audio from USB microphone using sounddevice.
"""

import logging
import os
import tempfile
import threading

import numpy as np

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1


class AudioRecorder:
    """Record audio from USB microphone."""

    def __init__(self):
        self._recording = False
        self._frames = []
        self._lock = threading.Lock()
        self._stream = None

    def start_recording(self):
        """Begin recording audio from the microphone."""
        try:
            import sounddevice as sd

            with self._lock:
                self._frames = []
                self._recording = True

            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning("Audio input status: %s", status)
                if self._recording:
                    self._frames.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                callback=callback,
            )
            self._stream.start()
            logger.info("Recording started")
        except Exception as e:
            logger.error("Failed to start recording: %s", e)
            self._recording = False

    def stop_recording(self):
        """Stop recording and return path to WAV file."""
        try:
            with self._lock:
                self._recording = False

            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

            if not self._frames:
                logger.warning("No audio frames captured")
                return None

            audio_data = np.concatenate(self._frames, axis=0)
            self._frames = []

            from scipy.io import wavfile

            tmp_path = os.path.join(tempfile.gettempdir(), "assistant_recording.wav")
            audio_int16 = (audio_data * 32767).astype(np.int16)
            wavfile.write(tmp_path, SAMPLE_RATE, audio_int16)

            logger.info("Recording saved: %s (%.1fs)", tmp_path, len(audio_data) / SAMPLE_RATE)
            return tmp_path

        except Exception as e:
            logger.error("Failed to stop recording: %s", e)
            return None
