"""
Offline TTS: Piper preferred, espeak fallback.
"""

from pathlib import Path
from typing import Optional

from assistant.config import PIPER_MODEL_PATH, TTS_RATE, TTS_VOLUME


class TTSEngine:
    """Speak text via Piper (wav then play) or espeak."""

    def __init__(self) -> None:
        self._piper_available = False
        self._piper_model_path: Optional[str] = None
        self._espeak_available = False

    def load(self) -> bool:
        # Try Piper: .onnx path or directory containing it
        model_path = Path(PIPER_MODEL_PATH)
        onnx_path = None
        if model_path.suffix == ".onnx" and model_path.exists():
            onnx_path = model_path
        elif model_path.exists():
            for name in ("model.onnx", "en_US-lessac-medium.onnx"):
                p = model_path / name
                if p.exists():
                    onnx_path = p
                    break
            if onnx_path is None:
                for f in model_path.glob("*.onnx"):
                    onnx_path = f
                    break
        if onnx_path is not None:
            self._piper_model_path = str(onnx_path)
            self._piper_available = True
        else:
            self._piper_available = False
        # Fallback espeak
        try:
            import subprocess
            subprocess.run(["which", "espeak"], capture_output=True, check=True)
            self._espeak_available = True
        except Exception:
            self._espeak_available = False
        return self._piper_available or self._espeak_available

    def speak(self, text: str) -> None:
        if not text.strip():
            return
        if not self._piper_available and not self._espeak_available:
            self.load()
        if self._piper_available and self._piper_model_path:
            self._speak_piper(text)
        elif self._espeak_available:
            self._speak_espeak(text)

    def _speak_piper(self, text: str) -> None:
        import os
        import subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            wav_path = f.name
        try:
            # Prefer Python API (piper-tts package)
            try:
                import piper
                voice = piper.PiperVoice.load(self._piper_model_path)
                voice.synthesize(text, wav_path)
            except Exception:
                # Fallback: piper CLI
                subprocess.run(
                    ["python3", "-m", "piper", "-m", self._piper_model_path, "-f", wav_path, "--", text],
                    capture_output=True,
                    timeout=30,
                    check=True,
                )
            subprocess.run(
                ["aplay", "-q", wav_path],
                capture_output=True,
                timeout=60,
            )
        except Exception:
            self._speak_espeak(text)
        finally:
            try:
                os.unlink(wav_path)
            except Exception:
                pass

    def _speak_espeak(self, text: str) -> None:
        try:
            import subprocess
            subprocess.run(
                ["espeak", "-s", str(TTS_RATE), text],
                capture_output=True,
                timeout=60,
            )
        except Exception:
            pass
