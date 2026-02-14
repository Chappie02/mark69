"""
Local LLM via llama-cpp-python (in-process).
Loads a GGUF model and supports token streaming for OLED display.
"""

import logging
from pathlib import Path
from typing import Generator, Optional

from assistant.config import (
    LLAMA_MODEL_PATH,
    LLAMA_CONTEXT_SIZE,
    LLAMA_MAX_TOKENS,
    LLAMA_TEMPERATURE,
)

logger = logging.getLogger(__name__)


def _resolve_model_path(path: str) -> Optional[str]:
    """Resolve to a .gguf file path. If dir, use first .gguf found."""
    p = Path(path)
    if not p.exists():
        return None
    if p.is_file() and p.suffix.lower() == ".gguf":
        return str(p)
    if p.is_dir():
        for f in p.glob("*.gguf"):
            return str(f)
    return None


class LlamaEngine:
    """llama-cpp-python in-process LLM with streaming."""

    def __init__(self) -> None:
        self._llm = None
        self._initialized = False

    def init(self) -> bool:
        """Load GGUF model. Returns True on success."""
        model_path = _resolve_model_path(LLAMA_MODEL_PATH)
        if not model_path:
            logger.warning("LLM model not found at %s (expect .gguf file or dir)", LLAMA_MODEL_PATH)
            return False
        try:
            from llama_cpp import Llama

            self._llm = Llama(
                model_path=model_path,
                n_ctx=LLAMA_CONTEXT_SIZE,
                n_threads=2,  # Pi-friendly
                n_gpu_layers=-1,  # use GPU if available, else CPU
                verbose=False,
            )
            self._initialized = True
            logger.info("LLM loaded: %s", model_path)
            return True
        except Exception as e:
            logger.exception("LLM init failed: %s", e)
            self._initialized = False
            return False

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = LLAMA_MAX_TOKENS,
        temperature: float = LLAMA_TEMPERATURE,
        stream: bool = False,
    ) -> str:
        """Single completion. If stream=False, returns full response."""
        if stream:
            return "".join(
                self.stream_tokens(
                    prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            )
        if not self._initialized or self._llm is None:
            return ""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        try:
            out = self._llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False,
            )
            return (out.get("choices") or [{}])[0].get("text", "").strip()
        except Exception as e:
            logger.exception("LLM complete failed: %s", e)
            return ""

    def stream_tokens(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = LLAMA_MAX_TOKENS,
        temperature: float = LLAMA_TEMPERATURE,
    ) -> Generator[str, None, None]:
        """Stream completion tokens. Yields token strings for OLED updates."""
        if not self._initialized or self._llm is None:
            return
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        try:
            for chunk in self._llm(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            ):
                choices = chunk.get("choices")
                if not choices:
                    continue
                text = choices[0].get("text", "")
                if text:
                    yield text
        except Exception as e:
            logger.exception("LLM stream failed: %s", e)

    def cleanup(self) -> None:
        """Release model."""
        self._llm = None
        self._initialized = False
        logger.info("LLM engine cleanup done")
