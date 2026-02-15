"""
Record from USB microphone. Returns raw PCM for Vosk (16kHz mono).
Non-blocking: start/stop from button thread; processing elsewhere.
"""

import io
import queue
import threading
from typing import Optional

from assistant.config import SAMPLE_RATE, RECORD_CHANNELS


class AudioRecorder:
    """Records to an internal buffer; get_audio() returns bytes."""

    def __init__(self) -> None:
        self._stream = None
        self._chunks: list[bytes] = []
        self._lock = threading.Lock()
        self._recording = False

    def _init_stream(self) -> bool:
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            self._stream = pa.open(
                format=pyaudio.paInt16,
                channels=RECORD_CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=1024,
            )
            return True
        except Exception:
            return False

    def start(self) -> bool:
        with self._lock:
            if self._recording:
                return True
            if self._stream is None and not self._init_stream():
                return False
            self._chunks = []
            self._recording = True
        return True

    def stop(self) -> Optional[bytes]:
        with self._lock:
            self._recording = False
        if not self._chunks:
            return None
        return b"".join(self._chunks)

    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def run_capture_loop(self) -> None:
        """Call in a thread while recording; appends chunks. Exit when not recording."""
        try:
            import pyaudio
        except ImportError:
            return
        while True:
            with self._lock:
                if not self._recording or self._stream is None:
                    break
                stream = self._stream
            try:
                data = stream.read(1024, exception_on_overflow=False)
                with self._lock:
                    if self._recording:
                        self._chunks.append(data)
            except Exception:
                break

    def close(self) -> None:
        with self._lock:
            self._recording = False
            if self._stream is not None:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None
