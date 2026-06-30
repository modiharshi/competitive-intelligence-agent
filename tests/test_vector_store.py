import unittest
import shutil
import os
from competitive_intelligence_agent.vector_store import VectorStoreClient
from competitive_intelligence_agent.schemas import SignalEvent

class TestVectorStoreClient(unittest.TestCase):
    def setUp(self):
        self.persist_dir = "data/test_chromadb"
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
        self.client = VectorStoreClient(self.persist_dir)

    def tearDown(self):
        if os.path.exists(self.persist_dir):
            try:
                shutil.rmtree(self.persist_dir)
            except Exception:
                pass

    def test_indexing_and_search_retrieval(self):
        sig = SignalEvent(
            id="sig-vector-1",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Product",
            content_diff="Our team launched a new LLM-based dashboard feature.",
            timestamp="2026-05-01T00:00:00+00:00"
        )
        
        self.client.index_signal(sig)
        
        # Test query retrieval by keywords
        results = self.client.search_signals("LLM dashboard", competitor_name="HubSpot")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "sig-vector-1")
        self.assertEqual(results[0]["competitor_name"], "HubSpot")
        self.assertIn("LLM-based dashboard", results[0]["content_diff"])

if __name__ == "__main__":
    unittest.main()
