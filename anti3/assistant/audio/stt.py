"""
Speech-to-Text — Offline transcription using faster-whisper.
"""

import logging
import os

logger = logging.getLogger(__name__)

MODEL_SIZE = "tiny"
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


class SpeechToText:
    """Offline speech-to-text using faster-whisper."""

    def __init__(self):
        self._model = None
        self._load_model()

    def _load_model(self):
        """Load the Whisper model."""
        try:
            from faster_whisper import WhisperModel

            local_model = os.path.join(MODELS_DIR, f"whisper-{MODEL_SIZE}")
            model_path = local_model if os.path.isdir(local_model) else MODEL_SIZE

            self._model = WhisperModel(
                model_path,
                device="cpu",
                compute_type="int8",
            )
            logger.info("Whisper model '%s' loaded successfully", MODEL_SIZE)
        except Exception as e:
            logger.error("Failed to load Whisper model: %s", e)
            self._model = None

    def transcribe(self, audio_path):
        """Transcribe audio file to text. Returns string or empty on failure."""
        if self._model is None:
            logger.error("Whisper model not loaded")
            return ""

        try:
            segments, info = self._model.transcribe(
                audio_path,
                beam_size=1,
                language="en",
                vad_filter=True,
            )

            text = " ".join(segment.text.strip() for segment in segments)
            logger.info("Transcribed: '%s'", text)
            return text.strip()

        except Exception as e:
            logger.error("Transcription failed: %s", e)
            return ""
