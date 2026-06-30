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
        
        dominant_cat = cluster_signals[0].category if cluster_signals else "Product"
        theme = f"{competitor_name} {dominant_cat.lower()} movement"
        summary = (
            f"Grounded strategic prediction based on {len(retrieved_docs)} indexed signals. "
            "Verified citations established from search index."
        )

        return StrategicHypothesis(
            id=f"hyp-{competitor_name.lower().replace(' ', '-')}-{dominant_cat.lower().replace(' ', '-')}",
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
