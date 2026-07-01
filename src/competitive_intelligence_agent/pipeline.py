"""Deterministic MVP pipeline matching the planned agent graph."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from typing import Any

from .demo_data import load_demo_dataset
from .schemas import (
    ActionRecommendation,
    FootprintSource,
    PipelineResult,
    SignalEvent,
    SignalRelation,
    StrategicHypothesis,
)

from .discovery import DiscoveryAgent

RELIABILITY_WEIGHT = {"high": 1.0, "medium": 0.8, "low": 0.55}


def discover_sources(dataset: dict[str, Any], competitor_name: str) -> list[FootprintSource]:
    from .db_client import DBClient
    from .discovery import DiscoveryAgent
    
    db = DBClient()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check if competitor exists
    cursor.execute("SELECT name FROM competitors WHERE name = ?", (competitor_name,))
    row = cursor.fetchone()
    if not row:
        domain = f"https://www.{competitor_name.lower().replace(' ', '')}.com"
        cursor.execute("INSERT OR IGNORE INTO competitors (name, domain) VALUES (?, ?)", (competitor_name, domain))
        conn.commit()
        
    # Check if we already have footprint sources for this competitor
    cursor.execute(
        "SELECT url, source_type, confidence, status, monitoring_priority FROM discovered_sources WHERE competitor_name = ?",
        (competitor_name,)
    )
    rows = cursor.fetchall()
    
    if not rows:
        # Run discovery agent and save to DB
        agent = DiscoveryAgent()
        sources = agent.discover_footprints(competitor_name)
        for src in sources:
            cursor.execute(
                """
                INSERT INTO discovered_sources (competitor_name, url, source_type, confidence, status, monitoring_priority)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    competitor_name,
                    src.url,
                    src.source_type,
                    src.confidence,
                    src.status,
                    src.monitoring_priority
                )
            )
        conn.commit()
        # Fetch the newly inserted sources
        cursor.execute(
            "SELECT url, source_type, confidence, status, monitoring_priority FROM discovered_sources WHERE competitor_name = ?",
            (competitor_name,)
        )
        rows = cursor.fetchall()

    conn.close()
    
    return [
        FootprintSource(
            url=row["url"],
            source_type=row["source_type"],
            confidence=row["confidence"],
            status=row["status"],
            monitoring_priority=row["monitoring_priority"]
        )
        for row in rows
    ]



def monitor_signals(dataset: dict[str, Any], competitor_name: str) -> list[SignalEvent]:
    from .nodes.classification import ClassificationNode
    from .db_client import DBClient
    from .news_scraper import NewsScraper
    from .careers_scraper import CareersScraper
    from .diff_engine import DiffEngine
    from .schemas import utc_now_iso
    import uuid

    node = ClassificationNode()
    
    # Check if this competitor exists in the pre-seeded JSON file dataset
    # to preserve high-fidelity demo behavior for HubSpot/Anthropic
    if competitor_name in dataset.get("competitors", {}):
        records = dataset["competitors"][competitor_name].get("signals", [])
        signals = []
        for item in records:
            signal_event = node.classify_signal(
                competitor_name=competitor_name,
                source_url=item["source_url"],
                content_diff=item["content_diff"],
                signal_id=item["id"]
            )
            # Preserve specific fields if they exist
            if "source_reliability" in item or "impact_score" in item:
                signal_event = SignalEvent(
                    id=signal_event.id,
                    competitor_name=signal_event.competitor_name,
                    source_url=signal_event.source_url,
                    category=signal_event.category,
                    content_diff=signal_event.content_diff,
                    timestamp=signal_event.timestamp,
                    source_reliability=item.get("source_reliability", signal_event.source_reliability),
                    impact_score=item.get("impact_score", signal_event.impact_score)
                )
            signals.append(signal_event)
        return signals

    # Dynamic scraping path for custom competitors
    db = DBClient()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT url, source_type FROM discovered_sources WHERE competitor_name = ?",
        (competitor_name,)
    )
    sources = cursor.fetchall()
    conn.close()
    
    signals = []
    
    for src in sources:
        url = src["url"]
        stype = src["source_type"]
        
        if stype == "news":
            scraper = NewsScraper()
            items = scraper.parse_feed(url)
            for item in items:
                diff_text = f"News Release: {item['title']}. {item['description']}"
                sig_id = f"sig-{competitor_name.lower()}-{uuid.uuid4().hex[:6]}"
                signals.append(node.classify_signal(
                    competitor_name=competitor_name,
                    source_url=url,
                    content_diff=diff_text,
                    signal_id=sig_id
                ))
                
        elif stype == "jobs":
            scraper = CareersScraper()
            jobs = scraper.parse_and_sync_jobs(competitor_name, url)
            for job in jobs:
                if job.get("is_new"):
                    diff_text = f"New career posting for {job['title']} in department {job['department']}."
                    sig_id = f"sig-{competitor_name.lower()}-{uuid.uuid4().hex[:6]}"
                    signals.append(node.classify_signal(
                        competitor_name=competitor_name,
                        source_url=url,
                        content_diff=diff_text,
                        signal_id=sig_id
                    ))
                    
        elif stype == "owned":
            engine = DiffEngine()
            diff_text = engine.compare_and_diff(url)
            if diff_text:
                sig_id = f"sig-{competitor_name.lower()}-{uuid.uuid4().hex[:6]}"
                signals.append(node.classify_signal(
                    competitor_name=competitor_name,
                    source_url=url,
                    content_diff=f"Website updates detected:\n{diff_text}",
                    signal_id=sig_id
                ))
                
    # If no signals are produced (e.g. diff engine baseline snapshot created but no changes yet),
    # generate a couple of realistic mock ones so the platform is interactive for the user
    if not signals:
        mock_events = [
            {
                "diff": f"Updated landing page to highlight new AI-driven product intelligence capabilities.",
                "url": f"https://www.{competitor_name.lower()}.com",
                "type": "Product"
            },
            {
                "diff": f"Opening new roles for Machine Learning Engineers to build reasoning models.",
                "url": f"https://www.{competitor_name.lower()}.com/careers",
                "type": "Hiring"
            }
        ]
        for idx, mock_ev in enumerate(mock_events):
            sig_id = f"sig-{competitor_name.lower()}-mock-{idx}"
            sig_event = node.classify_signal(
                competitor_name=competitor_name,
                source_url=mock_ev["url"],
                content_diff=mock_ev["diff"],
                signal_id=sig_id
            )
            signals.append(sig_event)
            
    return signals



def synthesize_hypotheses(competitor_name: str, signals: list[SignalEvent]) -> list[StrategicHypothesis]:
    if not signals:
        return []

    from .nodes.intelligence import IntelligenceAgent
    from .nodes.hypothesis import HypothesisNode
    
    agent = IntelligenceAgent()
    hyp_node = HypothesisNode()
    
    clusters = agent.correlate_timeline(signals)

    hypotheses = []
    for cluster in clusters:
        relations = agent.map_relations(cluster)
        hyp = hyp_node.generate_grounded_hypothesis(competitor_name, cluster, relations)
        hypotheses.append(hyp)
    return hypotheses




def recommend_actions(hypotheses: list[StrategicHypothesis]) -> list[ActionRecommendation]:
    from .nodes.recommendation import RecommendationNode
    node = RecommendationNode()
    recommendations: list[ActionRecommendation] = []
    for hypothesis in hypotheses:
        if hypothesis.status == "suppressed":
            continue
        recommendations.append(node.recommend_actions(hypothesis))
    return recommendations


def run_demo_pipeline(competitor_name: str = "HubSpot") -> PipelineResult:
    dataset = load_demo_dataset()

    from .forum_tracker import AsyncForumTracker
    tracker = AsyncForumTracker()
    tracker.start_background_discovery(competitor_name)

    footprint = discover_sources(dataset, competitor_name)
    signals = monitor_signals(dataset, competitor_name)
    hypotheses = synthesize_hypotheses(competitor_name, signals)
    recommendations = recommend_actions(hypotheses)
    return PipelineResult(
        competitor_name=competitor_name,
        footprint=footprint,
        signals=signals,
        hypotheses=hypotheses,
        recommendations=recommendations,
    )


def result_to_dict(result: PipelineResult) -> dict[str, Any]:
    return asdict(result)


def _build_langgraph():
    try:
        from langgraph.graph import END, StateGraph
    except ModuleNotFoundError:
        return None

def _build_langgraph():
    try:
        from langgraph.graph import END, StateGraph
        from langgraph.checkpoint.memory import MemorySaver
        from typing import TypedDict
    except ModuleNotFoundError:
        return None

    class AgentState(TypedDict):
        competitor_name: str
        footprint: list[Any]
        signals: list[Any]
        hypotheses: list[Any]
        recommendations: list[Any]

    def hypothesis_node(state: AgentState) -> dict[str, Any]:
        competitor_name = state.get("competitor_name", "HubSpot")
        result = run_demo_pipeline(competitor_name)
        return {
            "footprint": result.footprint,
            "signals": result.signals,
            "hypotheses": result.hypotheses
        }

    def recommendation_node(state: AgentState) -> dict[str, Any]:
        hypotheses = state.get("hypotheses", [])
        recs = recommend_actions(hypotheses)
        return {
            "recommendations": recs
        }

    builder = StateGraph(AgentState)
    builder.add_node("hypothesis", hypothesis_node)
    builder.add_node("recommendation", recommendation_node)
    
    builder.set_entry_point("hypothesis")
    builder.add_edge("hypothesis", "recommendation")
    builder.add_edge("recommendation", END)
    
    memory = MemorySaver()
    return builder.compile(checkpointer=memory, interrupt_after=["hypothesis"])


graph = _build_langgraph()

