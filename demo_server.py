"""
Simple dummy server for testing the benchmark runner.

Run this in one terminal:
    python demo_server.py

Then run the benchmark in another terminal:
    python demo_run.py
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json


class AdditionHandler(BaseHTTPRequestHandler):
    """Handles POST requests and returns addition answers."""
    
    def do_POST(self):
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        data = json.loads(body)
        
        # Extract the question and compute answer
        question = data.get("question", "")
        
        # Simple parser for "What is X + Y?"
        try:
            # Extract numbers from question like "What is 1 + 2?"
            parts = question.replace("?", "").split("+")
            if len(parts) == 2:
                a = int(parts[0].split()[-1])
                b = int(parts[1].strip())
                answer = str(a + b)
            else:
                answer = "unknown"
        except Exception:
            answer = "error"
        
        # Send response
        response = json.dumps({"answer": answer})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {args[0]}")


if __name__ == "__main__":
    port = 8000
    server = HTTPServer(("localhost", port), AdditionHandler)
    print(f"🚀 Dummy server running at http://localhost:{port}/solve")
    print("   POST with JSON like: {\"question\": \"What is 2 + 3?\"}")
    print("   Press Ctrl+C to stop")
    server.serve_forever()

