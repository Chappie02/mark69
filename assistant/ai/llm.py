"""
Offline LLM via llama-cpp-python. Gemma 3 4B IT GGUF 4-bit.
Stream tokens; optimized for 4GB RAM.
"""

from pathlib import Path
from typing import Generator, Optional

from assistant.config import (
    LLM_MODEL_PATH,
    LLM_CONTEXT_SIZE,
    LLM_MAX_TOKENS,
    LLM_TEMP,
    LLM_TOP_P,
    LLM_N_THREADS,
)


class LLMEngine:
    """Load GGUF once; generate with stream."""

    def __init__(self) -> None:
        self._model = None
        self._loaded = False

    def load(self) -> bool:
        path = Path(LLM_MODEL_PATH)
        if not path.exists():
            return False
        try:
            from llama_cpp import Llama
            self._model = Llama(
                model_path=str(path),
                n_ctx=LLM_CONTEXT_SIZE,
                n_threads=LLM_N_THREADS,
                n_gpu_layers=0,  # CPU only for RPi
                verbose=False,
            )
            self._loaded = True
            return True
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = True,
    ) -> Generator[str, None, None] | str:
        if not self._loaded and not self.load():
            yield "" if stream else ""
            return
        full = ""
        if system_prompt:
            full = f"<start_of_turn>system\n{system_prompt}<end_of_turn>\n"
        full += f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        try:
            if stream:
                for chunk in self._model(
                    full,
                    max_tokens=LLM_MAX_TOKENS,
                    temperature=LLM_TEMP,
                    top_p=LLM_TOP_P,
                    stream=True,
                    stop=["<end_of_turn>", "<eos>"],
                ):
                    text = chunk.get("choices", [{}])[0].get("text", "")
                    if text:
                        yield text
            else:
                out = self._model(
                    full,
                    max_tokens=LLM_MAX_TOKENS,
                    temperature=LLM_TEMP,
                    top_p=LLM_TOP_P,
                    stream=False,
                    stop=["<end_of_turn>", "<eos>"],
                )
                text = out.get("choices", [{}])[0].get("text", "")
                yield text
        except Exception:
            if stream:
                yield ""
            else:
                yield ""
