"""
POST /generate-report — AI Developer 2 responsibility
Async job processing: returns job_id immediately, processes in background thread,
supports SSE streaming (AI Developer 1 adds SSE; this provides the async job backbone).
Also supports synchronous mode for simpler use cases.
"""

import os
import json
import time
import uuid
import logging
import threading
from flask import Blueprint, request, jsonify, Response, stream_with_context

from services.groq_client import get_groq_client
from services.cache_service import get_cache_service
from services.sanitiser import validate_and_sanitise
from services.response_builder import build_meta, build_error_response

logger = logging.getLogger(__name__)

generate_report_bp = Blueprint("generate_report", __name__)

PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "prompts", "generate_report_prompt.txt")

# In-memory job store (in production use Redis)
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _process_report_job(job_id: str, filing_data: dict):
    """Background thread: calls Groq and updates job status."""
    with _jobs_lock:
        _jobs[job_id]["status"] = "processing"

    client = get_groq_client()
    prompt_template = load_prompt()
    filing_str = json.dumps(filing_data, indent=2)
    prompt = prompt_template.format(filing_data=filing_str)

    start = time.time()
    result = client.call_groq(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=1500,
        fallback_key="generate_report",
    )
    elapsed_ms = (time.time() - start) * 1000

    if result["is_fallback"]:
        report_data = json.loads(result["content"])
    else:
        report_data = client.parse_json_response(result["content"])

    report_data["meta"] = build_meta(
        confidence=0.82 if not result["is_fallback"] else 0.0,
        model_used=result["model_used"],
        tokens_used=result["tokens_used"],
        response_time_ms=elapsed_ms,
        is_fallback=result["is_fallback"],
    )

    with _jobs_lock:
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = report_data
        _jobs[job_id]["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    logger.info("Report job %s completed in %.1fms", job_id, elapsed_ms)


@generate_report_bp.route("/generate-report", methods=["POST"])
def generate_report():
    """
    Generate a compliance report for a regulatory filing.

    Request body:
      filing_data (dict, required) — the full filing object
      async_mode (bool, optional, default true) — false for synchronous response
      fresh (bool, optional) — skip cache

    Returns (async mode):
      {job_id, status, poll_url}

    Returns (sync mode):
      {title, executive_summary, overview, top_items, recommendations, meta}
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify(build_error_response("Request body must be valid JSON")[0]), 400

    if "filing_data" not in body or not body["filing_data"]:
        return jsonify(build_error_response("Missing required field: 'filing_data'")[0]), 400

    filing_data = body["filing_data"]
    async_mode = body.get("async_mode", True)
    fresh = body.get("fresh", False)

    # Cache check for sync mode
    if not async_mode and not fresh:
        cache = get_cache_service()
        cached = cache.get("generate_report", {"filing_data": str(filing_data)[:200]})
        if cached:
            return jsonify(cached), 200

    if async_mode:
        # Return job_id immediately
        job_id = str(uuid.uuid4())
        with _jobs_lock:
            _jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "result": None,
                "completed_at": None,
            }

        thread = threading.Thread(
            target=_process_report_job,
            args=(job_id, filing_data),
            daemon=True,
        )
        thread.start()

        logger.info("Queued async report job %s", job_id)
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "poll_url": f"/generate-report/status/{job_id}",
            "message": "Report generation started. Poll the poll_url for status.",
        }), 202

    else:
        # Synchronous mode — wait for result
        client = get_groq_client()
        prompt_template = load_prompt()
        filing_str = json.dumps(filing_data, indent=2)
        prompt = prompt_template.format(filing_data=filing_str)

        start = time.time()
        result = client.call_groq(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=1500,
            fallback_key="generate_report",
        )
        elapsed_ms = (time.time() - start) * 1000

        if result["is_fallback"]:
            report_data = json.loads(result["content"])
        else:
            report_data = client.parse_json_response(result["content"])

        report_data["meta"] = build_meta(
            confidence=0.82 if not result["is_fallback"] else 0.0,
            model_used=result["model_used"],
            tokens_used=result["tokens_used"],
            response_time_ms=elapsed_ms,
            is_fallback=result["is_fallback"],
        )

        # Cache sync response
        cache = get_cache_service()
        cache.set("generate_report", {"filing_data": str(filing_data)[:200]}, report_data)

        return jsonify(report_data), 200


@generate_report_bp.route("/generate-report/status/<job_id>", methods=["GET"])
def get_job_status(job_id: str):
    """Poll for async job status."""
    with _jobs_lock:
        job = _jobs.get(job_id)

    if not job:
        return jsonify({"error": f"Job '{job_id}' not found"}), 404

    if job["status"] == "completed":
        return jsonify({
            "job_id": job_id,
            "status": "completed",
            "completed_at": job["completed_at"],
            "result": job["result"],
        }), 200

    return jsonify({
        "job_id": job_id,
        "status": job["status"],
        "created_at": job["created_at"],
        "message": "Report is being generated. Poll again in a few seconds.",
    }), 200


@generate_report_bp.route("/generate-report/stream", methods=["POST"])
def generate_report_stream():
    """
    SSE streaming endpoint for /generate-report.
    Streams tokens as they arrive from Groq.
    Frontend reads with EventSource.
    """
    body = request.get_json(silent=True)
    if not body or "filing_data" not in body:
        return jsonify({"error": "Missing filing_data"}), 400

    filing_data = body["filing_data"]

    def generate():
        client = get_groq_client()
        prompt_template = load_prompt()
        filing_str = json.dumps(filing_data, indent=2)
        prompt = prompt_template.format(filing_data=filing_str)

        try:
            from groq import Groq
            import os
            groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            stream = groq_client.chat.completions.create(
                model=client.MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=1500,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield f"data: {json.dumps({'token': delta})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error("SSE streaming error: %s", str(e))
            yield f"data: {json.dumps({'error': str(e), 'is_fallback': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
