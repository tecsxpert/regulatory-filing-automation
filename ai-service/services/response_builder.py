from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_response(
    data: dict[str, Any],
    groq_info: dict[str, Any],
    cached: bool = False,
) -> dict[str, Any]:
    clean_data = dict(data)
    clean_data.pop("generated_at", None)

    meta = {
        "model_used": groq_info.get("model_used"),
        "tokens_used": groq_info.get("tokens_used"),
        "response_time_ms": groq_info.get("response_time_ms"),
        "cached": cached,
        "is_fallback": groq_info.get("is_fallback", False),
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    if "confidence" in clean_data:
        meta["confidence"] = clean_data["confidence"]
    elif "confidence" in groq_info:
        meta["confidence"] = groq_info["confidence"]

    return {"data": clean_data, "meta": meta}
