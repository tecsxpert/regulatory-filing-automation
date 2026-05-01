from __future__ import annotations

import json
import time
from typing import Any

from app import create_app


def _print_response(label: str, status_code: int, body: Any) -> None:
    print(f"\n## {label} ({status_code})")
    print(json.dumps(body, indent=2, sort_keys=True))


def main() -> int:
    client = create_app().test_client()

    health = client.get("/health")
    _print_response("health", health.status_code, health.get_json())

    models = client.get("/models")
    _print_response("models", models.status_code, models.get_json())

    categorise = client.post(
        "/categorise",
        json={"text": "Annual 10-K filing for fiscal year 2025."},
    )
    _print_response("categorise", categorise.status_code, categorise.get_json())

    report = client.post(
        "/generate-report",
        json={
            "company": "Acme Corp",
            "filing_type": "10-K",
            "period": "FY2025",
            "notes": "Demo dry run with fallback-safe behavior.",
        },
    )
    _print_response("generate-report", report.status_code, report.get_json())

    async_report = client.post(
        "/generate-report",
        json={
            "company": "Acme Corp",
            "filing_type": "10-K",
            "period": "FY2025",
            "async": True,
        },
    )
    async_body = async_report.get_json()
    _print_response("generate-report async", async_report.status_code, async_body)

    if async_body and async_body.get("job_id"):
        job = None
        for _ in range(10):
            job = client.get(f"/generate-report/jobs/{async_body['job_id']}")
            body = job.get_json() or {}
            if body.get("status") in {"completed", "failed"}:
                break
            time.sleep(0.05)
        assert job is not None
        _print_response("generate-report job", job.status_code, job.get_json())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
