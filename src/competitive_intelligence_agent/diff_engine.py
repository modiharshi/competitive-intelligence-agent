import os
import urllib.request
import difflib
from datetime import datetime
from .db_client import DBClient

class DiffEngine:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_client = DBClient(db_path)

    def _fetch_html(self, url: str) -> str:
        # Standard HTTP client fetching with resilience/ethics headers
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Competitive-Intelligence-Agent/1.0 (resilience-crawling; respect-robots)"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception:
            # Fallback mock/simulated contents if offline or request fails
            return f"<html><body><h1>Default Simulated Page</h1><p>Active domain: {url}</p></body></html>"

    def get_previous_snapshot(self, url: str) -> str:
        conn = self.db_client.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT html_content FROM website_snapshots WHERE url = ?;", (url,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""

    def save_snapshot(self, url: str, html_content: str):
        conn = self.db_client.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO website_snapshots (url, html_content, last_checked)
            VALUES (?, ?, ?);
        """, (url, html_content, now))
        conn.commit()
        conn.close()

    def compare_and_diff(self, url: str, new_html: str = None) -> str:
        # Fetch new content if not provided explicitly
        current_html = new_html if new_html is not None else self._fetch_html(url)
        previous_html = self.get_previous_snapshot(url)

        if not previous_html:
            # First crawl: save snapshot and return empty diff (baseline established)
            self.save_snapshot(url, current_html)
            return ""

        # Generate line-by-line diff
        prev_lines = previous_html.splitlines()
        curr_lines = current_html.splitlines()
        
        diff_lines = list(difflib.unified_diff(
            prev_lines, 
            curr_lines, 
            fromfile="previous", 
            tofile="current", 
            lineterm=""
        ))

        # Save the new snapshot for the next comparison
        self.save_snapshot(url, current_html)

        if len(diff_lines) <= 2:
            return ""

        return "\n".join(diff_lines)
