# AI Service Summary Card

## Scope

- Flask AI service for regulatory filing automation.
- Groq chat integration with JSON parsing, retry-safe errors, and fallback responses.
- Prompt templates for categorisation and report generation.
- Local health, model listing, categorise, generate-report, and async report job routes.
- In-memory cache plus optional Redis cache service.

## Endpoints

- `GET /health`
- `GET /models`
- `POST /categorise`
- `POST /generate-report`
- `GET /generate-report/jobs/<job_id>`

## Operational Scripts

- `python test_groq.py`
- `python prompt_qa.py`
- `python benchmark.py`
- `python demo_dry_run.py`

## Verification

- Prompt QA passes.
- Benchmark runs locally through Flask test client.
- Demo dry run works without a Groq API key by exercising fallback-safe responses.
- Dockerfile runs the app with gunicorn and honors `PORT`.

## Required Environment

- `GROQ_API_KEY`
- `GROQ_MODEL`
- Optional: `REDIS_URL`, `AI_CACHE_TTL_S`, `AI_CACHE_MAX_ENTRIES`, `PORT`
