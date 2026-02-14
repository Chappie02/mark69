"""
Offline Speech-to-Text using Vosk.
Records from default input (e.g. USB mic) and returns text.
"""

import json
import logging
import queue
import threading
from pathlib import Path
from typing import Optional

from assistant.config import (
    SAMPLE_RATE,
    VOSK_MODEL_PATH,
    RECORD_SECONDS_MAX,
    CHUNK_SIZE,
)

logger = logging.getLogger(__name__)


class SpeechToText:
    """Vosk-based offline STT. Records audio and returns transcribed text."""

    def __init__(self) -> None:
        self._model = None
        self._initialized = False

    def init(self) -> bool:
        """Load Vosk model. Returns True on success."""
        try:
            from vosk import Model

            path = Path(VOSK_MODEL_PATH)
            if not path.exists():
                logger.warning("Vosk model path does not exist: %s", path)
                return False
            self._model = Model(str(path))
            self._initialized = True
            logger.info("Vosk STT model loaded: %s", VOSK_MODEL_PATH)
            return True
        except Exception as e:
            logger.exception("Vosk STT init failed: %s", e)
            self._initialized = False
            return False

    def record_audio(self, duration_seconds: float = RECORD_SECONDS_MAX) -> Optional[bytes]:
        """Record raw PCM audio (16-bit mono, SAMPLE_RATE). Returns bytes or None."""
        try:
            import pyaudio
            import wave
            import io

            pa = pyaudio.PyAudio()
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )
            frames = []
            total_chunks = int(SAMPLE_RATE / CHUNK_SIZE * duration_seconds)
            for _ in range(total_chunks):
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    frames.append(data)
                except Exception:
                    break
            stream.stop_stream()
            stream.close()
            pa.terminate()
            return b"".join(frames)
        except Exception as e:
            logger.exception("Record audio failed: %s", e)
            return None

    def transcribe(self, audio_bytes: Optional[bytes] = None) -> str:
        """
        Transcribe audio. If audio_bytes is None, records first (blocking).
        Returns transcribed text (empty string on failure or silence).
        """
        if audio_bytes is None:
            audio_bytes = self.record_audio()
        if not audio_bytes:
            return ""

        if not self._initialized or self._model is None:
            logger.warning("Vosk not initialized")
            return ""

        try:
            from vosk import KaldiRecognizer

            rec = KaldiRecognizer(self._model, SAMPLE_RATE)
            rec.SetWords(True)
            # Process in chunks
            step = 4000
            for i in range(0, len(audio_bytes), step):
                chunk = audio_bytes[i : i + step]
                if rec.AcceptWaveform(chunk):
                    pass
            result = rec.FinalResult()
            obj = json.loads(result)
            text = (obj.get("text") or "").strip()
            return text
        except Exception as e:
            logger.exception("Transcribe failed: %s", e)
            return ""

    def listen_and_transcribe(self, duration_seconds: float = RECORD_SECONDS_MAX) -> str:
        """Convenience: record then transcribe. Blocking."""
        audio = self.record_audio(duration_seconds)
        return self.transcribe(audio)

    def cleanup(self) -> None:
        self._model = None
        self._initialized = False
        logger.info("STT cleanup done")
