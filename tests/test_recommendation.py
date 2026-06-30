import os
import unittest
from competitive_intelligence_agent.nodes.recommendation import RecommendationNode
from competitive_intelligence_agent.schemas import StrategicHypothesis
from competitive_intelligence_agent.db_client import DBClient

class TestRecommendationNode(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_recommendation.db"
        # Ensure clean database
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass
        self.db_client = DBClient(self.db_path)
        self.node = RecommendationNode(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_recommendation_few_shot_injection(self):
        # Insert test feedback records directly into SQLite
        conn = self.db_client.get_connection()
        cursor = conn.cursor()
        
        # 1. Insert competitor metadata to satisfy foreign key constraint if any
        cursor.execute("INSERT INTO competitors (name, domain) VALUES ('HubSpot', 'https://hubspot.com')")
        
        # 2. Insert thumbs_up feedback (should be injected)
        cursor.execute("""
            INSERT INTO feedback (competitor_name, hypothesis_id, vote, comments, timestamp)
            VALUES ('HubSpot', 'hyp-1', 'thumbs_up', 'Focus recommendations heavily on defensive product actions', '2026-06-24T12:00:00Z')
        """)
        
        # 3. Insert thumbs_down feedback (should be ignored)
        cursor.execute("""
            INSERT INTO feedback (competitor_name, hypothesis_id, vote, comments, timestamp)
            VALUES ('HubSpot', 'hyp-2', 'thumbs_down', 'Irrelevant feedback suggestion', '2026-06-24T12:05:00Z')
        """)
        
        conn.commit()
        conn.close()

        # Build dummy StrategicHypothesis
        hyp = StrategicHypothesis(
            id="hyp-hubspot-product",
            competitor_name="HubSpot",
            theme="HubSpot product movement",
            summary="Grounded strategic prediction.",
            confidence_score=0.85,
            time_horizon="Short-Term",
            supporting_signals=["sig-1"],
            signal_relations=[],
            sources=["https://hubspot.com/pricing"],
            status="active"
        )

        # Get recommendations
        rec = self.node.recommend_actions(hyp)

        # Assertions
        self.assertEqual(rec.hypothesis_id, hyp.id)
        self.assertEqual(rec.priority, "High")
        
        # Verify that only the thumbs-up record comments are injected
        self.assertIn("Focus recommendations heavily on defensive product actions", rec.reasoning)
        self.assertNotIn("Irrelevant feedback suggestion", rec.reasoning)

        # Verify get_few_shot_examples explicitly
        few_shots = self.node.get_few_shot_examples()
        self.assertEqual(len(few_shots), 1)
        self.assertEqual(few_shots[0].vote, "thumbs_up")
        self.assertEqual(few_shots[0].comments, "Focus recommendations heavily on defensive product actions")

if __name__ == "__main__":
    unittest.main()
