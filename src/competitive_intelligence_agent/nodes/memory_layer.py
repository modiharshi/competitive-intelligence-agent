from datetime import datetime
from typing import List, Dict, Any
from ..db_client import DBClient
from ..schemas import StrategicHypothesis

class CompetitorMemoryNode:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_client = DBClient(db_path)

    def _determine_pattern_type(self, theme: str) -> str:
        theme_lower = theme.lower()
        if "pricing" in theme_lower:
            return "pricing_strategy"
        elif "hiring" in theme_lower:
            return "hiring_pattern"
        elif "product" in theme_lower:
            return "product_roadmap"
        else:
            return "market_expansion"

    def persist_hypothesis_to_memory(self, hypothesis: StrategicHypothesis) -> Dict[str, Any]:
        competitor_name = hypothesis.competitor_name
        pattern_type = self._determine_pattern_type(hypothesis.theme)
        
        # Build memory pattern summary
        summary = (
            f"Observed theme '{hypothesis.theme}' with summary: {hypothesis.summary}. "
            f"Supporting signals: {', '.join(hypothesis.supporting_signals)}."
        )
        
        conn = self.db_client.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        # Insert or update memory record in SQLite
        cursor.execute("""
            INSERT INTO competitor_memory (competitor_name, pattern_type, summary, confidence_level, last_observed)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(competitor_name, pattern_type) DO UPDATE SET
                summary = excluded.summary,
                confidence_level = excluded.confidence_level,
                last_observed = excluded.last_observed;
        """, (competitor_name, pattern_type, summary, hypothesis.confidence_score, now))
        
        conn.commit()
        
        # Query the updated record to return
        cursor.execute("""
            SELECT id, competitor_name, pattern_type, summary, confidence_level, last_observed 
            FROM competitor_memory 
            WHERE competitor_name = ? AND pattern_type = ?;
        """, (competitor_name, pattern_type))
        row = cursor.fetchone()
        conn.close()
        
        # Mock ChromaDB Vector DB collection update placeholder
        self._sync_vector_store(competitor_name, pattern_type, summary)
        
        return {
            "id": row["id"],
            "competitor_name": row["competitor_name"],
            "pattern_type": row["pattern_type"],
            "summary": row["summary"],
            "confidence_level": row["confidence_level"],
            "last_observed": row["last_observed"]
        }

    def _sync_vector_store(self, competitor_name: str, pattern_type: str, summary: str):
        # Mock interface for ChromaDB vector embeddings
        try:
            import chromadb
            # If chromadb library is resolved, we can run mock initialization 
            # to verify configuration runs without breaking.
            pass
        except Exception:
            pass
