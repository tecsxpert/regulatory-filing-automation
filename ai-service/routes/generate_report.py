from __future__ import annotations

import os
import json
import logging

from flask import Blueprint, jsonify, request

from services.cache import ResponseCache
from services.groq_client import GroqClient, GroqServiceException
from services.prompt_store import PromptStore
from services.response_builder import build_response

from ._shared import require_json, stable_key

bp = Blueprint("generate_report", __name__)

_cache = ResponseCache(
    ttl_s=int(os.getenv("AI_CACHE_TTL_S", "600")),
    max_entries=int(os.getenv("AI_CACHE_MAX_ENTRIES", "1024")),
)

logger = logging.getLogger(__name__)
_prompts = PromptStore.from_default_location()


def _get_client() -> GroqClient:
    return GroqClient.from_env()


@bp.post("/generate-report")
def generate_report():
    fallback_response = {
        "title": "Report Unavailable",
        "executive_summary": "AI service temporarily unavailable. Please retry in a few minutes.",
        "overview": "",
        "top_items": [],
        "recommendations": [],
    }
    try:
        payload = require_json(request)

        company = (payload.get("company") or "").strip()
        filing_type = (payload.get("filing_type") or "").strip()
        period = (payload.get("period") or "").strip()
        notes = (payload.get("notes") or "").strip()

        if not company or not filing_type or not period:
            return (
                jsonify(
                    {
                        "error": "Missing required fields: company, filing_type, period",
                    }
                ),
                400,
            )

        model = payload.get("model")
        temperature = payload.get("temperature", 0.5)
        top_p = payload.get("top_p", 1.0)
        max_tokens = payload.get("max_tokens", 1000)

        system_prompt = payload.get(
            "system_prompt",
            "You generate clear, compliance-friendly drafts. "
            "Do not invent facts; if data is missing, add TODO placeholders.",
        )
        user_prompt = _prompts.render(
            "generate_report.txt",
            company=company,
            filing_type=filing_type,
            period=period,
            notes=notes,
            filing_data=json.dumps(payload.get("filing_data", {}), sort_keys=True),
        )

        cache_key = stable_key(
            "generate-report",
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
            logger.error("JSON parsing failed for /generate-report: %s", e)
            groq_info["is_fallback"] = True
            return jsonify({"data": fallback_response, "meta": groq_info}), 200

        response_data = build_response(parsed_content, groq_info, cached=False)
        _cache.set(cache_key, response_data)
        return jsonify(response_data), 200
    except (ValueError, GroqServiceException) as e:
        logger.error("Error in /generate-report: %s", e)
        return jsonify({"data": fallback_response, "meta": {"is_fallback": True, "error_detail": str(e)}}), 200
    except Exception as e:
        logger.exception("Unexpected error in /generate-report endpoint")
        return jsonify({"data": fallback_response, "meta": {"is_fallback": True, "error_detail": str(e)}}), 200
