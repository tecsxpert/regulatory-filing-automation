# Regulatory Filing Automation

## ai-service (Flask)

Python microservice under `ai-service/` exposing:
- `POST /categorise`
- `POST /generate-report`
- `GET /health` (default port `5000`)

Docs: `ai-service/AI_DOCS.md`

- Day 1: added catch-up file `regulatory-filing-automation/days/day-1.md`
- Day 2: added `ai-service/services/groq_client.py` with retry + backoff
