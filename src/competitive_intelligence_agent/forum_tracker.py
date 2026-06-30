import time
import threading
from typing import List
from .db_client import DBClient
from .schemas import FootprintSource

class AsyncForumTracker:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_client = DBClient(db_path)

    def _discover_and_save(self, competitor_name: str):
        # Simulate crawling latency of Tier 3 sources progressively
        name_clean = competitor_name.strip()
        name_lower = name_clean.lower().replace(" ", "")
        
        # 1. G2 Forum (simulated progressive fetch)
        time.sleep(0.5)  # non-blocking for main loop since it runs in a thread
        g2_url = f"https://www.g2.com/products/{name_lower}/reviews"
        self._save_to_db(competitor_name, g2_url, "community", 0.82)

        # 2. Reddit Community
        time.sleep(0.5)
        reddit_url = f"https://www.reddit.com/r/{name_lower}"
        self._save_to_db(competitor_name, reddit_url, "community", 0.78)

    def _save_to_db(self, competitor_name: str, url: str, source_type: str, confidence: float):
        conn = self.db_client.get_connection()
        cursor = conn.cursor()
        try:
            # Ensure competitor exists in competitors table first to satisfy foreign key
            cursor.execute(
                "INSERT OR IGNORE INTO competitors (name, domain) VALUES (?, ?)", 
                (competitor_name, f"https://www.{competitor_name.lower().replace(' ', '')}.com")
            )
            # Insert the discovered source
            cursor.execute("""
                INSERT INTO discovered_sources (competitor_name, url, source_type, confidence, status, monitoring_priority)
                VALUES (?, ?, ?, ?, 'monitoring', 'low')
            """, (competitor_name, url, source_type, confidence))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def start_background_discovery(self, competitor_name: str):
        thread = threading.Thread(target=self._discover_and_save, args=(competitor_name,), daemon=True)
        thread.start()
        return thread
