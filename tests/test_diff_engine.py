import unittest
import os
from competitive_intelligence_agent.diff_engine import DiffEngine
from competitive_intelligence_agent.db_client import DBClient

class TestDiffEngine(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_diff_app.db"
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

    def test_first_crawl_establishes_baseline(self):
        engine = DiffEngine(self.db_path)
        url = "https://www.hubspot.com/pricing"
        html = "<html><body><h1>Pricing: $10/mo</h1></body></html>"
        
        # First comparison should establish baseline and return empty diff
        diff = engine.compare_and_diff(url, html)
        self.assertEqual(diff, "")
        
        # Verify it was saved in SQLite
        saved_html = engine.get_previous_snapshot(url)
        self.assertEqual(saved_html, html)

    def test_comparison_detects_changes(self):
        engine = DiffEngine(self.db_path)
        url = "https://www.hubspot.com/pricing"
        html_v1 = "<html><body><h1>Pricing: $10/mo</h1></body></html>"
        html_v2 = "<html><body><h1>Pricing: $15/mo</h1></body></html>"
        
        # First establish baseline
        engine.compare_and_diff(url, html_v1)
        
        # Second run should detect change and produce diff
        diff = engine.compare_and_diff(url, html_v2)
        
        # Verify diff contains modified price
        self.assertIn("$15/mo", diff)
        self.assertIn("$10/mo", diff)

    def test_no_changes_empty_diff(self):
        engine = DiffEngine(self.db_path)
        url = "https://www.hubspot.com/pricing"
        html = "<html><body><h1>Pricing: $10/mo</h1></body></html>"
        
        engine.compare_and_diff(url, html)
        diff = engine.compare_and_diff(url, html)
        
        self.assertEqual(diff, "")

if __name__ == "__main__":
    unittest.main()
