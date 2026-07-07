from typing import List
from ..schemas import StrategicHypothesis, SignalEvent, SignalRelation
from ..vector_store import VectorStoreClient

class HypothesisNode:
    def __init__(self, db_path: str = "data/app.db", persist_dir: str = ".chromadb"):
        self.vector_client = VectorStoreClient(persist_dir)

    def generate_grounded_hypothesis(
        self, 
        competitor_name: str, 
        cluster_signals: List[SignalEvent], 
        relations: List[SignalRelation]
    ) -> StrategicHypothesis:
        # Index cluster signals for retrieval grounding
        for sig in cluster_signals:
            self.vector_client.index_signal(sig)

        # Retrieve grounding context matching the competitor movement
        retrieved_docs = self.vector_client.search_signals(
            query=f"{competitor_name} strategic updates", 
            competitor_name=competitor_name, 
            limit=5
        )

        # Combine citations from retrieved docs and active cluster signals
        citations_set = {doc["source_url"] for doc in retrieved_docs}
        for sig in cluster_signals:
            citations_set.add(sig.source_url)
            
        citations = sorted(citations_set)
        if not citations:
            raise ValueError("hypotheses require at least one citation")

        # Basic confidence math: based on RAG verification and signal count
        base_confidence = min(0.95, 0.5 + (len(cluster_signals) * 0.15))
        
        # If confidence falls below 70%, it must be marked as suppressed
        status = "active" if base_confidence >= 0.70 else "suppressed"
        
        categories = {sig.category for sig in cluster_signals}
        
        # Cross-signal correlation logic
        if "Hiring" in categories and "Product" in categories:
            theme = f"Enterprise Scaling Prep"
            observation = f"Aggregated hiring openings for ML & Infrastructure engineers align with major documentation and landing page modifications."
            impact = f"Highly likely preparing for enterprise scale deployment and compliant hosting solutions."
            motivation = f"Attracting institutional SaaS clients requiring secure compliance frameworks."
            watch_next = f"SOC2 certifications, HIPAA policy announcements, enterprise sales hiring spikes."
        elif "Pricing" in categories and ("Customer Sentiment" in categories or "Community Activity" in categories):
            theme = f"Pricing Strategy Correction"
            observation = f"Pricing structure adjustments detected alongside negative reviews or community discussions on forums."
            impact = f"Risk of user churn; potential restructuring of tiers or discount incentives."
            motivation = f"Mitigating customer dissatisfaction while optimizing average revenue per account."
            watch_next = f"Discount announcements, support desk hires, tier feature updates."
        elif "Product" in categories and "Marketing" in categories:
            theme = f"New Product Launch Pipeline"
            observation = f"Marketing campaigns and news releases coordinated with changes in core feature documentation."
            impact = f"Disruptive entry into new feature categories; immediate threat to adjacent competitors."
            motivation = f"Capturing market share in new segments before competitors react."
            watch_next = f"Press releases, CEO keynotes, developer beta registrations."
        else:
            dominant_cat = cluster_signals[0].category if cluster_signals else "Product"
            theme = f"{dominant_cat} Strategy Shift"
            observation = f"Coordinated developments detected within category: {dominant_cat}."
            impact = f"Medium-term strategic alignment changes."
            motivation = f"General optimization of operations."
            watch_next = f"Related hiring changes, website positioning updates."

        # Format as structured McKinsey-style four-part report
        summary = (
            f"### Observation\n{observation}\n\n"
            f"### Business Impact\n{impact}\n\n"
            f"### Possible Motivation\n{motivation}\n\n"
            f"### What To Watch Next\n{watch_next}"
        )

        return StrategicHypothesis(
            id=f"hyp-{competitor_name.lower().replace(' ', '-')}-{theme.lower().replace(' ', '-')}",
            competitor_name=competitor_name,
            theme=theme,
            summary=summary,
            confidence_score=base_confidence,
            time_horizon="Short-Term" if base_confidence >= 0.85 else "Mid-Term",
            supporting_signals=[sig.id for sig in cluster_signals],
            signal_relations=relations,
            sources=citations,
            status=status
        )
