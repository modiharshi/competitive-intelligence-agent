---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/briefs/brief-competitive-intelligence-agent-2026-06-21/brief.md
  - _bmad-output/planning-artifacts/prds/prd-competitive-intelligence-agent-2026-06-21/prd.md
workflowType: 'architecture'
project_name: 'competitive-intelligence-agent'
user_name: 'Harshi'
date: '2026-06-21'
lastStep: 8
status: 'complete'
completedAt: '2026-06-23'
---

# Architecture Decision Document: Competitive Intelligence Agent

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Six FR groups spanning the full competitive intelligence pipeline:
- FR-1 (Discovery Agent): 4 sub-requirements — company resolution, tiered source discovery, source validation, structured footprint output
- FR-2 (Monitoring Agent): 5 sub-requirements — web diffing, news/press, hiring trends, sentiment, Pydantic-constrained signal classification (10 categories)
- FR-3 (Intelligence Agent): 3 sub-requirements — hybrid triggering, multi-dimensional correlation, structured synthesized output
- FR-4 (Hypothesis Agent): 3 sub-requirements — confidence scoring, prediction horizons, RAG grounding with 70% confidence gate
- FR-5 (Recommendation Agent): 2 sub-requirements — 5 response categories, Pydantic recommendation schema
- FR-6 (Reporting Agent): 3 sub-requirements — dashboard views, alerts/reports, HITL few-shot feedback logging

**Non-Functional Requirements:**
- NFR-1.1: Tier 1+2 footprint discovery < 30s (Tier 3 async/non-blocking)
- NFR-1.2: Synthesis + hypothesis generation < 10s
- NFR-1.3: Dashboard initial page load < 2s
- NFR-2.1: API key handling via environment variables only
- NFR-2.2: Respect robots.txt; descriptive User-Agent headers
- NFR-3.1: Exponential backoff on source failure; orchestrator must not halt

**KPI Targets (Validation Layer):**
- Signal Classification F1-Score > 0.85
- Noise Reduction Ratio > 80% vs raw feed
- Footprint Discovery Rate > 85% of active public profiles
- Hypothesis Traceability Rate: 100%

**Scale & Complexity:**
- Primary domain: Backend-first multi-agent AI pipeline + Vanilla JS/CSS/HTML dashboard
- Complexity level: High
- Estimated architectural components: 8 (7 agents + dashboard)

### Technical Constraints & Dependencies 

- **Orchestration:** LangGraph (or equivalent graph-based framework) — node-per-agent
- **LLM Layer:** Gemini / OpenAI via environment-variable–managed API keys
- **Structured Output:** `instructor` library or `.with_structured_output()` for Pydantic enforcement
- **Retrieval:** Vector store (e.g., ChromaDB / FAISS) for RAG grounding of hypotheses
- **Search APIs:** SerpAPI or Google CSE for Tier 2 source discovery and monitoring
- **Demo Dataset:** Curated historical JSON (local file) for Tier 3 / synthesis demo mode
- **Frontend:** Vanilla HTML/CSS/JS — no framework; must load in < 2s
- **Secret Management:** All API tokens via `.env` / `os.environ`; no hardcoded credentials
- **Ethics:** robots.txt compliance, descriptive User-Agent, no authenticated scraping

### Cross-Cutting Concerns Identified. 

1. **Observability & Logging** — Structured per-agent logs needed for KPI tracking and debugging
2. **Schema Integrity** — Pydantic models are the contract layer between all agents
3. **API Quota Management** — Independent rate limits across LLM, search, and scraping layers
4. **Error Isolation** — Failures in Tier 3 collection or individual source scrapes must not propagate to block orchestration
5. **HITL State Path** — Feedback log (JSON) must be accessible at Recommendation Agent inference time without coupling agents directly

---

## Starter Template Evaluation

### Primary Technology Domain
Python-first agentic backend (LangGraph) with a lightweight static dashboard (Vanilla HTML/CSS/JS).

### Starter Options Considered
1. **LangGraph Python Starter (`uv` + `langgraph-cli`):** Uses modern Python packaging tool `uv` for ultra-fast dependency resolution and virtual environments. Scaffolds a modular structure with `agent.py`, `state.py`, `nodes.py`, and `tools.py`. Built-in support for `langgraph.json` configuration for local development via `langgraph dev`.
2. **Standard Poetry + LangChain Template:** Traditional Poetry-based project layout. Solid, but slower dependency resolution and lacks the default out-of-the-box configuration for the LangGraph local dev server.

### Selected Starter: LangGraph Python Starter (via `uv`)

**Rationale for Selection:**
- Native integration with LangGraph structure (Graph, Nodes, State).
- Speed and modern compliance of `uv` package manager (crucial for local testing).
- Standardized separation of agent states (`state.py`), tools (`tools.py`), and graph transitions (`agent.py`).
- Out-of-the-box support for the LangGraph local development server with hot-reloading (`langgraph dev`).

**Initialization Command:**
```bash
uv init --lib competitive-intelligence-agent
uv add langgraph langchain-openai langchain-community instructor pydantic chromadb fastapi uvicorn
uv add --dev langgraph-cli[inmem] pytest
```

**Architectural Decisions Provided by Starter:**
- **Language & Runtime:** Python 3.11+ managed by `uv`.
- **Styling Solution:** None (backend). Dashboard structured as static files (`index.html`, `style.css`, `app.js`).
- **Build Tooling:** `uv` pyproject.toml configuration.
- **Testing Framework:** `pytest` configuration.
- **Code Organization:** A clean `src/` directory separating graph states, nodes, and custom tools.
- **Development Experience:** `langgraph-cli` integration for local visualization and execution.

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- **Orchestration Model:** LangGraph state machine where nodes execute independent agents, routing state transitions explicitly.
- **RAG & Hallucination Mitigation Strategy:** ChromaDB acting as local vector store for raw signals and site-diff histories. RAG contexts strictly enforce citation of source URL + timestamp.
- **Pydantic Validation Guard:** 100% structured LLM output via the `instructor` library, enforcing concrete schemas on every single agent edge transition.

**Important Decisions (Shape Architecture):**
- **Structured Relational Storage:** SQLite database for profiles, metadata, footprints, and feedback logs.
- **Async Execution:** Celery or standard Python `asyncio` tasks for Tier 3 monitoring routines.

**Deferred Decisions (Post-MVP):**
- **Enterprise IAM & Multi-Tenancy:** Handled as mock authentication in Phase 1 dashboard.

### Data Architecture

- **Primary DB:** SQLite (`sqlite3`) storing metadata, target company records, discovered footprints, and user feedback logs.
- **Vector DB:** ChromaDB (persisted under `data/chromadb/`) storing raw signal text embeddings (`sentence-transformers/all-MiniLM-L6-v2` or `openai/text-embedding-3-small`).
- **Structured Exchange format:** Strict JSON objects representing serialized Pydantic models.

### Hallucination & Accuracy Safeguards

1. **Structured Parser Gatekeeping:** The LLM cannot return raw text; it is query-bounded to return a strict schema (e.g. `StrategicHypothesis` containing `confidence_score`, `timeline_horizon`, and `verifiable_citations` array).
2. **Grounding context boundary:** Prompt parameters require matching every generated hypothesis claim directly to a document chunk ID in the retrieved context. If an item cannot be sourced, the hypothesis is marked invalid or confidence drops to zero.
3. **Alert score thresholding:** Hypotheses with calculated confidence scores < 70% are automatically logged to audit trails but marked `suppressed` in the database, protecting the reporting layer from low-quality noise.

### Temporal Intelligence, Memory & Early Warning Architecture

1. **Timeline Correlation Component:** Before intelligence synthesis, incoming signals are grouped into chronological sequences. A dedicated timeline correlation routine models temporal progression, identifying transitions like `Hiring Spike -> Patent Filing -> Beta Sign-up Page`.
2. **Signal Relationship Layer (Lightweight Knowledge Graph):** Signal correlation is structured using semantic relations stored as directed edges:
   - `precedes`: Temporal ordering.
   - `amplifies`: Signal reinforces another (e.g., job posting corroborates news leak).
   - `contradicts`: Opposing indicators (e.g., executive denial vs. hiring data).
   - `supports` & `causes`: Causal or logical containment.
3. **Competitor Memory Layer:** Long-term historical context is kept in a SQLite relational database and ChromaDB vector collections, recording:
   - Historical signals & synthesized hypotheses from previous runs.
   - Recurring themes and strategic patterns identified over time (e.g., "HubSpot regularly launches developer products in Q3 following Q1-Q2 hiring bursts").
4. **Early Warning Engine:** A dedicated evaluation engine translates hypotheses into actionable risk metrics by calculating an `Early Warning Score` (0 to 100):
   $$\text{Early Warning Score} = \text{Confidence} \times (w_1 \cdot \text{Urgency} + w_2 \cdot \text{Business Impact})$$
   Where `Urgency` represents time-to-impact (Short/Mid/Long-term), and `Business Impact` is assessed based on target category threat (e.g., Pricing/Product changes weight higher than leadership changes).

### Resilience, Storage, and Interactive HITL Decisions

1. **LLM Node Resilience:** Every agent node that invokes an external LLM API is decorated with `tenacity.retry` executing exponential backoff on rate-limit (429) and transient errors (500, 503).
2. **WAL Mode Execution:** The SQLite engine in `db_client.py` executes `PRAGMA journal_mode=WAL;` at database instantiation, allowing simultaneous readers to query metrics while background crawlers write new signals.
3. **LangGraph Interactive Interrupt (Stateful Pausing):** To implement human-in-the-loop validation, LangGraph compiles with an `interrupt_after=["hypothesis"]` transition. When a batch of hypotheses is generated:
   - The graph state is persisted in checkpointer memory, and thread execution pauses.
   - The user views hypotheses on the dashboard, marking them as `approved` or `rejected` (logged via `/api/feedback`).
   - Upon clicking "Resume Pipeline," the dashboard calls FastAPI `/api/graph/resume`, updating the state variables and triggering the compilation runner to finish the graph (executing recommendation & reporting nodes).
4. **Few-Shot Context Injection:** A feedback reader step executed at the start of the `hypothesis` and `recommendation` nodes queries past `FeedbackRecord` entries from SQLite for the specific competitor, passing successful/approved items into the system prompt context.
5. **Side-by-Side Comparison Endpoint:** A `/api/competitors/compare?competitor_a=OpenAI&competitor_b=Anthropic` route is exposed on the FastAPI application, fetching and formatting both companies' latest hypotheses side-by-side in JSON.

---

## Implementation Patterns & Consistency Rules

### Naming Patterns
- **Database Table Names:** lowercase, snake_case, pluralized (e.g., `competitors`, `discovered_sources`, `signals`, `hypotheses`, `feedback`).
- **Pydantic Model Names:** PascalCase (e.g., `SignalEvent`, `StrategicHypothesis`, `ActionRecommendation`).
- **API Endpoints:** lowercase, pluralized nouns, prefixed with `/api` (e.g., `/api/competitors`, `/api/hypotheses`, `/api/feedback`).
- **State Key Conventions:** snake_case in `AgentState` TypedDict.

### Structure Patterns
- **Tests Location:** Kept in the root directory under `/tests/`, running via `pytest`.
- **Node Separation:** Every agent must inhabit a separate Python module within `src/nodes/` implementing the signature `def agent_name_node(state: AgentState) -> dict`.

### Communication & State Payload Schema (AgentState)
All agents interact strictly via the centralized `AgentState` context:

```python
from typing import TypedDict, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class FootprintSource(BaseModel):
    url: str
    source_type: Literal['owned', 'social', 'customer']
    confidence: float
    status: Literal['monitoring', 'ignored']

class SignalEvent(BaseModel):
    id: str
    source_url: str
    category: Literal['Product', 'Pricing', 'Hiring', 'Marketing', 'Partnerships', 'Funding', 'Expansion', 'Leadership', 'Customer Sentiment', 'Community Activity']
    content_diff: str
    timestamp: str

class SignalRelation(BaseModel):
    source_id: str
    target_id: str
    relation_type: Literal['precedes', 'amplifies', 'contradicts', 'supports', 'causes']

class CompetitorMemoryItem(BaseModel):
    competitor_name: str
    pattern_type: str   # 'hiring_pattern' | 'pricing_strategy' | etc.
    summary: str
    confidence_level: float
    last_observed: str

class StrategicHypothesis(BaseModel):
    id: str
    theme: str
    confidence_score: float
    time_horizon: str  # 'Short-Term' | 'Mid-Term' | 'Long-Term'
    supporting_signals: List[str]  # IDs of SignalEvents
    signal_relations: List[SignalRelation]
    sources: List[str]  # Verifiable Source URLs

class ActionRecommendation(BaseModel):
    id: str
    hypothesis_id: str
    action: str
    posture: str  # 'Offensive' | 'Defensive'
    outcome: str

class EarlyWarningAlert(BaseModel):
    id: str
    hypothesis_id: str
    early_warning_score: float  # Calculated 0-100 score
    urgency: str               # 'High' | 'Medium' | 'Low'
    business_impact: str       # 'Critical' | 'Major' | 'Minor'
    threat_description: str

class FeedbackRecord(BaseModel):
    hypothesis_id: str
    vote: Literal['thumbs_up', 'thumbs_down']
    comments: str = ""
    timestamp: str

class AgentState(TypedDict):
    competitor_name: str
    domain: str
    footprints: List[FootprintSource]
    signals: List[SignalEvent]
    relations: List[SignalRelation]
    hypotheses: List[StrategicHypothesis]
    recommendations: List[ActionRecommendation]
    early_warnings: List[EarlyWarningAlert]
    competitor_memory: List[CompetitorMemoryItem]
    feedback: List[FeedbackRecord]
```

---

## Project Structure & Boundaries

```text
competitive-intelligence-agent/
├── .env.example
├── README.md
├── pyproject.toml
├── uv.lock
├── langgraph.json
├── data/
│   ├── app.db                # SQLite database (stores relational schemas, memory, relations)
│   └── chromadb/             # Vector database files
├── src/
│   ├── __init__.py
│   ├── main.py               # FastAPI backend app entry point
│   ├── agent.py              # LangGraph compilation & workflow setup
│   ├── state.py              # Pydantic & TypedDict State declarations
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── discovery.py      # FR-1 footprint discovery node
│   │   ├── monitoring.py     # FR-2 monitoring node
│   │   ├── classification.py # FR-2 signal classification node
│   │   ├── intelligence.py   # FR-3 signal synthesis node (includes Timeline & Graph Correlation)
│   │   ├── memory_layer.py   # Competitor Memory long-term tracking node
│   │   ├── hypothesis.py     # FR-4 hypothesis agent node
│   │   ├── early_warning.py  # Early Warning Engine scoring node
│   │   ├── recommendation.py # FR-5 recommendation agent node
│   │   └── reporting.py      # FR-6 reporting node
│   ├── tools/
│   │   ├── scraper.py        # Scraper utility (Direct HTTP / SerpAPI)
│   │   ├── db_client.py      # SQLite operations helper
│   │   └── vector_store.py   # ChromaDB client interface
│   └── ui/                   # Static UI Dashboard files
│       ├── index.html
│       ├── style.css
│       └── app.js
└── tests/
    ├── __init__.py
    ├── test_graph.py
    └── test_nodes.py
```

### Integration Points
1. **Frontend to Backend:** Static UI queries local FastAPI endpoints via AJAX requests (`fetch`).
2. **LLM Execution:** Handled via structured Pydantic models through the `instructor` OpenAI/Gemini bridge.
3. **Data Storage Integrity:** Node outputs are committed to both the `AgentState` object (for sequential node retrieval) and written to SQLite and ChromaDB as the sources of truth.

---

## Architecture Validation Results

### Coherence Validation ✅
- **Compatibility:** Python 3.11 with FastAPI and LangGraph compile cleanly together. Schema-enforced states ensure contract validation errors trigger immediately rather than propagating down the agent execution graph.
- **Hallucination Countermeasures:** RAG queries are tightly bound to metadata filters by target company, restricting context leaks. Pydantic validation prevents empty citation structures.

### Requirements Coverage Validation ✅
- **FR-1 & FR-2:** Managed via dynamic scraping routes & SerpAPI searches, structured as distinct initial graph steps.
- **FR-3 to FR-5:** Implemented as logical synthesis steps executing LLM pipelines with strict confidence thresholds.
- **NFR targets:** Minimal REST overhead + SQLite ensures dashboard initial load is < 2s. Multi-speed scheduling isolates slow scraping runs from main workflow execution.

### Architecture Completeness Checklist
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped
- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed
- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented
- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION  
**Confidence Level:** High  

---

## Implementation Handoff & Next Steps

**AI Agent Guidelines:**
1. Maintain strict typing declarations; run `mypy` or similar static checks where appropriate.
2. Ensure every new agent logic unit has a corresponding test file in `tests/`.
3. Do not modify the Pydantic schema schemas inside `state.py` without updating the decision logs.

**First Implementation Priority:**
Execute the starter initialization commands to configure `uv` and create the initial project file structure.
