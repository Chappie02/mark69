"""
Text-to-Speech — Offline TTS using piper-tts.
"""

import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


class TextToSpeech:
    """Offline text-to-speech using piper-tts."""

    def __init__(self):
        self._model_path = None
        self._find_model()

    def _find_model(self):
        """Locate the Piper voice model."""
        try:
            piper_dir = os.path.join(MODELS_DIR, "piper")
            if os.path.isdir(piper_dir):
                for f in os.listdir(piper_dir):
                    if f.endswith(".onnx"):
                        self._model_path = os.path.join(piper_dir, f)
                        break

            if self._model_path:
                logger.info("Piper TTS model found: %s", self._model_path)
            else:
                logger.warning("No Piper TTS model found in %s", MODELS_DIR)
        except Exception as e:
            logger.error("Error finding TTS model: %s", e)

    def speak(self, text):
        """Convert text to speech and play through speaker."""
        if not text or not text.strip():
            return

        try:
            tmp_wav = os.path.join(tempfile.gettempdir(), "assistant_tts.wav")

            if not self._model_path:
                logger.error("No TTS model available")
                return

            proc = subprocess.run(
                ["piper", "--model", self._model_path, "--output_file", tmp_wav],
                input=text,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if proc.returncode != 0:
                logger.error("Piper TTS error: %s", proc.stderr)
                return

            self._play_audio(tmp_wav)

        except subprocess.TimeoutExpired:
            logger.error("TTS generation timed out")
        except Exception as e:
            logger.error("TTS speak failed: %s", e)

    def _play_audio(self, wav_path):
        """Play a WAV file through the default audio output."""
        try:
            subprocess.run(["aplay", "-q", wav_path], timeout=30, check=True)
        except FileNotFoundError:
            try:
                import sounddevice as sd
                from scipy.io import wavfile

                rate, data = wavfile.read(wav_path)
                sd.play(data, rate)
                sd.wait()
            except Exception as e:
                logger.error("Audio playback failed: %s", e)
        except subprocess.TimeoutExpired:
            logger.error("Audio playback timed out")
        except Exception as e:
            logger.error("aplay failed: %s", e)
