"""
Offline text-to-speech. Prefer Piper; fallback to pyttsx3/espeak.
Returns WAV bytes for playback via audio.play_wav_bytes.
"""

import io
import os
import subprocess
import tempfile

from .config import PIPER_MODEL_PATH, PIPER_CONFIG_PATH, SAMPLE_RATE


def _piper_available() -> bool:
    return os.path.isfile(PIPER_MODEL_PATH) and os.path.isfile(PIPER_CONFIG_PATH)


def speak_piper(text: str) -> bytes:
    """Synthesize with Piper; returns WAV bytes or empty if failed."""
    if not text or not _piper_available():
        return b""
    try:
        # Piper CLI: echo "text" | piper --model ... --output_file -
        proc = subprocess.Popen(
            [
                "piper",
                "--model", PIPER_MODEL_PATH,
                "--config", PIPER_CONFIG_PATH,
                "--output_file", "-",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        out, _ = proc.communicate(input=text.encode("utf-8"), timeout=60)
        if proc.returncode == 0 and out:
            return out
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    return b""


def speak_pyttsx3(text: str) -> bytes:
    """Fallback: pyttsx3 to temp WAV file, then return bytes."""
    try:
        import pyttsx3
    except ImportError:
        return b""
    if not text:
        return b""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
        engine = pyttsx3.init()
        engine.save_to_file(text, path)
        engine.runAndWait()
        with open(path, "rb") as f:
            data = f.read()
        try:
            os.unlink(path)
        except Exception:
            pass
        return data
    except Exception:
        try:
            os.unlink(path)
        except Exception:
            pass
        return b""


def speak(text: str) -> bytes:
    """
    Convert text to speech offline. Returns WAV bytes.
    Tries Piper first, then pyttsx3.
    """
    if not text:
        return b""
    wav = speak_piper(text)
    if wav:
        return wav
    return speak_pyttsx3(text)
