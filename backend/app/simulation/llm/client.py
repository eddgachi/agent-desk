"""
DeepSeek API client.

Uses httpx for async HTTP calls to the DeepSeek chat completions endpoint.
Includes retry logic, timeout handling, and structured output parsing.
"""

import json
import logging
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

# ── Defaults ───────────────────────────────────────────────

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 30.0
MAX_RETRIES = 2

# ── Pydantic-style tool/response schema for structured output ──
# We use JSON mode to request structured responses.

STRUCTURED_SYSTEM_PROMPT = (
    "You are an AI assistant in an office simulation. "
    "Respond in valid JSON format only, no markdown, no additional text. "
    "Follow the exact schema requested."
)


class DeepSeekClient:
    """Async HTTP client for the DeepSeek chat API."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEEPSEEK_BASE_URL,
        model: str = DEEPSEEK_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 512,
        response_format: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Send a chat completion request.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": ...}
            temperature: Sampling temperature (0.0–1.0)
            max_tokens: Maximum tokens in response
            response_format: e.g., {"type": "json_object"} for structured output

        Returns:
            Response text content, or None on failure.
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        last_exc = None
        for attempt in range(1 + MAX_RETRIES):
            try:
                response = await self._client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                choice = data["choices"][0]
                content = choice["message"]["content"]
                logger.debug(
                    "DeepSeek OK: %d tokens (attempt %d)",
                    data.get("usage", {}).get("total_tokens", 0),
                    attempt + 1,
                )
                return content

            except httpx.HTTPStatusError as exc:
                last_exc = exc
                logger.warning(
                    "DeepSeek HTTP error (attempt %d): %s",
                    attempt + 1,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    import asyncio

                    await asyncio.sleep(1.0 * (attempt + 1))
            except httpx.TimeoutException as exc:
                last_exc = exc
                logger.warning(
                    "DeepSeek timeout (attempt %d): %s",
                    attempt + 1,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    import asyncio

                    await asyncio.sleep(1.0 * (attempt + 1))
            except Exception as exc:
                last_exc = exc
                logger.error("DeepSeek unexpected error: %s", exc)
                break

        logger.error("DeepSeek failed after %d attempts", 1 + MAX_RETRIES)
        return None

    async def chat_structured(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> Optional[dict]:
        """
        Request structured JSON output from DeepSeek.
        Uses the json_object response format.

        Returns:
            Parsed dict, or None on failure.
        """
        # Prepend system instruction for JSON
        wrapped = []
        has_system = any(m["role"] == "system" for m in messages)
        if not has_system:
            wrapped.append({"role": "system", "content": STRUCTURED_SYSTEM_PROMPT})

        wrapped.extend(messages)

        content = await self.chat(
            messages=wrapped,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )

        if content is None:
            return None

        try:
            parsed = json.loads(content)
            return parsed
        except json.JSONDecodeError as exc:
            logger.error(
                "DeepSeek JSON parse error: %s\ncontent: %s", exc, content[:200]
            )
            return None

    async def close(self) -> None:
        await self._client.aclose()
