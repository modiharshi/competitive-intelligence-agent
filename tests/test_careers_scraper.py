import unittest
import os
from competitive_intelligence_agent.careers_scraper import CareersScraper
from competitive_intelligence_agent.db_client import DBClient

class TestCareersScraper(unittest.TestCase):
    def setUp(self):
        self.db_path = "data/test_careers_app.db"
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.client = DBClient(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_job_extraction_and_new_flagging(self):
        scraper = CareersScraper(self.db_path)
        url = "https://www.hubspot.com/careers"
        
        html_data = """
        <div class="job-post">
            <h3 class="title">Staff AI Engineer</h3>
            <span class="dept">Engineering</span>
            <span class="date">2026-06-20</span>
        </div>
        """
        
        # First sync: should insert and mark as is_new = True
        jobs = scraper.parse_and_sync_jobs("HubSpot", url, html_data)
        self.assertEqual(len(jobs), 1)
        self.assertTrue(jobs[0]["is_new"])
        
        # Verify stored details in database
        conn = self.client.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_new FROM job_listings WHERE competitor_name='HubSpot';")
        self.assertEqual(cursor.fetchone()[0], 1)
        
        # Second sync with same content: should detect it exists and return is_new = False
        jobs_again = scraper.parse_and_sync_jobs("HubSpot", url, html_data)
        self.assertEqual(len(jobs_again), 1)
        self.assertFalse(jobs_again[0]["is_new"])
        
        # Add new job posting
        html_data_new = html_data + """
        <div class="job-post">
            <h3 class="title">Director of Product</h3>
            <span class="dept">Product</span>
            <span class="date">2026-06-24</span>
        </div>
        """
        jobs_three = scraper.parse_and_sync_jobs("HubSpot", url, html_data_new)
        self.assertEqual(len(jobs_three), 2)
        
        # Director of Product is new (is_new=True), Staff AI Engineer is old (is_new=False)
        job_map = {j["title"]: j["is_new"] for j in jobs_three}
        self.assertTrue(job_map["Director of Product"])
        self.assertFalse(job_map["Staff AI Engineer"])
        
        conn.close()

if __name__ == "__main__":
    unittest.main()
