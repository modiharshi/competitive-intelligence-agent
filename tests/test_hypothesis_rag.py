import unittest
import shutil
import os
from competitive_intelligence_agent.nodes.hypothesis import HypothesisNode
from competitive_intelligence_agent.schemas import SignalEvent

class TestHypothesisRAG(unittest.TestCase):
    def setUp(self):
        self.persist_dir = "data/test_hyp_chromadb"
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
        self.node = HypothesisNode(persist_dir=self.persist_dir)

    def tearDown(self):
        if os.path.exists(self.persist_dir):
            try:
                shutil.rmtree(self.persist_dir)
            except Exception:
                pass

    def test_hypothesis_generation_grounded_by_rag(self):
        sig1 = SignalEvent(
            id="sig-hyp-1",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Product",
            content_diff="Our team launched a new LLM-based dashboard feature.",
            timestamp="2026-05-01T00:00:00+00:00"
        )
        
        # Test generation with sufficient signals (confidence >= 70%)
        sig2 = SignalEvent(
            id="sig-hyp-2",
            competitor_name="HubSpot",
            source_url="https://example.com/2",
            category="Product",
            content_diff="Second launcher update.",
            timestamp="2026-05-02T00:00:00+00:00"
        )

        hyp = self.node.generate_grounded_hypothesis("HubSpot", [sig1, sig2], [])
        
        self.assertEqual(hyp.status, "active")
        self.assertGreaterEqual(hyp.confidence_score, 0.70)
        self.assertIn("https://example.com/1", hyp.sources)
        self.assertIn("https://example.com/2", hyp.sources)

    def test_low_confidence_hypothesis_is_suppressed(self):
        sig_weak = SignalEvent(
            id="sig-weak-1",
            competitor_name="HubSpot",
            source_url="https://example.com/1",
            category="Product",
            content_diff="minor tweak",
            timestamp="2026-05-01T00:00:00+00:00"
        )
        
        # Generating hypothesis with only 1 signal gives confidence = 0.5 + 0.15 = 0.65 (< 70%)
        # But wait! dataclass __post_init__ throws ValueError if confidence_score < 0.7 and status != "suppressed"
        # HypothesisNode should correctly mark status="suppressed" so it passes instantiation validation.
        hyp = self.node.generate_grounded_hypothesis("HubSpot", [sig_weak], [])
        self.assertEqual(hyp.status, "suppressed")
        self.assertLess(hyp.confidence_score, 0.70)

if __name__ == "__main__":
    unittest.main()
