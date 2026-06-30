import unittest
from competitive_intelligence_agent.nodes.early_warning import EarlyWarningEngine
from competitive_intelligence_agent.schemas import StrategicHypothesis

class TestEarlyWarningEngine(unittest.TestCase):
    def test_score_calculation_formula(self):
        engine = EarlyWarningEngine()
        
        # Test Case 1: High Urgency (Short-Term), Critical Impact (pricing)
        # Confidence = 0.90
        # Score = 0.90 * (0.4 * 1.0 + 0.6 * 1.0) = 0.90 * 1.0 = 90.0%
        hyp1 = StrategicHypothesis(
            id="hyp-1",
            competitor_name="HubSpot",
            theme="HubSpot pricing shift",
            summary="Updated prices",
            confidence_score=0.90,
            time_horizon="Short-Term",
            supporting_signals=[],
            signal_relations=[],
            sources=["https://example.com"]
        )
        alert1 = engine.calculate_threat_score(hyp1)
        self.assertEqual(alert1.early_warning_score, 90.0)
        self.assertEqual(alert1.urgency, "High")
        self.assertEqual(alert1.business_impact, "Critical")
        
        # Test Case 2: Medium Urgency (Mid-Term), Major Impact (product)
        # Confidence = 0.80
        # Score = 0.80 * (0.4 * 0.7 + 0.6 * 0.8) = 0.80 * (0.28 + 0.48) = 0.80 * 0.76 = 60.8%
        hyp2 = StrategicHypothesis(
            id="hyp-2",
            competitor_name="HubSpot",
            theme="HubSpot product update",
            summary="New feature",
            confidence_score=0.80,
            time_horizon="Mid-Term",
            supporting_signals=[],
            signal_relations=[],
            sources=["https://example.com"]
        )
        alert2 = engine.calculate_threat_score(hyp2)
        self.assertEqual(alert2.early_warning_score, 60.8)
        self.assertEqual(alert2.urgency, "Medium")
        self.assertEqual(alert2.business_impact, "Major")

if __name__ == "__main__":
    unittest.main()
