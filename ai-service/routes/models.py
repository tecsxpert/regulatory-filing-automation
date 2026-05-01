from __future__ import annotations

from flask import Blueprint, jsonify

from services.groq_client import GroqClient

bp = Blueprint("models", __name__)


@bp.get("/models")
def models():
    try:
        client = GroqClient.from_env()
        models = client.list_models()
        # Keep response small + easy to scan
        ids = [m.get("id") for m in models if m.get("id")]
        return jsonify(
            {
                "data": {"models": ids, "count": len(ids)},
                "meta": {"is_fallback": False},
            }
        )
    except ValueError as e:
        return (
            jsonify(
                {
                    "data": {"models": [], "count": 0},
                    "meta": {"is_fallback": True, "error_detail": str(e)},
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "data": {"models": [], "count": 0},
                    "meta": {"is_fallback": True, "error_detail": str(e)},
                }
            ),
            200,
        )

