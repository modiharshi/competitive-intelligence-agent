"""Shared contracts for the competitive intelligence pipeline.

The production architecture calls for Pydantic models at every agent edge.
This MVP keeps the same contract boundaries with dependency-light dataclasses
so the demo and tests run before third-party dependencies are installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

SignalCategory = Literal[
    "Product",
    "Pricing",
    "Hiring",
    "Marketing",
    "Partnerships",
    "Funding",
    "Expansion",
    "Leadership",
    "Customer Sentiment",
    "Community Activity",
    "Technical",
]

SOURCE_TYPES = {"owned", "social", "customer", "news", "jobs", "community"}
SIGNAL_CATEGORIES = {
    "Product",
    "Pricing",
    "Hiring",
    "Marketing",
    "Partnerships",
    "Funding",
    "Expansion",
    "Leadership",
    "Customer Sentiment",
    "Community Activity",
    "Technical",
}
RELATION_TYPES = {"precedes", "amplifies", "contradicts", "supports", "causes"}
RESPONSE_CATEGORIES = {
    "Product Response",
    "Marketing Response",
    "Sales Enablement",
    "Customer Retention",
    "Strategic Initiatives",
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def require_range(name: str, value: float, minimum: float = 0.0, maximum: float = 1.0) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


@dataclass(frozen=True)
class FootprintSource:
    url: str
    source_type: Literal["owned", "social", "customer", "news", "jobs", "community"]
    confidence: float
    status: Literal["monitoring", "ignored"] = "monitoring"
    monitoring_priority: Literal["high", "medium", "low"] = "medium"

    def __post_init__(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("source url must be absolute")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(f"unsupported source_type: {self.source_type}")
        require_range("confidence", self.confidence)


@dataclass(frozen=True)
class SignalEvent:
    id: str
    competitor_name: str
    source_url: str
    category: SignalCategory
    content_diff: str
    timestamp: str
    source_reliability: Literal["high", "medium", "low"] = "medium"
    impact_score: float = 0.5

    def __post_init__(self) -> None:
        if self.category not in SIGNAL_CATEGORIES:
            raise ValueError(f"unsupported signal category: {self.category}")
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError("signal source_url must be absolute")
        require_range("impact_score", self.impact_score)


@dataclass(frozen=True)
class SignalRelation:
    source_id: str
    target_id: str
    relation_type: Literal["precedes", "amplifies", "contradicts", "supports", "causes"]

    def __post_init__(self) -> None:
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(f"unsupported relation_type: {self.relation_type}")


@dataclass(frozen=True)
class StrategicHypothesis:
    id: str
    competitor_name: str
    theme: str
    summary: str
    confidence_score: float
    time_horizon: Literal["Short-Term", "Mid-Term", "Long-Term"]
    supporting_signals: list[str]
    signal_relations: list[SignalRelation]
    sources: list[str]
    status: Literal["active", "suppressed"] = "active"

    def __post_init__(self) -> None:
        require_range("confidence_score", self.confidence_score)
        if not self.sources:
            raise ValueError("hypotheses require at least one citation")
        if self.confidence_score < 0.7 and self.status != "suppressed":
            raise ValueError("hypotheses below 70% confidence must be suppressed")


@dataclass(frozen=True)
class ActionRecommendation:
    id: str
    hypothesis_id: str
    category: str
    recommended_action: str
    reasoning: str
    priority: Literal["High", "Medium", "Low"]
    effort: Literal["High", "Medium", "Low"]
    strategic_posture: Literal["Defensive", "Offensive", "Opportunistic"]
    expected_outcome: str
    supporting_evidence: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.category not in RESPONSE_CATEGORIES:
            raise ValueError(f"unsupported recommendation category: {self.category}")
        if not self.supporting_evidence:
            raise ValueError("recommendations require supporting evidence")


@dataclass(frozen=True)
class FeedbackRecord:
    competitor_name: str
    hypothesis_id: str
    vote: Literal["thumbs_up", "thumbs_down"]
    comments: str = ""
    timestamp: str = field(default_factory=utc_now_iso)



@dataclass(frozen=True)
class EarlyWarningAlert:
    id: str
    hypothesis_id: str
    early_warning_score: float
    urgency: Literal["High", "Medium", "Low"]
    business_impact: Literal["Critical", "Major", "Minor"]
    threat_description: str


@dataclass(frozen=True)
class PipelineResult:
    competitor_name: str
    footprint: list[FootprintSource]
    signals: list[SignalEvent]
    hypotheses: list[StrategicHypothesis]
    recommendations: list[ActionRecommendation]
    generated_at: str = field(default_factory=utc_now_iso)
    executive_summary: str = ""
    intelligence_pillars: dict = field(default_factory=dict)
    strategic_risks: list[str] = field(default_factory=list)
    strategic_opportunities: list[str] = field(default_factory=list)
    watch_list: list[str] = field(default_factory=list)


# Pydantic Schemas for V2 Pipeline
try:
    from pydantic import BaseModel, Field
    from typing import List, Dict, Optional

    class V2FootprintSource(BaseModel):
        url: str
        source_type: Literal['website', 'rss', 'careers', 'changelog', 'documentation', 'api_docs', 'newsroom']
        confidence_score: float
        monitoring_priority: Literal['high', 'medium', 'low']

    class V2RawEvent(BaseModel):
        id: str
        source_url: str
        content_hash: str
        raw_content: str
        fetched_timestamp: str

    class V2NormalizedSignal(BaseModel):
        id: str
        raw_event_id: str
        title: str
        summary: str
        key_changes: str
        url: str
        timestamp: str

    class V2ClassifiedSignal(BaseModel):
        id: str
        normalized_signal_id: str
        category: Literal['Product', 'Pricing', 'Hiring', 'Marketing', 'Partnerships', 'Funding', 'Expansion', 'Leadership', 'Customer Sentiment', 'Technical']
        impact_score: float
        confidence_score: float

    class V2BusinessTheme(BaseModel):
        theme_id: str
        theme_name: str
        confidence_score: float
        contributing_signal_ids: List[str]

    class V2CorrelationCluster(BaseModel):
        id: str
        theme_id: str
        signal_ids: List[str]
        earliest_timestamp: str
        latest_timestamp: str
        validation_status: Literal['passed', 'failed']

    class V2Hypothesis(BaseModel):
        id: str
        theme_id: str
        summary: str
        confidence_score: float
        time_horizon: Literal['Short-Term', 'Mid-Term', 'Long-Term']
        supporting_signals: List[str]
        sources: List[str]
        status: Literal['active', 'suppressed', 'insufficient_evidence']

    class V2Recommendation(BaseModel):
        id: str
        hypothesis_id: str
        recommended_action: str
        reasoning: str
        priority: Literal['High', 'Medium', 'Low']
        effort: Literal['High', 'Medium', 'Low']
        strategic_posture: Literal['Offensive', 'Defensive', 'Opportunistic']
        evidence_ids: List[str]

    class V2HITLFeedback(BaseModel):
        hypothesis_id: str
        vote: Literal['thumbs_up', 'thumbs_down']
        comments: Optional[str] = ""
        timestamp: str
except ImportError:
    pass
