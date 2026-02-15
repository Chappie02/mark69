"""
Offline STT using Vosk. 16kHz mono PCM in, text out.
"""

from pathlib import Path
from typing import Optional

from assistant.config import VOSK_MODEL_PATH, SAMPLE_RATE


class STTEngine:
    """Vosk recognizer. Load model once; recognize from bytes."""

    def __init__(self) -> None:
        self._model = None
        self._recognizer = None

    def load(self) -> bool:
        model_path = Path(VOSK_MODEL_PATH)
        if not model_path.exists():
            return False
        try:
            from vosk import Model, KaldiRecognizer
            self._model = Model(str(model_path))
            self._recognizer = None  # create per recognition with sample rate
            return True
        except Exception:
            return False

    def transcribe(self, pcm_bytes: bytes) -> str:
        if self._model is None and not self.load():
            return ""
        try:
            from vosk import KaldiRecognizer
            rec = KaldiRecognizer(self._model, SAMPLE_RATE)
            rec.SetWords(False)
            # Feed in chunks (Vosk expects 4000ms chunks or so for best results)
            chunk_size = 4000 * 2  # 4000 ms at 16bit mono
            for i in range(0, len(pcm_bytes), chunk_size):
                chunk = pcm_bytes[i : i + chunk_size]
                if len(chunk) > 0:
                    rec.AcceptWaveform(chunk)
            result = rec.FinalResult()
            import json
            data = json.loads(result)
            return (data.get("text") or "").strip()
        except Exception:
            return ""
