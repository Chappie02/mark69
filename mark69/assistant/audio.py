"""
Audio capture (USB microphone) and playback (USB speaker).
Offline-only; uses PyAudio for record/play.
"""

import io
import queue
import threading
import time
import wave

try:
    import pyaudio
    _PYAUDIO_AVAILABLE = True
except ImportError:
    _PYAUDIO_AVAILABLE = False

from .config import SAMPLE_RATE, CHANNELS, CHUNK_SIZE

# PyAudio format
if _PYAUDIO_AVAILABLE:
    PA_FORMAT = pyaudio.paInt16
else:
    PA_FORMAT = None


def record_while_pressed(
    stop_event: threading.Event,
    stream_callback=None,
) -> bytes:
    """
    Record from default input until stop_event is set.
    Returns WAV bytes (16-bit mono at SAMPLE_RATE).
    """
    if not _PYAUDIO_AVAILABLE:
        return b""
    pa = pyaudio.PyAudio()
    try:
        stream = pa.open(
            format=PA_FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )
    except Exception:
        return b""
    chunks = []
    try:
        while not stop_event.is_set():
            try:
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                chunks.append(data)
                if stream_callback:
                    stream_callback(data)
            except Exception:
                break
    finally:
        stream.stop_stream()
        stream.close()
    pa.terminate()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"".join(chunks))
    return buf.getvalue()


def play_wav_bytes(wav_bytes: bytes) -> None:
    """Play WAV bytes to default output (USB speaker)."""
    if not _PYAUDIO_AVAILABLE or not wav_bytes:
        return
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wav:
        pa = pyaudio.PyAudio()
        try:
            stream = pa.open(
                format=pa.get_format_from_width(wav.getsampwidth()),
                channels=wav.getnchannels(),
                rate=wav.getframerate(),
                output=True,
            )
            chunk = 1024
            data = wav.readframes(chunk)
            while data:
                stream.write(data)
                data = wav.readframes(chunk)
            stream.stop_stream()
            stream.close()
        finally:
            pa.terminate()


def play_wav_async(wav_bytes: bytes) -> threading.Thread:
    """Start playback in a background thread; returns the thread."""
    t = threading.Thread(target=play_wav_bytes, args=(wav_bytes,), daemon=True)
    t.start()
    return t
