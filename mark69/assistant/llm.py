"""
Local LLM via llama-cpp-python (llama.cpp).
Streaming generation; optimized for 4GB RAM, CPU-only on Pi.
"""

import os
from typing import Iterator, Optional

from .config import (
    LLAMA_MODEL_PATH,
    LLAMA_CTX,
    LLAMA_N_THREADS,
    LLAMA_N_GPU_LAYERS,
    LLAMA_TEMP,
    LLAMA_MAX_TOKENS,
    LLM_SYSTEM_PROMPT,
)

_llm = None


def _get_llm():
    global _llm
    if _llm is not None:
        return _llm
    if not os.path.isfile(LLAMA_MODEL_PATH):
        return None
    try:
        from llama_cpp import Llama
        _llm = Llama(
            model_path=LLAMA_MODEL_PATH,
            n_ctx=LLAMA_CTX,
            n_threads=LLAMA_N_THREADS,
            n_gpu_layers=LLAMA_N_GPU_LAYERS,
        )
        return _llm
    except Exception:
        return None


def generate(
    user_text: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = LLAMA_MAX_TOKENS,
) -> Iterator[str]:
    """
    Stream token-by-token response. Yields text chunks.
    Does not include system prompt in output.
    """
    llm = _get_llm()
    if llm is None:
        return
    system = system_prompt or LLM_SYSTEM_PROMPT
    prompt = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user_text}<|im_end|>\n<|im_start|>assistant\n"
    try:
        stream = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=LLAMA_TEMP,
            stream=True,
            stop=["<|im_end|>", "<|im_start|>"],
        )
        for chunk in stream:
            piece = chunk.get("choices", [{}])[0].get("text", "")
            if piece:
                yield piece
    except Exception:
        pass


def generate_full(user_text: str, system_prompt: Optional[str] = None, max_tokens: int = LLAMA_MAX_TOKENS) -> str:
    """Return full response as a single string."""
    return "".join(generate(user_text, system_prompt=system_prompt, max_tokens=max_tokens))
