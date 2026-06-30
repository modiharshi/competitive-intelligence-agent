import unittest
import os
import sqlite3
from competitive_intelligence_agent.db_client import DBClient

class TestDBClient(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_app.db"
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.client = DBClient(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_wal_mode_enabled(self):
        conn = self.client.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), "wal")

    def test_tables_created(self):
        conn = self.client.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        self.assertIn("competitors", tables)
        self.assertIn("discovered_sources", tables)
        self.assertIn("feedback", tables)

if __name__ == "__main__":
    unittest.main()
