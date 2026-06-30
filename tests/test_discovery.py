import unittest
from unittest.mock import patch, MagicMock
from competitive_intelligence_agent.discovery import DiscoveryAgent
from competitive_intelligence_agent.schemas import FootprintSource

class TestDiscoveryAgent(unittest.TestCase):
    def test_discovery_heuristics_offline(self):
        agent = DiscoveryAgent()
        sources = agent.discover_footprints("HubSpot")
        
        # Verify default list of sources are returned
        self.assertEqual(len(sources), 5)
        
        # Check source types and attributes
        source_types = [s.source_type for s in sources]
        self.assertIn("owned", source_types)
        self.assertIn("social", source_types)
        self.assertIn("news", source_types)
        
        # Check confidence ranges
        for source in sources:
            self.assertTrue(0.0 <= source.confidence <= 1.0)
            self.assertTrue(source.url.startswith("https://"))

    @patch("urllib.request.urlopen")
    def test_discovery_with_mocked_serpapi(self, mock_urlopen):
        # Mock SerpAPI response structure
        mock_response = MagicMock()
        mock_response.read.return_value = json_data = b"""
        {
            "organic_results": [
                {"link": "https://www.hubspot.com/custom-found-url"}
            ]
        }
        """
        mock_urlopen.return_value.__enter__.return_value = mock_response

        agent = DiscoveryAgent(serpapi_key="mock_key")
        sources = agent.discover_footprints("HubSpot")
        
        # Verify the custom found URL from the mocked search results was used
        found_urls = [s.url for s in sources]
        self.assertIn("https://www.hubspot.com/custom-found-url", found_urls)

if __name__ == "__main__":
    unittest.main()
