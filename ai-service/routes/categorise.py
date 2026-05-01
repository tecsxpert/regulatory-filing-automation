from __future__ import annotations

import os
import logging

from flask import Blueprint, jsonify, request

from services.cache import ResponseCache
from services.groq_client import GroqClient, GroqServiceException
from services.prompt_store import PromptStore
from services.response_builder import build_response

from ._shared import require_json, stable_key

bp = Blueprint("categorise", __name__)

_cache = ResponseCache(
    ttl_s=int(os.getenv("AI_CACHE_TTL_S", "600")),
    max_entries=int(os.getenv("AI_CACHE_MAX_ENTRIES", "1024")),
)

logger = logging.getLogger(__name__)
_prompts = PromptStore.from_default_location()


def _get_client() -> GroqClient:
    return GroqClient.from_env()


@bp.post("/categorise")
def categorise():
    fallback_response = {
        "category": "OTHER",
        "confidence": 0.0,
        "reasoning": "AI service temporarily unavailable",
    }

    try:
        payload = require_json(request)
        text = (payload.get("text") or "").strip()
        if not text:
            return jsonify({"error": "Missing required field: text"}), 400
        model = payload.get("model")
        temperature = payload.get("temperature", 0.2)
        top_p = payload.get("top_p", 1.0)
        max_tokens = payload.get("max_tokens", 256)

        system_prompt = payload.get(
            "system_prompt",
            "You are a precise assistant for regulatory filing automation. "
            "Return concise, structured JSON only.",
        )
        user_prompt = _prompts.render("categorise.txt", text=text)

        cache_key = stable_key(
            "categorise",
            {
                "model": model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            },
        )

        cached_result = _cache.get(cache_key)
        if cached_result is not None:
            cached_result["meta"]["cached"] = True
            return jsonify(cached_result), 200

        client = _get_client()
        content_str, groq_info = client.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=float(temperature),
            top_p=float(top_p),
            max_tokens=int(max_tokens),
            response_format={"type": "json_object"},
        )

        try:
            parsed_content = GroqClient.parse_json_response(content_str)
        except ValueError as e:
            logger.error("JSON parsing failed for /categorise: %s", e)
            groq_info["is_fallback"] = True
            return jsonify({"data": fallback_response, "meta": groq_info}), 200

        response_data = build_response(parsed_content, groq_info, cached=False)
        _cache.set(cache_key, response_data)
        return jsonify(response_data), 200
    except (ValueError, GroqServiceException) as e:
        logger.error("Error in /categorise: %s", e)
        return jsonify({"data": fallback_response, "meta": {"is_fallback": True, "error_detail": str(e)}}), 200
    except Exception as e:
        logger.exception("Unexpected error in /categorise endpoint")
        return jsonify({"data": fallback_response, "meta": {"is_fallback": True, "error_detail": str(e)}}), 200
