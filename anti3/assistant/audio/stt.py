"""
Speech-to-Text — Offline transcription using faster-whisper.
"""

import logging
import os

logger = logging.getLogger(__name__)

MODEL_SIZE = "tiny"  # Use "tiny" for Pi 5 4GB RAM; "base" also works
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

            # Check for local model first, otherwise download
            local_model = os.path.join(MODELS_DIR, f"whisper-{MODEL_SIZE}")
            if os.path.isdir(local_model):
                model_path = local_model
            else:
                model_path = MODEL_SIZE  # Will auto-download

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
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to WAV audio file.

        Returns:
            Transcribed text string, or empty string on failure.
        """
        if self._model is None:
            logger.error("Whisper model not loaded — cannot transcribe")
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
