# Competitive Intelligence Agent

An agentic competitive intelligence system that discovers competitor footprints, monitors public signals, generates grounded hypotheses, and recommends strategic actions.

## Overview

The Competitive Intelligence Agent helps businesses track competitors by turning scattered public information into structured, executive-ready intelligence.

It monitors signals such as product updates, hiring activity, news, pricing changes, and company announcements, then uses a multi-agent workflow to classify, correlate, and summarize those signals into actionable insights.

## Key Features

- Competitor footprint discovery
- Public signal monitoring
- Signal classification
- Cross-signal intelligence synthesis
- RAG-grounded hypothesis generation
- Strategic recommendations
- Executive-style dashboard
- Local demo mode with curated data
- Optional Ollama/local model support

## Tech Stack

- Python 3.11+
- FastAPI
- LangGraph
- Pydantic
- ChromaDB
- SQLite
- HTML/CSS/JavaScript
- Ollama / Gemini / OpenAI support

## Local Demo

The core pipeline runs without external API keys using curated demo data.

```bash
PYTHONPATH=src python3 -m competitive_intelligence_agent.cli HubSpot
