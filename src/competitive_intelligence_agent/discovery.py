import os
import json
import urllib.request
import urllib.parse
from typing import List
from .schemas import FootprintSource

class DiscoveryAgent:
    def __init__(self, serpapi_key: str = None):
        self.serpapi_key = serpapi_key or os.environ.get("SERPAPI_API_KEY")

    def _query_serpapi(self, query: str) -> List[str]:
        if not self.serpapi_key:
            return []
        
        # Simple HTTP request to SerpAPI using standard urllib
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "engine": "google"
        }
        url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
        
        try:
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Competitive-Intelligence-Agent/1.0 (resilience-crawling; respect-robots)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("organic_results", [])
                return [r.get("link") for r in results if r.get("link")]
        except Exception:
            # Graceful isolation on search API failures
            return []

    def discover_footprints(self, competitor_name: str) -> List[FootprintSource]:
        footprints = []
        name_clean = competitor_name.strip()
        name_lower = name_clean.lower().replace(" ", "")

        # 1. Main Website Domain
        domain = f"https://www.{name_lower}.com"
        # Try SerpAPI if key exists
        serp_links = self._query_serpapi(f"{name_clean} official website")
        if serp_links:
            domain = serp_links[0]
            confidence = 0.98
        else:
            confidence = 0.90  # Heuristic fallback confidence
            
        footprints.append(FootprintSource(
            url=domain,
            source_type="owned",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="high"
        ))

        # 2. Social Channels (GitHub, Twitter/X, LinkedIn)
        channels = [
            ("github", "https://github.com/", "social", 0.85),
            ("twitter", "https://twitter.com/", "social", 0.80),
            ("linkedin", "https://linkedin.com/company/", "social", 0.85)
        ]

        for service, base_url, source_type, base_conf in channels:
            serp_social = self._query_serpapi(f"{name_clean} official {service}")
            matched_url = None
            if serp_social:
                # Find the link that matches the social site base_url
                for link in serp_social:
                    if base_url in link:
                        matched_url = link
                        break
            
            if matched_url:
                footprints.append(FootprintSource(
                    url=matched_url,
                    source_type=source_type,
                    confidence=0.95,
                    status="monitoring",
                    monitoring_priority="medium"
                ))
            else:
                # Fallback to standard guess
                fallback_url = f"{base_url}{name_lower}"
                footprints.append(FootprintSource(
                    url=fallback_url,
                    source_type=source_type,
                    confidence=base_conf,
                    status="monitoring",
                    monitoring_priority="medium"
                ))

        # 3. News Feed
        news_query = self._query_serpapi(f"{name_clean} press releases newsroom")
        news_url = None
        if news_query:
            news_url = news_query[0]
            confidence = 0.92
        else:
            news_url = f"{domain}/news"
            confidence = 0.75

        footprints.append(FootprintSource(
            url=news_url,
            source_type="news",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        return footprints
