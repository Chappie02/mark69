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
        self._config_path = None
        self._find_model()

    def _find_model(self):
        """Locate the Piper voice model in the models directory."""
        try:
            piper_dir = os.path.join(MODELS_DIR, "piper")

            # Look for .onnx model file
            if os.path.isdir(piper_dir):
                for f in os.listdir(piper_dir):
                    if f.endswith(".onnx"):
                        self._model_path = os.path.join(piper_dir, f)
                        config = self._model_path + ".json"
                        if os.path.exists(config):
                            self._config_path = config
                        break

            if self._model_path:
                logger.info("Piper TTS model found: %s", self._model_path)
            else:
                logger.warning("No Piper TTS model found in %s", piper_dir)

        except Exception as e:
            logger.error("Error finding TTS model: %s", e)

    def speak(self, text):
        """
        Convert text to speech and play through speaker.

        Args:
            text: The text to speak aloud.
        """
        if not text or not text.strip():
            return

        try:
            # Generate WAV using piper CLI
            tmp_wav = os.path.join(tempfile.gettempdir(), "assistant_tts.wav")

            if self._model_path:
                # Use piper with local model
                cmd = [
                    "piper",
                    "--model", self._model_path,
                    "--output_file", tmp_wav,
                ]

                proc = subprocess.run(
                    cmd,
                    input=text,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if proc.returncode != 0:
                    logger.error("Piper TTS error: %s", proc.stderr)
                    return
            else:
                logger.error("No TTS model available")
                return

            # Play the audio file
            self._play_audio(tmp_wav)

        except subprocess.TimeoutExpired:
            logger.error("TTS generation timed out")
        except Exception as e:
            logger.error("TTS speak failed: %s", e)

    def _play_audio(self, wav_path):
        """Play a WAV file through the default audio output."""
        try:
            # Try aplay first (ALSA)
            subprocess.run(
                ["aplay", "-q", wav_path],
                timeout=30,
                check=True,
            )
        except FileNotFoundError:
            # Fallback: try using sounddevice
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
