import os
from typing import List, Dict, Any
from .schemas import SignalEvent

class VectorStoreClient:
    def __init__(self, persist_dir: str = ".chromadb"):
        self.persist_dir = persist_dir
        self.chroma_client = None
        self.collection = None
        self.fallback_db = {} # Simple in-memory fallback dict

        try:
            # pyrefly: ignore [missing-import]
            import chromadb
            # Disable telemetry and start persistent client
            from chromadb.config import Settings
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.chroma_client.get_or_create_collection("signals")
        except Exception:
            pass

    def index_signal(self, signal: SignalEvent):
        self.fallback_db[signal.id] = {
            "id": signal.id,
            "competitor_name": signal.competitor_name,
            "source_url": signal.source_url,
            "category": signal.category,
            "content_diff": signal.content_diff,
            "timestamp": signal.timestamp
        }
        
        if self.collection is not None:
            try:
                self.collection.add(
                    documents=[signal.content_diff],
                    metadatas=[{
                        "competitor_name": signal.competitor_name,
                        "source_url": signal.source_url,
                        "category": signal.category,
                        "timestamp": signal.timestamp
                    }],
                    ids=[signal.id]
                )
            except Exception:
                pass

    def search_signals(self, query: str, competitor_name: str = None, limit: int = 3) -> List[Dict[str, Any]]:
        if self.collection is not None:
            try:
                where_clause = {}
                if competitor_name:
                    where_clause["competitor_name"] = competitor_name
                    
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where=where_clause if where_clause else None
                )
                
                hits = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0]
                    ids = results["ids"][0]
                    for i in range(len(docs)):
                        hits.append({
                            "id": ids[i],
                            "content_diff": docs[i],
                            "competitor_name": metas[i].get("competitor_name"),
                            "source_url": metas[i].get("source_url"),
                            "category": metas[i].get("category"),
                            "timestamp": metas[i].get("timestamp")
                        })
                return hits
            except Exception:
                pass

        # Fallback local keyword index query
        query_words = set(query.lower().split())
        matches = []
        for sig_id, sig in self.fallback_db.items():
            if competitor_name and sig["competitor_name"] != competitor_name:
                continue
                
            content = sig["content_diff"].lower()
            score = sum(1 for w in query_words if w in content)
            
            if score > 0 or not query_words:
                matches.append((score, sig))
                
        matches.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in matches[:limit]]
