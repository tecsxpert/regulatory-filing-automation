from __future__ import annotations

import argparse
import statistics
import time
from typing import Any

from app import create_app


def _time_request(client: Any, method: str, path: str, **kwargs: Any) -> float:
    started = time.perf_counter()
    response = getattr(client, method)(path, **kwargs)
    response.get_data()
    return (time.perf_counter() - started) * 1000


def _summary(samples: list[float]) -> dict[str, float]:
    ordered = sorted(samples)
    p95_index = max(0, int(len(ordered) * 0.95) - 1)
    return {
        "min_ms": round(min(ordered), 2),
        "avg_ms": round(statistics.fmean(ordered), 2),
        "p95_ms": round(ordered[p95_index], 2),
        "max_ms": round(max(ordered), 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local AI service routes.")
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()

    iterations = max(1, args.iterations)
    client = create_app().test_client()

    cases = {
        "health": ("get", "/health", {}),
        "categorise_validation": ("post", "/categorise", {"json": {}}),
        "generate_report_validation": ("post", "/generate-report", {"json": {}}),
    }

    for name, (method, path, kwargs) in cases.items():
        samples = [
            _time_request(client, method, path, **kwargs) for _ in range(iterations)
        ]
        stats = _summary(samples)
        print(
            f"{name}: min={stats['min_ms']}ms avg={stats['avg_ms']}ms "
            f"p95={stats['p95_ms']}ms max={stats['max_ms']}ms"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
