"""
POST /categorise — AI Developer 2 core endpoint
Classifies a regulatory filing into a predefined category.
Returns: {category, confidence, reasoning, meta}
"""

import os
import time
import logging
from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from services.groq_client import get_groq_client
from services.cache_service import get_cache_service
from services.sanitiser import validate_and_sanitise
from services.response_builder import build_meta, build_error_response

logger = logging.getLogger(__name__)

categorise_bp = Blueprint("categorise", __name__)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "categorise_prompt.txt")


def load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


VALID_CATEGORIES = [
    "ANNUAL_REPORT", "QUARTERLY_FILING", "INCIDENT_REPORT",
    "LICENSE_APPLICATION", "LICENSE_RENEWAL", "AMENDMENT",
    "DISCLOSURE", "AUDIT_RESPONSE", "EXEMPTION_REQUEST", "OTHER",
]


@categorise_bp.route("/categorise", methods=["POST"])
def categorise():
    """
    Classify a regulatory filing into a predefined category.

    Request body:
      title (str, required)
      description (str, required)
      filing_type (str, optional)
      regulatory_body (str, optional)
      fresh (bool, optional) — skip cache if true

    Returns:
      {category, confidence, reasoning, meta}
    """
    request_start = time.time()
    body = request.get_json(silent=True)

    if not body:
        return jsonify(build_error_response("Request body must be valid JSON")[0]), 400

    # Validate and sanitise
    data, err = validate_and_sanitise(body, required_fields=["title", "description"])
    if err:
        return jsonify(build_error_response(err)[0]), 400

    fresh = data.pop("fresh", False)
    payload_for_cache = {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "filing_type": data.get("filing_type", ""),
        "regulatory_body": data.get("regulatory_body", ""),
    }

    # Cache check (skip if fresh=true)
    if not fresh:
        cache = get_cache_service()
        cached = cache.get("categorise", payload_for_cache)
        if cached:
            logger.info("Cache hit for /categorise")
            return jsonify(cached), 200

    # Build prompt
    prompt_template = load_prompt()
    prompt = prompt_template.format(
        title=data.get("title", ""),
        description=data.get("description", ""),
        filing_type=data.get("filing_type", "N/A"),
        regulatory_body=data.get("regulatory_body", "N/A"),
    )

    # Call Groq
    client = get_groq_client()
    result = client.call_groq(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # low temp for consistent classification
        max_tokens=300,
        fallback_key="categorise",
    )

    elapsed_ms = (time.time() - request_start) * 1000

    if result["is_fallback"]:
        import json
        fallback_data = json.loads(result["content"])
        fallback_data["meta"] = build_meta(
            confidence=0.0,
            model_used=result["model_used"],
            tokens_used=0,
            response_time_ms=elapsed_ms,
            cached=False,
            is_fallback=True,
        )
        return jsonify(fallback_data), 200

    # Parse JSON response
    parsed = client.parse_json_response(result["content"])

    # Validate category
    category = parsed.get("category", "OTHER")
    if category not in VALID_CATEGORIES:
        logger.warning("Groq returned invalid category '%s', defaulting to OTHER", category)
        category = "OTHER"

    confidence = float(parsed.get("confidence", 0.5))

    response = {
        "category": category,
        "confidence": round(confidence, 3),
        "reasoning": parsed.get("reasoning", "Classification based on filing content."),
        "meta": build_meta(
            confidence=confidence,
            model_used=result["model_used"],
            tokens_used=result["tokens_used"],
            response_time_ms=result["response_time_ms"],
            cached=False,
            is_fallback=False,
        ),
    }

    # Store in cache
    cache = get_cache_service()
    cache.set("categorise", payload_for_cache, response)

    logger.info(
        "Categorised filing '%s' as %s (confidence %.2f) in %.1fms",
        data.get("title", "")[:50], category, confidence, elapsed_ms,
    )

    return jsonify(response), 200
