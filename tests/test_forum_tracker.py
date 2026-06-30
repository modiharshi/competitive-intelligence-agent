import unittest
import os
import time
from competitive_intelligence_agent.forum_tracker import AsyncForumTracker
from competitive_intelligence_agent.db_client import DBClient

class TestAsyncForumTracker(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_forum_tracker.db"
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.client = DBClient(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_progressive_crawling_background_flow(self):
        tracker = AsyncForumTracker(self.db_path)
        
        # Start background discovery task (starts thread)
        thread = tracker.start_background_discovery("HubSpot")
        
        # Check that it runs in the background and does not block immediately
        self.assertTrue(thread.is_alive())
        
        # Join thread to wait for it to complete
        thread.join(timeout=3)
        
        # Check that sources were successfully written to the database
        conn = self.client.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url, source_type, confidence FROM discovered_sources WHERE competitor_name = 'HubSpot';")
        rows = cursor.fetchall()
        
        urls = [r[0] for r in rows]
        source_types = [r[1] for r in rows]
        
        self.assertIn("https://www.g2.com/products/hubspot/reviews", urls)
        self.assertIn("https://www.reddit.com/r/hubspot", urls)
        self.assertIn("community", source_types)
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
