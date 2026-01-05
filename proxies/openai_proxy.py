#!/usr/bin/env python3
"""
OpenAI proxy server for benchmarking.

Edit the CONFIGURATION section below, then run:
    python proxies/openai_proxy.py
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import httpx


# === CONFIGURATION ===

# Models to serve (each gets its own port)
MODELS = [
    {"name": "gpt-4o-mini", "port": 8001},
    {"name": "gpt-4o", "port": 8002},
    # {"name": "gpt-3.5-turbo", "port": 8003},
]

# System prompt file (shared across providers)
SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"


# === IMPLEMENTATION ===

# Load .env file from engine root (parent of proxies/)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

# Load system prompt
if SYSTEM_PROMPT_FILE.exists():
    SYSTEM_PROMPT = SYSTEM_PROMPT_FILE.read_text().strip()
else:
    SYSTEM_PROMPT = "You are a helpful assistant. Reply with ONLY the answer, no explanation."
    print(f"Warning: {SYSTEM_PROMPT_FILE} not found, using default prompt")


def call_openai(prompt: str, model: str) -> str:
    """Call OpenAI and return the response text."""
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 100,
            "temperature": 0,
        },
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def make_handler(model_name: str):
    """Create a handler class for a specific model."""
    class Handler(BaseHTTPRequestHandler):
        model = model_name

        def do_POST(self):
            if self.path != "/solve":
                self.send_error(404)
                return

            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            data = json.loads(body)
            prompt = data.get("question") or data.get("prompt", "")

            try:
                answer = call_openai(prompt, self.model)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"answer": answer}).encode())
            except Exception as e:
                self.send_error(500, str(e))

        def log_message(self, fmt, *args):
            print(f"[{self.model}] {args[0]}")

    return Handler


def run_server(model_name: str, port: int):
    """Run a server for a single model."""
    handler = make_handler(model_name)
    server = HTTPServer(("localhost", port), handler)
    print(f"  {model_name}: http://localhost:{port}/solve")
    server.serve_forever()


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Error: OPENAI_API_KEY not set. Create a .env file with OPENAI_API_KEY=sk-...")

    if not MODELS:
        sys.exit("Error: No models configured. Edit MODELS in openai_proxy.py")

    print("OpenAI proxy servers:")
    
    # Start all but the last server in background threads
    for config in MODELS[:-1]:
        thread = threading.Thread(
            target=run_server,
            args=(config["name"], config["port"]),
            daemon=True
        )
        thread.start()

    # Run the last server in the main thread (blocks)
    last = MODELS[-1]
    run_server(last["name"], last["port"])
