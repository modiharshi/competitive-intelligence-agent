import unittest
from competitive_intelligence_agent.news_scraper import NewsScraper

class TestNewsScraper(unittest.TestCase):
    def test_rss_feed_parsing_valid(self):
        xml_data = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
        <channel>
            <title>HubSpot Press Releases</title>
            <link>https://www.hubspot.com</link>
            <description>News feed</description>
            <item>
                <title>HubSpot Launches New AI Tools</title>
                <link>https://www.hubspot.com/news/launches-ai</link>
                <description>We launched some amazing LLM integrations today.</description>
            </item>
            <item>
                <title>HubSpot Pricing Adjustment</title>
                <link>https://www.hubspot.com/news/pricing-update</link>
                <description>New plan changes are taking effect next month.</description>
            </item>
        </channel>
        </rss>
        """
        scraper = NewsScraper()
        items = scraper.parse_feed("https://example.com/rss", xml_data)
        
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "HubSpot Launches New AI Tools")
        self.assertEqual(items[0]["link"], "https://www.hubspot.com/news/launches-ai")
        self.assertEqual(items[0]["description"], "We launched some amazing LLM integrations today.")

    def test_rss_feed_parsing_malformed(self):
        malformed_xml = "<html><body>Not an RSS feed</body></html>"
        scraper = NewsScraper()
        items = scraper.parse_feed("https://example.com/rss", malformed_xml)
        
        self.assertEqual(len(items), 0)

if __name__ == "__main__":
    unittest.main()
