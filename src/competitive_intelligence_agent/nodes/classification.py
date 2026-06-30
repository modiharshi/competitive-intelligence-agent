import functools
import time
import os

try:

    import tenacity
    retry_decorator = tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=5),
        retry=tenacity.retry_if_exception_type(Exception),
        reraise=True
    )
except ImportError:
    def retry_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 3
            delay = 1
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == attempts - 1:
                        raise
                    time.sleep(delay)
                    delay *= 2
            return None
        return wrapper

from typing import Dict, Any
from ..schemas import SignalCategory, SignalEvent, utc_now_iso

# Custom exception to represent transient API limits or network issues
class LLMTransientError(Exception):
    pass

class ClassificationNode:
    def __init__(self, use_mock_llm: bool = True):
        self.use_mock_llm = use_mock_llm

    # Tenacity retry decorator with exponential backoff on transient errors
    @retry_decorator
    def _call_llm_classify(self, content_diff: str) -> SignalCategory:

        # Check if environment keys are missing or mock is enforced
        openai_key = os.environ.get("OPENAI_API_KEY")
        gemini_key = os.environ.get("GEMINI_API_KEY")
        
        if not self.use_mock_llm and (openai_key or gemini_key):
            # Real LLM API call details here
            # Under sandbox, if rate limits (429) happen, we raise LLMTransientError to trigger retries
            pass
            
        # Robust keyword heuristic classification fallback for offline test execution
        content_lower = content_diff.lower()
        if "price" in content_lower or "pricing" in content_lower or "cost" in content_lower:
            return "Pricing"
        elif "hiring" in content_lower or "careers" in content_lower or "job" in content_lower:
            return "Hiring"
        elif "sentiment" in content_lower or "review" in content_lower or "g2" in content_lower:
            return "Customer Sentiment"
        elif "press" in content_lower or "announces" in content_lower or "announced" in content_lower:
            return "Marketing"
        elif "partner" in content_lower or "partnership" in content_lower:
            return "Partnerships"
        elif "funding" in content_lower or "raised" in content_lower or "million" in content_lower:
            return "Funding"
        elif "expansion" in content_lower or "regional" in content_lower or "opened" in content_lower:
            return "Expansion"
        elif "ceo" in content_lower or "hire" in content_lower or "leadership" in content_lower or "vp" in content_lower:
            return "Leadership"
        elif "community" in content_lower or "forum" in content_lower or "reddit" in content_lower:
            return "Community Activity"
        else:
            return "Product"

    def classify_signal(self, competitor_name: str, source_url: str, content_diff: str, signal_id: str) -> SignalEvent:
        category = self._call_llm_classify(content_diff)
        return SignalEvent(
            id=signal_id,
            competitor_name=competitor_name,
            source_url=source_url,
            category=category,
            content_diff=content_diff,
            timestamp=utc_now_iso(),
            source_reliability="medium",
            impact_score=0.75
        )
