import json
import unittest
from io import BytesIO
from competitive_intelligence_agent.dev_server import DemoHandler
from competitive_intelligence_agent.db_client import DBClient

class MockSocket:
    def __init__(self, data=b""):
        self.rfile = BytesIO(data)
        self.wfile = BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data):
        self.wfile.write(data)

class TestAPIGraph(unittest.TestCase):
    def test_graph_start_endpoint(self):
        request_line = b"GET /api/graph/start?competitor=HubSpot HTTP/1.1\r\nHost: localhost\r\n\r\n"
        socket = MockSocket(request_line)
        handler = DemoHandler(socket, ("127.0.0.1", 8000), None)
        response_bytes = socket.wfile.getvalue()
        parts = response_bytes.split(b"\r\n\r\n", 1)
        self.assertEqual(len(parts), 2)
        headers, body = parts
        self.assertTrue(headers.startswith(b"HTTP/1.1 200 OK") or headers.startswith(b"HTTP/1.0 200 OK"))
        
        data = json.loads(body.decode("utf-8"))
        self.assertIn("thread_id", data)
        self.assertIn("status", data)
        self.assertIn("footprint", data)
        self.assertIn("signals", data)
        self.assertIn("hypotheses", data)

    def test_graph_resume_endpoint(self):
        # First start the graph to get a thread ID
        request_line_start = b"GET /api/graph/start?competitor=HubSpot HTTP/1.1\r\nHost: localhost\r\n\r\n"
        socket_start = MockSocket(request_line_start)
        handler_start = DemoHandler(socket_start, ("127.0.0.1", 8000), None)
        parts_start = socket_start.wfile.getvalue().split(b"\r\n\r\n", 1)
        data_start = json.loads(parts_start[1].decode("utf-8"))
        thread_id = data_start["thread_id"]

        # Now resume the graph
        request_line_resume = f"GET /api/graph/resume?thread_id={thread_id} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode("utf-8")
        socket_resume = MockSocket(request_line_resume)
        handler_resume = DemoHandler(socket_resume, ("127.0.0.1", 8000), None)
        parts_resume = socket_resume.wfile.getvalue().split(b"\r\n\r\n", 1)
        
        headers, body = parts_resume
        self.assertTrue(headers.startswith(b"HTTP/1.1 200 OK") or headers.startswith(b"HTTP/1.0 200 OK"))
        data_resume = json.loads(body.decode("utf-8"))
        self.assertIn("recommendations", data_resume)
        self.assertEqual(data_resume["status"], "completed")

    def test_post_feedback_endpoint(self):
        # We simulate a POST request to /api/feedback
        payload = {
            "competitor_name": "HubSpot",
            "hypothesis_id": "hyp-hubspot-pricing",
            "vote": "thumbs_up",
            "comments": "Strategic pricing change comments"
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        request_headers = f"POST /api/feedback HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: {len(body_bytes)}\r\n\r\n".encode("utf-8")
        
        socket = MockSocket(request_headers + body_bytes)
        handler = DemoHandler(socket, ("127.0.0.1", 8000), None)
        response_bytes = socket.wfile.getvalue()
        parts = response_bytes.split(b"\r\n\r\n", 1)
        headers, body = parts
        self.assertTrue(headers.startswith(b"HTTP/1.1 200 OK") or headers.startswith(b"HTTP/1.0 200 OK"))
        
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["status"], "success")

        # Verify that it was committed to SQLite feedback table
        db = DBClient()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT comments FROM feedback WHERE hypothesis_id = 'hyp-hubspot-pricing'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["comments"], "Strategic pricing change comments")

if __name__ == "__main__":
    unittest.main()
