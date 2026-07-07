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
            print(f"[SerpApi Client] Skipping query (No API key found): '{query}'")
            return []
        
        # Simple HTTP request to SerpAPI using standard urllib
        params = {
            "q": query,
            "api_key": self.serpapi_key,
            "engine": "google"
        }
        url = f"https://serpapi.com/search?{urllib.parse.urlencode(params)}"
        print(f"[SerpApi Client] Firing SerpApi Query: '{query}'")
        
        try:
            req = urllib.request.Request(
                url, 
                headers={"User-Agent": "Competitive-Intelligence-Agent/1.0 (resilience-crawling; respect-robots)"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                results = data.get("organic_results", [])
                links = [r.get("link") for r in results if r.get("link")]
                print(f"[SerpApi Client] Fetched {len(links)} results for query '{query}': {links[:3]}...")
                return links
        except Exception as e:
            print(f"[SerpApi Client Error] Query failed: '{query}' - Error: {e}")
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

        # 4. Rating Agency & Financial Reports
        rating_query = self._query_serpapi(f"{name_clean} credit rating SP Global Moodys fitch")
        rating_url = None
        if rating_query:
            rating_url = rating_query[0]
            confidence = 0.90
        else:
            rating_url = f"https://www.spglobal.com/ratings/en/search/?query={urllib.parse.quote(name_clean)}"
            confidence = 0.80

        footprints.append(FootprintSource(
            url=rating_url,
            source_type="news",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        # 5. Tech Talk & Engineering Videos
        techtalk_query = self._query_serpapi(f"{name_clean} tech talk youtube engineering blog")
        techtalk_url = None
        if techtalk_query:
            techtalk_url = techtalk_query[0]
            confidence = 0.88
        else:
            techtalk_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(name_clean + ' engineering')}"
            confidence = 0.80

        footprints.append(FootprintSource(
            url=techtalk_url,
            source_type="owned",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        # 6. Status, Outages, and RCAs
        status_query = self._query_serpapi(f"{name_clean} status page post mortem outage RCA")
        status_url = None
        if status_query:
            status_url = status_query[0]
            confidence = 0.95
        else:
            status_url = f"https://status.{name_lower}.com"
            confidence = 0.85

        footprints.append(FootprintSource(
            url=status_url,
            source_type="owned",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        # 7. Public Lawsuits & Litigation
        lawsuit_query = self._query_serpapi(f"{name_clean} lawsuit litigation court case public")
        lawsuit_url = None
        if lawsuit_query:
            lawsuit_url = lawsuit_query[0]
            confidence = 0.90
        else:
            lawsuit_url = f"https://dockets.justia.com/search?q={urllib.parse.quote(name_clean)}"
            confidence = 0.80

        footprints.append(FootprintSource(
            url=lawsuit_url,
            source_type="news",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        # 8. Reuters Financial & Corporate News
        reuters_query = self._query_serpapi(f"{name_clean} site:reuters.com")
        reuters_url = None
        if reuters_query:
            reuters_url = reuters_query[0]
            confidence = 0.94
        else:
            reuters_url = f"https://www.reuters.com/search/news?blob={urllib.parse.quote(name_clean)}"
            confidence = 0.82

        footprints.append(FootprintSource(
            url=reuters_url,
            source_type="news",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        # 9. Top Executive Business News Interviews
        interview_query = self._query_serpapi(f"{name_clean} CEO executive interview Bloomberg CNBC TechCrunch WSJ")
        interview_url = None
        if interview_query:
            interview_url = interview_query[0]
            confidence = 0.92
        else:
            interview_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(name_clean + ' CEO interview Bloomberg CNBC')}"
            confidence = 0.80

        footprints.append(FootprintSource(
            url=interview_url,
            source_type="news",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        # 10. Dark Web Threat Intelligence & Leaks
        darkweb_query = self._query_serpapi(f"{name_clean} dark web leaks database ransomware forum onion")
        darkweb_url = None
        if darkweb_query:
            darkweb_url = darkweb_query[0]
            confidence = 0.90
        else:
            darkweb_url = f"http://{name_lower}leakstor.onion"
            confidence = 0.70

        footprints.append(FootprintSource(
            url=darkweb_url,
            source_type="news",
            confidence=confidence,
            status="monitoring",
            monitoring_priority="medium"
        ))

        return footprints
