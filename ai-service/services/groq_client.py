from __future__ import annotations

import logging
import json
import os
import re
import time
from typing import Any

from groq import Groq, GroqError

logger = logging.getLogger(__name__)


class GroqServiceException(RuntimeError):
    pass


class GroqClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.groq.com/openai/v1",
        default_model: str | None = None,
        timeout_s: float = 30.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout_s = float(timeout_s)
        self._client = Groq(
            api_key=api_key,
            base_url=self._base_url,
            timeout=self._timeout_s,
        )

    @staticmethod
    def from_env() -> "GroqClient":
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        default_model = os.getenv("GROQ_MODEL", "").strip() or "llama-3.3-70b-versatile"
        timeout_s = float(os.getenv("GROQ_TIMEOUT_S", "30"))
        return GroqClient(
            api_key=api_key,
            base_url=base_url,
            default_model=default_model,
            timeout_s=timeout_s,
        )

    @staticmethod
    def parse_json_response(raw_content: str) -> dict[str, Any]:
        cleaned_content = re.sub(
            r"```(?:json)?\s*(.*?)\s*```",
            r"\1",
            raw_content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        cleaned_content = cleaned_content.strip()
        try:
            parsed = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from Groq response: %s", e)
            raise ValueError("Invalid JSON response from AI model") from e
        if not isinstance(parsed, dict):
            raise ValueError("AI model returned JSON, but not a JSON object.")
        return parsed

    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.3,
        top_p: float = 1.0,
        max_tokens: int = 512,
        response_format: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        resolved_model = (model or self._default_model or "").strip()
        if not resolved_model:
            raise ValueError(
                "Groq model is not set. Provide `model` in the request or set GROQ_MODEL."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": messages,
            "temperature": float(temperature),
            "top_p": float(top_p),
            "max_tokens": int(max_tokens),
        }
        if response_format:
            payload["response_format"] = response_format
        if extra:
            payload.update(extra)

        started = time.perf_counter()
        try:
            completion = self._client.chat.completions.create(**payload)
        except GroqError as e:
            raise GroqServiceException(f"Groq API error: {e}") from e

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        content = completion.choices[0].message.content or ""
        usage = getattr(completion, "usage", None)
        tokens_used = getattr(usage, "total_tokens", None) if usage else None
        info = {
            "model_used": getattr(completion, "model", resolved_model),
            "tokens_used": tokens_used,
            "response_time_ms": elapsed_ms,
            "raw": completion.model_dump(mode="json")
            if hasattr(completion, "model_dump")
            else None,
        }
        return str(content), info

    def list_models(self) -> list[dict[str, Any]]:
        try:
            models = self._client.models.list()
        except GroqError as e:
            raise GroqServiceException(f"Groq API error: {e}") from e

        data = getattr(models, "data", [])
        result: list[dict[str, Any]] = []
        for model in data:
            if hasattr(model, "model_dump"):
                result.append(model.model_dump(mode="json"))
            elif isinstance(model, dict):
                result.append(model)
        return result
