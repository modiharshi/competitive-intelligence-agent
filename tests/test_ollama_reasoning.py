import unittest
from unittest.mock import patch, MagicMock
from competitive_intelligence_agent.ollama_client import call_ollama
from competitive_intelligence_agent.nodes.classification import ClassificationNode

class TestOllamaReasoning(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_call_ollama_success(self, mock_urlopen):
        # Mock response from Ollama
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"message": {"content": "{\\"category\\": \\"Pricing\\"}"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        messages = [{"role": "user", "content": "test"}]
        result = call_ollama(messages, response_json=True)
        self.assertIsNotNone(result)
        self.assertIn("Pricing", result)

    @patch("urllib.request.urlopen")
    def test_call_ollama_failure_fallback(self, mock_urlopen):
        # Mock urlopen to raise an exception
        mock_urlopen.side_effect = Exception("Connection refused")

        messages = [{"role": "user", "content": "test"}]
        result = call_ollama(messages)
        self.assertIsNone(result)

    @patch("competitive_intelligence_agent.ollama_client.call_ollama")
    def test_classification_fallback(self, mock_call_ollama):
        # Mock Ollama call to fail
        mock_call_ollama.return_value = None
        
        node = ClassificationNode()
        category = node._call_llm_classify("This is pricing change description")
        self.assertEqual(category, "Pricing")

if __name__ == "__main__":
    unittest.main()
