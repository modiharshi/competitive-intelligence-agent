# Competitive Intelligence Agent

Agentic competitive intelligence MVP for discovering competitor footprints, monitoring public signals, generating grounded hypotheses, and recommending actions.

## Local Demo

The core pipeline runs without external API keys by using curated demo data:

```bash
PYTHONPATH=src python3 -m competitive_intelligence_agent.cli HubSpot
```

The intended full stack is Python 3.11+, FastAPI, LangGraph, Pydantic, and a static HTML/CSS/JS dashboard. API keys should be supplied through environment variables only.

## Project Shape

- `src/competitive_intelligence_agent/` contains the dependency-light MVP pipeline and FastAPI adapter.
- `data/demo_signals.json` provides deterministic capstone demo data.
- `web/` contains the static dashboard shell.
- `_bmad-output/planning-artifacts/` contains the product, UX, and architecture source documents.
