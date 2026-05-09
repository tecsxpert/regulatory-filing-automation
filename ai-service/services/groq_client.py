"""
GroqClient — AI Developer 2 core responsibility
Handles all Groq API calls with:
  - 3-retry exponential backoff
  - Error logging
  - Fallback template responses
  - Response time tracking
  - Token usage tracking
"""

import os
import time
import logging
import json
from groq import Groq, RateLimitError, APIStatusError, APIConnectionError

logger = logging.getLogger(__name__)

# Fallback templates returned when Groq is unavailable
FALLBACK_TEMPLATES = {
    "describe": {
        "description": "This regulatory filing requires review. AI analysis is temporarily unavailable. Please review manually.",
        "key_points": ["Manual review required", "AI service temporarily unavailable"],
        "summary": "Automated analysis unavailable. Please consult your compliance officer.",
        "is_fallback": True,
    },
    "categorise": {
        "category": "UNCATEGORIZED",
        "confidence": 0.0,
        "reasoning": "AI categorisation temporarily unavailable. Please categorise manually.",
        "is_fallback": True,
    },
    "recommend": {
        "recommendations": [
            {
                "action_type": "MANUAL_REVIEW",
                "description": "AI recommendations temporarily unavailable. Conduct manual compliance review.",
                "priority": "HIGH",
            }
        ],
        "is_fallback": True,
    },
    "generate_report": {
        "title": "Regulatory Filing Report",
        "executive_summary": "AI report generation temporarily unavailable.",
        "overview": "Please retry after a few minutes or contact your compliance officer.",
        "top_items": [],
        "recommendations": ["Retry AI report generation", "Manual review recommended"],
        "is_fallback": True,
    },
    "query": {
        "answer": "AI knowledge base is temporarily unavailable. Please consult your compliance documentation directly.",
        "sources": [],
        "is_fallback": True,
    },
    "analyse_document": {
        "insights": [],
        "risks": [],
        "summary": "Document analysis temporarily unavailable.",
        "is_fallback": True,
    },
    "default": {
        "result": "AI processing temporarily unavailable. Please retry in a few minutes.",
        "is_fallback": True,
    },
}

# Registry for tracking response times (last 10 calls)
_response_times: list[float] = []
_cache_hits: int = 0
_cache_misses: int = 0


def record_response_time(ms: float):
    global _response_times
    _response_times.append(ms)
    if len(_response_times) > 10:
        _response_times = _response_times[-10:]


def increment_cache_hit():
    global _cache_hits
    _cache_hits += 1


def increment_cache_miss():
    global _cache_misses
    _cache_misses += 1


def get_stats() -> dict:
    avg = round(sum(_response_times) / len(_response_times), 2) if _response_times else 0
    return {
        "avg_response_time_ms": avg,
        "last_10_response_times_ms": [round(t, 2) for t in _response_times],
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
    }


class GroqClient:
    """
    Singleton-style Groq API client.
    All AI calls go through call_groq().
    """

    MODEL = "llama-3.3-70b-versatile"
    MAX_RETRIES = 3
    BASE_DELAY = 1.0  # seconds, doubles each retry

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            self.client = None
            logger.info(
                "GROQ_API_KEY environment variable not set. AI calls will use fallback responses."
            )
            return
        self.client = Groq(api_key=api_key)
        logger.info("GroqClient initialised with model %s", self.MODEL)

    def call_groq(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 1000,
        response_format: dict | None = None,
        fallback_key: str = "default",
    ) -> dict:
        """
        Call Groq with automatic retry and fallback.

        Returns:
            dict with keys:
              - content (str): raw text response
              - tokens_used (int)
              - response_time_ms (float)
              - model_used (str)
              - is_fallback (bool)
        """
        if self.client is None:
            logger.info(
                "Groq client is not configured. Returning fallback for key '%s'.",
                fallback_key,
            )
            return self._fallback_response(fallback_key)

        last_error = None
        delay = self.BASE_DELAY

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                start = time.time()

                kwargs = {
                    "model": self.MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = self.client.chat.completions.create(**kwargs)
                elapsed_ms = round((time.time() - start) * 1000, 2)

                record_response_time(elapsed_ms)
                logger.info(
                    "Groq call succeeded on attempt %d in %.1fms", attempt, elapsed_ms
                )

                return {
                    "content": response.choices[0].message.content,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "response_time_ms": elapsed_ms,
                    "model_used": self.MODEL,
                    "is_fallback": False,
                }

            except RateLimitError as e:
                last_error = e
                logger.warning(
                    "Groq rate limit hit on attempt %d/%d. Waiting %.1fs.",
                    attempt, self.MAX_RETRIES, delay,
                )
                time.sleep(delay)
                delay *= 2

            except APIConnectionError as e:
                last_error = e
                logger.warning(
                    "Groq connection error on attempt %d/%d: %s. Waiting %.1fs.",
                    attempt, self.MAX_RETRIES, str(e), delay,
                )
                time.sleep(delay)
                delay *= 2

            except APIStatusError as e:
                last_error = e
                if e.status_code in (500, 502, 503, 504):
                    logger.warning(
                        "Groq server error %d on attempt %d/%d. Waiting %.1fs.",
                        e.status_code, attempt, self.MAX_RETRIES, delay,
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    # 4xx errors — no point retrying
                    logger.error("Groq API error %d: %s", e.status_code, str(e))
                    break

            except Exception as e:
                last_error = e
                logger.error("Unexpected error calling Groq: %s", str(e))
                break

        # All retries exhausted — return fallback
        logger.error(
            "All %d Groq retries exhausted. Last error: %s. Returning fallback for key '%s'.",
            self.MAX_RETRIES, str(last_error), fallback_key,
        )
        return self._fallback_response(fallback_key)

    def parse_json_response(self, raw: str) -> dict:
        """Safely parse JSON from Groq response, stripping markdown fences."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last fence lines
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error("JSON parse failed: %s\nRaw: %s", str(e), raw[:200])
            return {"parse_error": str(e), "raw": raw}

    def _fallback_response(self, fallback_key: str = "default") -> dict:
        fallback_data = FALLBACK_TEMPLATES.get(fallback_key, FALLBACK_TEMPLATES["default"])
        return {
            "content": json.dumps(fallback_data),
            "tokens_used": 0,
            "response_time_ms": 0,
            "model_used": self.MODEL,
            "is_fallback": True,
        }


# Module-level singleton
_groq_client: GroqClient | None = None


def get_groq_client() -> GroqClient:
    global _groq_client
    if _groq_client is None:
        _groq_client = GroqClient()
    return _groq_client
