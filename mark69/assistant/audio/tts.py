"""
Offline Text-to-Speech.
Uses Piper when available; falls back to pyttsx3 if configured.
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from assistant.config import PIPER_MODEL_PATH, SAMPLE_RATE

logger = logging.getLogger(__name__)


class TextToSpeech:
    """Offline TTS via Piper (preferred) or pyttsx3."""

    def __init__(self) -> None:
        self._piper_path: Optional[Path] = None
        self._engine = None
        self._use_piper = True

    def init(self) -> bool:
        """Detect Piper or pyttsx3. Returns True if at least one works."""
        # Try Piper first (piper binary or piper-tts package)
        try:
            result = subprocess.run(
                ["which", "piper"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                self._piper_path = Path(result.stdout.strip())
                self._use_piper = True
                logger.info("TTS: using Piper at %s", self._piper_path)
                return True
        except Exception as e:
            logger.debug("Piper not in PATH: %s", e)

        try:
            import piper
            self._use_piper = True
            self._piper_path = None  # use Python api
            logger.info("TTS: using piper Python API")
            return True
        except ImportError:
            pass

        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._use_piper = False
            logger.info("TTS: using pyttsx3")
            return True
        except Exception as e:
            logger.warning("pyttsx3 init failed: %s", e)

        logger.warning("No TTS backend available")
        return False

    def speak(self, text: str) -> bool:
        """Speak text. Blocking. Returns True on success."""
        if not text.strip():
            return True

        if self._use_piper:
            return self._speak_piper(text)
        return self._speak_pyttsx3(text)

    def _speak_piper(self, text: str) -> bool:
        """Use Piper CLI or Python API to synthesize and play."""
        try:
            if self._piper_path and self._piper_path.exists():
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    wav_path = f.name
                # Find model: PIPER_MODEL_PATH may be dir or .onnx file
                model_path = Path(PIPER_MODEL_PATH)
                if model_path.is_dir():
                    # First .onnx in dir
                    onnx = next(model_path.glob("*.onnx"), None)
                    model = str(onnx) if onnx else str(model_path)
                else:
                    model = str(model_path)
                cmd = [
                    str(self._piper_path),
                    "--model", model,
                    "--output_file", wav_path,
                ]
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                proc.communicate(input=text, timeout=30)
                if proc.returncode != 0:
                    return False
                self._play_wav(wav_path)
                Path(wav_path).unlink(missing_ok=True)
                return True
            else:
                # Python piper API
                import piper
                voice = piper.Voice.load(PIPER_MODEL_PATH)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    wav_path = f.name
                voice.synthesize(text, f)
                f.flush()
                self._play_wav(wav_path)
                Path(wav_path).unlink(missing_ok=True)
                return True
        except Exception as e:
            logger.exception("Piper TTS failed: %s", e)
            return False

    def _play_wav(self, path: str) -> None:
        """Play WAV file (aplay or ffplay)."""
        for cmd in [["aplay", "-q", path], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path]]:
            try:
                subprocess.run(cmd, check=True, timeout=60)
                return
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        logger.warning("Could not play WAV: no aplay/ffplay")

    def _speak_pyttsx3(self, text: str) -> bool:
        try:
            if self._engine:
                self._engine.say(text)
                self._engine.runAndWait()
                return True
        except Exception as e:
            logger.exception("pyttsx3 speak failed: %s", e)
        return False

    def cleanup(self) -> None:
        if self._engine:
            try:
                self._engine.stop()
            except Exception:
                pass
            self._engine = None
        self._piper_path = None
        logger.info("TTS cleanup done")
