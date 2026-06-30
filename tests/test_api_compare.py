import json
import unittest
from io import BytesIO

from competitive_intelligence_agent.dev_server import DemoHandler

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

class TestAPICompare(unittest.TestCase):
    def test_dev_server_compare_endpoint(self):
        # We simulate a request GET /api/competitors/compare?comp1=HubSpot&comp2=Anthropic HTTP/1.1
        request_line = b"GET /api/competitors/compare?comp1=HubSpot&comp2=Anthropic HTTP/1.1\r\nHost: localhost\r\n\r\n"
        socket = MockSocket(request_line)
        
        # Instantiate DemoHandler with mock connection socket
        handler = DemoHandler(socket, ("127.0.0.1", 8000), None)
        
        # Check written response
        response_bytes = socket.wfile.getvalue()
        
        # Extract headers and body
        parts = response_bytes.split(b"\r\n\r\n", 1)
        self.assertEqual(len(parts), 2)
        headers, body = parts
        
        # Verify status line is 200 OK
        self.assertTrue(headers.startswith(b"HTTP/1.1 200 OK") or headers.startswith(b"HTTP/1.0 200 OK"))
        
        # Verify JSON content
        data = json.loads(body.decode("utf-8"))
        self.assertIn("comp1", data)
        self.assertIn("comp2", data)
        self.assertEqual(data["comp1"]["competitor_name"], "HubSpot")
        self.assertEqual(data["comp2"]["competitor_name"], "Anthropic")
        self.assertIsInstance(data["comp1"]["hypotheses"], list)
        self.assertIsInstance(data["comp2"]["hypotheses"], list)

    def test_dev_server_compare_missing_params(self):
        request_line = b"GET /api/competitors/compare?comp1=HubSpot HTTP/1.1\r\nHost: localhost\r\n\r\n"
        socket = MockSocket(request_line)
        handler = DemoHandler(socket, ("127.0.0.1", 8000), None)
        response_bytes = socket.wfile.getvalue()
        parts = response_bytes.split(b"\r\n\r\n", 1)
        headers, body = parts
        self.assertTrue(headers.startswith(b"HTTP/1.1 400 Bad Request") or headers.startswith(b"HTTP/1.0 400 Bad Request"))

    def test_fastapi_compare_endpoint(self):
        try:
            from fastapi.testclient import TestClient
            from competitive_intelligence_agent.api import app
        except ImportError:
            self.skipTest("FastAPI or dependencies not installed")

        client = TestClient(app)
        response = client.get("/api/competitors/compare?comp1=HubSpot&comp2=Anthropic")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("comp1", data)
        self.assertIn("comp2", data)
        self.assertEqual(data["comp1"]["competitor_name"], "HubSpot")
        self.assertEqual(data["comp2"]["competitor_name"], "Anthropic")

if __name__ == "__main__":
    unittest.main()
