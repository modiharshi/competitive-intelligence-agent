import unittest

from competitive_intelligence_agent.pipeline import run_demo_pipeline
from competitive_intelligence_agent.schemas import SignalEvent, StrategicHypothesis


class PipelineTests(unittest.TestCase):
    def test_demo_pipeline_generates_grounded_recommendation(self):
        result = run_demo_pipeline("HubSpot")

        self.assertGreaterEqual(len(result.footprint), 2)
        self.assertEqual(len(result.hypotheses), 1)
        self.assertEqual(result.hypotheses[0].status, "active")
        self.assertGreaterEqual(result.hypotheses[0].confidence_score, 0.7)
        self.assertGreaterEqual(len(result.hypotheses[0].sources), 2)
        self.assertEqual(len(result.recommendations), 1)

    def test_signal_category_is_constrained(self):
        with self.assertRaises(ValueError):
            SignalEvent(
                id="sig-invalid",
                competitor_name="Example",
                source_url="https://example.com",
                category="Rumor",
                content_diff="Unsupported category.",
                timestamp="2026-01-01T00:00:00+00:00",
            )

    def test_low_confidence_hypothesis_must_be_suppressed(self):
        with self.assertRaises(ValueError):
            StrategicHypothesis(
                id="hyp-low",
                competitor_name="Example",
                theme="Weak signal",
                summary="Insufficient confidence.",
                confidence_score=0.4,
                time_horizon="Long-Term",
                supporting_signals=["sig-1"],
                signal_relations=[],
                sources=["https://example.com"],
            )


if __name__ == "__main__":
    unittest.main()
