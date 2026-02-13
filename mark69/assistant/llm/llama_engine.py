"""
Local LLM via llama.cpp server (HTTP).
Supports token streaming for OLED display.
"""

import json
import logging
from typing import Generator, Optional

from assistant.config import (
    LLAMA_CPP_SERVER_URL,
    LLAMA_CONTEXT_SIZE,
    LLAMA_MAX_TOKENS,
    LLAMA_TEMPERATURE,
)

logger = logging.getLogger(__name__)


class LlamaEngine:
    """llama.cpp HTTP API client with streaming."""

    def __init__(self) -> None:
        self._base_url = LLAMA_CPP_SERVER_URL.rstrip("/")
        self._initialized = True  # No model load here; server holds model

    def init(self) -> bool:
        """Check server reachability. Returns True if server responds."""
        try:
            import requests
            r = requests.get(f"{self._base_url}/health", timeout=5)
            if r.status_code == 200:
                logger.info("LLM server reachable: %s", self._base_url)
                return True
            # Some servers use / or /v1/models
            r = requests.get(self._base_url, timeout=5)
            logger.info("LLM server reachable: %s", self._base_url)
            return True
        except Exception as e:
            logger.warning("LLM server not reachable: %s", e)
            return False

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = LLAMA_MAX_TOKENS,
        temperature: float = LLAMA_TEMPERATURE,
        stream: bool = False,
    ) -> str:
        """
        Single completion. If stream=False, returns full response.
        If stream=True, returns empty string (use stream_tokens for streaming).
        """
        if stream:
            return ""
        chunks = list(
            self.stream_tokens(
                prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
        return "".join(chunks)

    def stream_tokens(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = LLAMA_MAX_TOKENS,
        temperature: float = LLAMA_TEMPERATURE,
    ) -> Generator[str, None, None]:
        """
        Stream completion tokens from llama.cpp server.
        Yields token strings; caller can update OLED and accumulate response.
        """
        try:
            import requests
            from sseclient import SSEClient
        except ImportError as e:
            logger.error("Missing requests or sseclient: %s", e)
            return

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "prompt": full_prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        url = f"{self._base_url}/completion"
        try:
            resp = requests.post(url, json=payload, stream=True, timeout=60)
            resp.raise_for_status()
        except Exception as e:
            logger.exception("LLM request failed: %s", e)
            return

        # Parse SSE or NDJSON
        content_type = resp.headers.get("Content-Type", "")
        if "text/event-stream" in content_type:
            client = SSEClient(resp)
            for event in client.events():
                if event.data and event.data.strip() != "[DONE]":
                    try:
                        data = json.loads(event.data)
                        token = data.get("content", "")
                        if token:
                            yield token
                    except json.JSONDecodeError:
                        pass
        else:
            # Some servers return plain NDJSON lines
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("content", data.get("token", ""))
                    if token:
                        yield token
                except json.JSONDecodeError:
                    pass

    def cleanup(self) -> None:
        self._initialized = False
        logger.info("LLM engine cleanup done")
