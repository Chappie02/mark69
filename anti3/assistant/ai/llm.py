"""
LLM Chat — Offline LLM using llama-cpp-python with streaming.
"""

import glob
import logging
import os

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


class LLMChat:
    """Offline LLM chat using llama.cpp Python bindings."""

    def __init__(self):
        self._model = None
        self._load_model()

    def _load_model(self):
        """Load the first GGUF model found in models/."""
        try:
            from llama_cpp import Llama

            model_path = self._find_model()
            if not model_path:
                logger.error("No GGUF model found in %s", MODELS_DIR)
                return

            self._model = Llama(
                model_path=model_path,
                n_ctx=512,
                n_threads=4,
                n_gpu_layers=0,
                verbose=False,
            )
            logger.info("LLM model loaded from %s", model_path)

        except Exception as e:
            logger.error("Failed to load LLM model: %s", e)
            self._model = None

    def _find_model(self):
        """Find the first .gguf file in models/."""
        try:
            for pattern in [
                os.path.join(MODELS_DIR, "*.gguf"),
                os.path.join(MODELS_DIR, "**", "*.gguf"),
            ]:
                files = glob.glob(pattern, recursive=True)
                if files:
                    return files[0]
            return None
        except Exception as e:
            logger.error("Error finding GGUF model: %s", e)
            return None

    def chat(self, prompt):
        """Generate a response, yielding tokens one by one."""
        if self._model is None:
            logger.error("LLM model not loaded")
            yield "Sorry, the language model is not available."
            return

        try:
            formatted = f"User: {prompt}\nAssistant:"

            stream = self._model(
                formatted,
                max_tokens=256,
                temperature=0.7,
                top_p=0.9,
                stream=True,
                stop=["User:", "\n\n"],
            )

            for chunk in stream:
                token = chunk["choices"][0]["text"]
                if token:
                    yield token

        except Exception as e:
            logger.error("LLM chat failed: %s", e)
            yield "Sorry, an error occurred."
