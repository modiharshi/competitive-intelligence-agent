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
        
        def trace_sql(sql_statement: str):
            # Print database queries to server side log
            print(f"[SQL Database Query] {sql_statement.strip()}")
            
        conn.set_trace_callback(trace_sql)
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

        # V2 Table: Companies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                domain TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # V2 Table: Footprint Sources
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS footprint_sources (
                id TEXT PRIMARY KEY,
                company_id TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source_type TEXT CHECK(source_type IN ('website', 'rss', 'careers', 'changelog', 'documentation', 'api_docs', 'newsroom')) NOT NULL,
                confidence_score REAL NOT NULL,
                monitoring_priority TEXT CHECK(monitoring_priority IN ('high', 'medium', 'low')) NOT NULL,
                FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Raw Events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_events (
                id TEXT PRIMARY KEY,
                source_url TEXT NOT NULL,
                content_hash TEXT UNIQUE NOT NULL,
                raw_content TEXT NOT NULL,
                fetched_timestamp TEXT NOT NULL
            );
        """)

        # V2 Table: Normalized Signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS normalized_signals (
                id TEXT PRIMARY KEY,
                raw_event_id TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_changes TEXT NOT NULL,
                url TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (raw_event_id) REFERENCES raw_events(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Classified Signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classified_signals (
                id TEXT PRIMARY KEY,
                normalized_signal_id TEXT UNIQUE NOT NULL,
                category TEXT CHECK(category IN ('Product', 'Pricing', 'Hiring', 'Marketing', 'Partnerships', 'Funding', 'Expansion', 'Leadership', 'Customer Sentiment', 'Technical')) NOT NULL,
                impact_score REAL NOT NULL,
                confidence_score REAL NOT NULL,
                FOREIGN KEY (normalized_signal_id) REFERENCES normalized_signals(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Business Themes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_themes (
                id TEXT PRIMARY KEY,
                theme_name TEXT NOT NULL,
                confidence_score REAL NOT NULL
            );
        """)

        # V2 Table: Business Theme-Signal Association Mapping
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS business_theme_signals (
                theme_id TEXT NOT NULL,
                signal_id TEXT NOT NULL,
                PRIMARY KEY (theme_id, signal_id),
                FOREIGN KEY (theme_id) REFERENCES business_themes(id) ON DELETE CASCADE,
                FOREIGN KEY (signal_id) REFERENCES classified_signals(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Correlation Clusters
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS correlation_clusters (
                id TEXT PRIMARY KEY,
                theme_id TEXT NOT NULL,
                signal_ids TEXT NOT NULL,
                earliest_timestamp TEXT NOT NULL,
                latest_timestamp TEXT NOT NULL,
                validation_status TEXT CHECK(validation_status IN ('passed', 'failed')) NOT NULL,
                FOREIGN KEY (theme_id) REFERENCES business_themes(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Hypotheses
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hypotheses (
                id TEXT PRIMARY KEY,
                theme_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                time_horizon TEXT CHECK(time_horizon IN ('Short-Term', 'Mid-Term', 'Long-Term')) NOT NULL,
                supporting_signals TEXT NOT NULL,
                sources TEXT NOT NULL,
                status TEXT CHECK(status IN ('active', 'suppressed', 'insufficient_evidence')) NOT NULL,
                FOREIGN KEY (theme_id) REFERENCES business_themes(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Recommendations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                hypothesis_id TEXT NOT NULL,
                recommended_action TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')) NOT NULL,
                effort TEXT CHECK(effort IN ('High', 'Medium', 'Low')) NOT NULL,
                strategic_posture TEXT CHECK(strategic_posture IN ('Offensive', 'Defensive', 'Opportunistic')) NOT NULL,
                evidence_ids TEXT NOT NULL,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id) ON DELETE CASCADE
            );
        """)

        # V2 Table: Human-In-The-Loop Feedback
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hitl_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hypothesis_id TEXT NOT NULL,
                vote TEXT CHECK(vote IN ('thumbs_up', 'thumbs_down')) NOT NULL,
                comments TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id) ON DELETE CASCADE
            );
        """)

        # Seed initial competitors and sources if empty
        cursor.execute("SELECT COUNT(*) FROM competitors")
        if cursor.fetchone()[0] == 0:
            try:
                import json
                import datetime
                from pathlib import Path
                package_root = Path(__file__).resolve().parents[2]
                demo_path = package_root / "data" / "demo_signals.json"
                if demo_path.exists():
                    with open(demo_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for comp_name, comp_data in data.get("competitors", {}).items():
                        domain = f"https://www.{comp_name.lower().replace(' ', '')}.com"
                        comp_id = comp_name.lower().replace(' ', '_')
                        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
                        
                        # Seed V1
                        cursor.execute(
                            "INSERT OR IGNORE INTO competitors (name, domain) VALUES (?, ?)",
                            (comp_name, domain)
                        )
                        # Seed V2
                        cursor.execute(
                            "INSERT OR IGNORE INTO companies (id, name, domain, created_at) VALUES (?, ?, ?, ?)",
                            (comp_id, comp_name, domain, created_at)
                        )
                        
                        for src in comp_data.get("footprint", []):
                            # Seed V1
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
                            # Seed V2
                            src_type = src["source_type"]
                            if src_type == "jobs":
                                src_type = "careers"
                            elif src_type == "community":
                                src_type = "rss"
                            elif src_type not in ['website', 'rss', 'careers', 'changelog', 'documentation', 'api_docs', 'newsroom']:
                                src_type = "website"
                                
                            src_id = f"src_{src_type}_{comp_id}"
                            cursor.execute(
                                """
                                INSERT OR IGNORE INTO footprint_sources (id, company_id, url, source_type, confidence_score, monitoring_priority)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    src_id,
                                    comp_id,
                                    src["url"],
                                    src_type,
                                    src["confidence"],
                                    src.get("monitoring_priority", "medium")
                                )
                            )
            except Exception:
                pass

        conn.commit()
        conn.close()



