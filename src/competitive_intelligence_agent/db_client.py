import os
import sqlite3

class DBClient:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        # Ensure target data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. Competitors metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitors (
                name TEXT PRIMARY KEY,
                domain TEXT NOT NULL
            );
        """)

        # 2. Discovered footprints/sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS discovered_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                url TEXT NOT NULL,
                source_type TEXT CHECK(source_type IN ('owned', 'social', 'customer', 'news', 'jobs', 'community')) NOT NULL,
                confidence REAL NOT NULL,
                status TEXT CHECK(status IN ('monitoring', 'ignored')) NOT NULL,
                monitoring_priority TEXT CHECK(monitoring_priority IN ('high', 'medium', 'low')) NOT NULL,
                FOREIGN KEY(competitor_name) REFERENCES competitors(name) ON DELETE CASCADE
            );
        """)

        # 3. Feedback log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                vote TEXT CHECK(vote IN ('thumbs_up', 'thumbs_down')) NOT NULL,
                comments TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(competitor_name) REFERENCES competitors(name) ON DELETE CASCADE
            );
        """)

        # 4. Website snapshots table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS website_snapshots (
                url TEXT PRIMARY KEY,
                html_content TEXT NOT NULL,
                last_checked TEXT NOT NULL
            );
        """)

        # 5. Job listings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                title TEXT NOT NULL,
                department TEXT NOT NULL,
                posted_date TEXT NOT NULL,
                is_new INTEGER DEFAULT 1,
                UNIQUE(competitor_name, title, department)
            );
        """)

        # 6. Competitor memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competitor_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competitor_name TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                summary TEXT NOT NULL,
                confidence_level REAL NOT NULL,
                last_observed TEXT NOT NULL,
                UNIQUE(competitor_name, pattern_type)
            );
        """)

        # Seed initial competitors and sources if empty
        cursor.execute("SELECT COUNT(*) FROM competitors")
        if cursor.fetchone()[0] == 0:
            try:
                import json
                from pathlib import Path
                package_root = Path(__file__).resolve().parents[2]
                demo_path = package_root / "data" / "demo_signals.json"
                if demo_path.exists():
                    with open(demo_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for comp_name, comp_data in data.get("competitors", {}).items():
                        domain = f"https://www.{comp_name.lower().replace(' ', '')}.com"
                        cursor.execute(
                            "INSERT OR IGNORE INTO competitors (name, domain) VALUES (?, ?)",
                            (comp_name, domain)
                        )
                        for src in comp_data.get("footprint", []):
                            cursor.execute(
                                """
                                INSERT INTO discovered_sources (competitor_name, url, source_type, confidence, status, monitoring_priority)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    comp_name,
                                    src["url"],
                                    src["source_type"],
                                    src["confidence"],
                                    src["status"],
                                    src.get("monitoring_priority", "medium")
                                )
                            )
            except Exception:
                pass

        conn.commit()
        conn.close()



