"""
Offline speech-to-text using Vosk (lightweight, runs on Pi).
Consumes WAV bytes; returns transcribed text.
"""

import io
import json
import os

from .config import SAMPLE_RATE, VOSK_MODEL_DIR

_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model
    try:
        from vosk import Model
    except ImportError:
        return None
    if not os.path.isdir(VOSK_MODEL_DIR):
        return None
    try:
        _model = Model(VOSK_MODEL_DIR)
        return _model
    except Exception:
        return None


def transcribe(wav_bytes: bytes) -> str:
    """
    Transcribe WAV bytes (16-bit mono, 16 kHz) to text.
    Returns empty string if no model or no speech detected.
    """
    model = _get_model()
    if model is None:
        return ""
    try:
        from vosk import KaldiRecognizer
    except ImportError:
        return ""
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(False)
    buf = io.BytesIO(wav_bytes)
    import wave
    with wave.open(buf, "rb") as wav:
        if wav.getframerate() != SAMPLE_RATE or wav.getnchannels() != 1:
            return ""
        while True:
            data = wav.readframes(4000)
            if len(data) == 0:
                break
            rec.AcceptWaveform(data)
    result = rec.FinalResult()
    try:
        obj = json.loads(result)
        return (obj.get("text") or "").strip()
    except Exception:
        return ""
