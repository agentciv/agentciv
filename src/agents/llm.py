"""Provider-agnostic LLM wrapper for Agent Civilisation.

Thin async wrapper supporting:
  - "openai": OpenAI Python package
  - "anthropic": Anthropic Python package
  - "google": Google Generative AI (aiohttp fallback)
  - "local": OpenAI-compatible API at a custom base URL (ollama, vllm, etc.)

Handles rate limiting with exponential backoff (max 3 retries) and returns
a safe fallback on failure so the simulation never crashes.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from src.config import SimulationConfig

logger = logging.getLogger(__name__)

# Fallback response when the LLM call fails — must be a valid action
_FALLBACK_RESPONSE = "I will wait and observe."

# Exponential backoff parameters
_MAX_RETRIES = 3
_INITIAL_BACKOFF_SECONDS = 1.0
_CALL_TIMEOUT_SECONDS = 30.0


class LLMClient:
    """Async LLM client that abstracts away the provider."""

    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.provider = config.model_provider
        self.model = config.model_name
        self.max_tokens = config.llm_max_tokens
        self.temperature = config.llm_temperature

        # Read API key from the env var specified in config, with fallback
        self.api_key: str = os.environ.get(config.api_key_env_var, "") or ""

        # For local provider, read the custom base URL
        self.base_url: str = os.environ.get(
            "AGENT_CIV_API_BASE", "http://localhost:11434/v1"
        )

        # Lazily initialised provider clients
        self._openai_client: Optional[object] = None
        self._anthropic_client: Optional[object] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def call_llm(self, prompt: str) -> str:
        """Send a prompt to the configured LLM and return the response text.

        Retries with exponential backoff on rate-limit (429) errors.
        Returns a safe fallback string on unrecoverable failure.
        """
        backoff = _INITIAL_BACKOFF_SECONDS

        for attempt in range(_MAX_RETRIES + 1):
            try:
                match self.provider:
                    case "openai" | "local":
                        return await asyncio.wait_for(
                            self._call_openai(prompt), timeout=_CALL_TIMEOUT_SECONDS,
                        )
                    case "anthropic":
                        return await asyncio.wait_for(
                            self._call_anthropic(prompt), timeout=_CALL_TIMEOUT_SECONDS,
                        )
                    case "google":
                        return await asyncio.wait_for(
                            self._call_google(prompt), timeout=_CALL_TIMEOUT_SECONDS,
                        )
                    case _:
                        logger.error("Unknown LLM provider: %s", self.provider)
                        return _FALLBACK_RESPONSE

            except asyncio.TimeoutError:
                logger.warning(
                    "LLM call timed out after %.0fs (provider=%s, attempt=%d/%d)",
                    _CALL_TIMEOUT_SECONDS, self.provider, attempt + 1, _MAX_RETRIES + 1,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return _FALLBACK_RESPONSE

            except Exception as exc:
                exc_str = str(exc).lower()
                is_rate_limit = (
                    "429" in exc_str
                    or "rate" in exc_str
                    or "too many" in exc_str
                    or "quota" in exc_str
                )

                if is_rate_limit and attempt < _MAX_RETRIES:
                    logger.warning(
                        "Rate limited (attempt %d/%d). Backing off %.1fs.",
                        attempt + 1,
                        _MAX_RETRIES,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue

                # Log at warning level for import errors (no package installed),
                # error level for actual API failures
                if "package is required" in str(exc) or "ImportError" in type(exc).__name__:
                    if not getattr(self, "_import_warned", False):
                        logger.warning("LLM provider '%s' unavailable: %s", self.provider, exc)
                        self._import_warned = True
                else:
                    logger.error(
                        "LLM call failed (provider=%s, attempt=%d): %s",
                        self.provider, attempt + 1, exc,
                    )
                return _FALLBACK_RESPONSE

        return _FALLBACK_RESPONSE

    # ------------------------------------------------------------------
    # Provider implementations
    # ------------------------------------------------------------------

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI or OpenAI-compatible API (also used for 'local' provider)."""
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise ImportError(
                "The 'openai' package is required for the openai/local provider. "
                "Install it with: pip install openai"
            )

        if self._openai_client is None:
            kwargs: dict = {"api_key": self.api_key}
            if self.provider == "local":
                kwargs["base_url"] = self.base_url
            self._openai_client = AsyncOpenAI(**kwargs)

        client: AsyncOpenAI = self._openai_client  # type: ignore[assignment]
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        choice = response.choices[0]
        return choice.message.content or _FALLBACK_RESPONSE

    async def _call_anthropic(self, prompt: str) -> str:
        """Call the Anthropic Messages API."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required for the anthropic provider. "
                "Install it with: pip install anthropic"
            )

        if self._anthropic_client is None:
            # If api_key is empty, omit it so the SDK can discover from
            # ANTHROPIC_API_KEY env var automatically
            kwargs: dict = {}
            if self.api_key:
                kwargs["api_key"] = self.api_key
            self._anthropic_client = AsyncAnthropic(**kwargs)

        client: AsyncAnthropic = self._anthropic_client  # type: ignore[assignment]
        response = await client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        # Anthropic returns a list of content blocks
        if response.content:
            return response.content[0].text
        return _FALLBACK_RESPONSE

    async def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API via aiohttp (no SDK dependency required)."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError(
                "The 'aiohttp' package is required for the google provider. "
                "Install it with: pip install aiohttp"
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": self.temperature,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 429:
                    raise Exception("429 rate limit from Google API")
                if resp.status != 200:
                    body = await resp.text()
                    raise Exception(
                        f"Google API returned {resp.status}: {body[:300]}"
                    )
                data = await resp.json()

        # Parse the Gemini response
        try:
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", _FALLBACK_RESPONSE)
        except (KeyError, IndexError, TypeError):
            pass

        return _FALLBACK_RESPONSE
