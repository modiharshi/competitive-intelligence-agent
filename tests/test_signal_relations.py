import unittest
from competitive_intelligence_agent.nodes.intelligence import IntelligenceAgent
from competitive_intelligence_agent.schemas import SignalEvent

class TestSignalRelations(unittest.TestCase):
    def test_relationship_mapping_rules(self):
        agent = IntelligenceAgent()
        
        # 1. Test causes: Hiring preceding Product
        sig_hiring = SignalEvent(
            id="sig-hire",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Hiring",
            content_diff="Hiring AI engineers",
            timestamp="2026-05-01T00:00:00"
        )
        sig_product = SignalEvent(
            id="sig-prod",
            competitor_name="HubSpot",
            source_url="https://example.com/2",
            category="Product",
            content_diff="New AI feature launch",
            timestamp="2026-05-02T00:00:00"
        )
        
        relations1 = agent.map_relations([sig_hiring, sig_product])
        self.assertEqual(len(relations1), 1)
        self.assertEqual(relations1[0].relation_type, "causes")
        
        # 2. Test amplifies: Same category, increasing impact
        sig_prod_low = SignalEvent(
            id="sig-prod-1",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Product",
            content_diff="low impact product update",
            timestamp="2026-05-01T00:00:00",
            impact_score=0.4
        )
        sig_prod_high = SignalEvent(
            id="sig-prod-2",
            competitor_name="HubSpot",
            source_url="https://example.com/2",
            category="Product",
            content_diff="major roadmap launch",
            timestamp="2026-05-02T00:00:00",
            impact_score=0.9
        )
        relations2 = agent.map_relations([sig_prod_low, sig_prod_high])
        self.assertEqual(relations2[0].relation_type, "amplifies")

        # 3. Test contradicts: add vs remove
        sig_add = SignalEvent(
            id="sig-add",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Pricing",
            content_diff="added pricing tier",
            timestamp="2026-05-01T00:00:00"
        )
        sig_remove = SignalEvent(
            id="sig-remove",
            competitor_name="HubSpot",
            source_url="https://example.com/2",
            category="Pricing",
            content_diff="removed pricing tier",
            timestamp="2026-05-02T00:00:00"
        )
        relations3 = agent.map_relations([sig_add, sig_remove])
        self.assertEqual(relations3[0].relation_type, "contradicts")

if __name__ == "__main__":
    unittest.main()
