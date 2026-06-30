import unittest
from datetime import datetime, UTC
from competitive_intelligence_agent.nodes.intelligence import IntelligenceAgent
from competitive_intelligence_agent.schemas import SignalEvent

class TestIntelligenceAgent(unittest.TestCase):
    def test_timeline_sorting_and_clustering(self):
        agent = IntelligenceAgent()
        
        # Create signals spread across dates
        sig1 = SignalEvent(
            id="sig-1",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Product",
            content_diff="V1 launch",
            timestamp="2026-05-01T00:00:00+00:00"
        )
        sig2 = SignalEvent(
            id="sig-2",
            competitor_name="HubSpot",
            source_url="https://example.com/2",
            category="Hiring",
            content_diff="Spike",
            timestamp="2026-05-15T00:00:00+00:00"  # 14 days later (same cluster)
        )
        sig3 = SignalEvent(
            id="sig-3",
            competitor_name="HubSpot",
            source_url="https://example.com/3",
            category="Pricing",
            content_diff="New pricing structure",
            timestamp="2026-06-15T00:00:00+00:00"  # 45 days after sig1 (new cluster)
        )
        
        signals = [sig3, sig1, sig2]  # Unsorted input list
        
        clusters = agent.correlate_timeline(signals)
        
        self.assertEqual(len(clusters), 2)
        
        # First cluster has sig1 and sig2 (within 30 days)
        self.assertEqual(len(clusters[0]), 2)
        self.assertEqual(clusters[0][0].id, "sig-1")
        self.assertEqual(clusters[0][1].id, "sig-2")
        
        # Second cluster has sig3
        self.assertEqual(len(clusters[1]), 1)
        self.assertEqual(clusters[1][0].id, "sig-3")

if __name__ == "__main__":
    unittest.main()
