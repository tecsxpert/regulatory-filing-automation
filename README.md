# Regulatory Filing Automation

## ai-service (Flask)

Python microservice under `ai-service/` exposing:
- `POST /categorise`
- `POST /generate-report`
- `GET /health` (default port `5000`)

Docs: `ai-service/AI_DOCS.md`

- Day 1: added catch-up file `regulatory-filing-automation/days/day-1.md`
- Day 2: added `ai-service/services/groq_client.py` with retry + backoff
- Day 3: added `ai-service/routes/categorise.py` and prompt `ai-service/prompts/categorise_prompt.txt`
- Day 4: added `ai-service/services/chroma_client.py` for ChromaDB setup
- Day 5: add catch-up file `regulatory-filing-automation/days/day-5.md`
- Day 3: added `ai-service/routes/categorise.py` and prompt `ai-service/prompts/categorise_prompt.txt`
- Day 4: added `ai-service/services/chroma_client.py` (ChromaDB integration)
- Day 5: added catch-up file `regulatory-filing-automation/days/day-5.md`
