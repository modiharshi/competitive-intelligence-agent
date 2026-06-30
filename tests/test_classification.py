import unittest
from unittest.mock import MagicMock
from competitive_intelligence_agent.nodes.classification import ClassificationNode, LLMTransientError

class TestClassificationNode(unittest.TestCase):
    def test_signal_categories_classification(self):
        node = ClassificationNode()
        
        # Test keyword matching heuristic fallback
        sig_pricing = node.classify_signal("HubSpot", "https://hubspot.com", "We changed our pricing to $10/mo", "sig-1")
        self.assertEqual(sig_pricing.category, "Pricing")
        
        sig_hiring = node.classify_signal("HubSpot", "https://hubspot.com", "Looking for new Staff AI Engineers to join careers page", "sig-2")
        self.assertEqual(sig_hiring.category, "Hiring")

        sig_product = node.classify_signal("HubSpot", "https://hubspot.com", "Integrating a new dashboard automation feature", "sig-3")
        self.assertEqual(sig_product.category, "Product")

    def test_retry_on_transient_error(self):
        node = ClassificationNode()
        
        # Create a mock method that fails twice and succeeds on the third attempt
        call_count = 0
        original_classify = node._call_llm_classify
        
        def mock_call(content_diff: str):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise LLMTransientError("Simulated transient rate limit")
            return "Pricing"
            
        # Temporarily patch the inner call
        node._call_llm_classify = mock_call
        
        # Note: Since retry_decorator is applied at definition time, we need to test the decorated version.
        # But wait, mock_call is not decorated. Let's decorate mock_call to test the retry wrapper itself.
        from competitive_intelligence_agent.nodes.classification import retry_decorator
        
        decorated_mock = retry_decorator(mock_call)
        category = decorated_mock("We changed our pricing")
        
        self.assertEqual(category, "Pricing")
        self.assertEqual(call_count, 3)

if __name__ == "__main__":
    unittest.main()
