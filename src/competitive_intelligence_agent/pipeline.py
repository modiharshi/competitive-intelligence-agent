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
    agent = DiscoveryAgent()
    return agent.discover_footprints(competitor_name)



def monitor_signals(dataset: dict[str, Any], competitor_name: str) -> list[SignalEvent]:
    from .nodes.classification import ClassificationNode
    node = ClassificationNode()
    records = dataset["competitors"].get(competitor_name, {}).get("signals", [])
    
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
    if competitor_name not in dataset["competitors"]:
        available = ", ".join(sorted(dataset["competitors"]))
        raise ValueError(f"unknown competitor '{competitor_name}'. Available demo competitors: {available}")

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

