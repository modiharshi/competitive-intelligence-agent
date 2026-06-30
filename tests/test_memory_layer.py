import unittest
import os
from competitive_intelligence_agent.nodes.memory_layer import CompetitorMemoryNode
from competitive_intelligence_agent.db_client import DBClient
from competitive_intelligence_agent.schemas import StrategicHypothesis

class TestCompetitorMemory(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_memory_app.db"
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

    def test_memory_layer_persistence_and_conflict_updates(self):
        node = CompetitorMemoryNode(self.db_path)
        
        hyp = StrategicHypothesis(
            id="hyp-hubspot-pricing",
            competitor_name="HubSpot",
            theme="HubSpot pricing movement",
            summary="pricing modifications detected",
            confidence_score=0.88,
            time_horizon="Short-Term",
            supporting_signals=["sig-1", "sig-2"],
            signal_relations=[],
            sources=["https://example.com"]
        )
        
        # Persist memory first time
        record = node.persist_hypothesis_to_memory(hyp)
        self.assertEqual(record["competitor_name"], "HubSpot")
        self.assertEqual(record["pattern_type"], "pricing_strategy")
        self.assertEqual(record["confidence_level"], 0.88)
        self.assertIn("pricing modifications", record["summary"])
        
        # Update hypothesis confidence and summary, then persist again to trigger SQLite ON CONFLICT
        hyp_updated = StrategicHypothesis(
            id="hyp-hubspot-pricing",
            competitor_name="HubSpot",
            theme="HubSpot pricing movement",
            summary="higher confidence pricing modifications",
            confidence_score=0.95,
            time_horizon="Short-Term",
            supporting_signals=["sig-1", "sig-2", "sig-3"],
            signal_relations=[],
            sources=["https://example.com"]
        )
        
        updated_record = node.persist_hypothesis_to_memory(hyp_updated)
        self.assertEqual(updated_record["confidence_level"], 0.95)
        self.assertIn("higher confidence", updated_record["summary"])

if __name__ == "__main__":
    unittest.main()
