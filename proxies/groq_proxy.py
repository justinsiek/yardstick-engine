#!/usr/bin/env python3
"""
Groq proxy server for benchmarking open-source models.

Free tier, OpenAI-compatible API, super fast inference.
Sign up at: https://console.groq.com

Edit the CONFIGURATION section below, then run:
    python proxies/groq_proxy.py
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import httpx


# === CONFIGURATION ===

MODELS = [
    {"name": "llama-3.1-8b-instant", "port": 8002},
    # {"name": "llama-3.2-1b-preview", "port": 8003},
    # {"name": "llama-3.1-70b-versatile", "port": 8004},

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

# Get API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    sys.exit("Error: GROQ_API_KEY not found in .env file. Get a free key at https://console.groq.com")

# Load system prompt
if SYSTEM_PROMPT_FILE.exists():
    SYSTEM_PROMPT = SYSTEM_PROMPT_FILE.read_text().strip()
else:
    SYSTEM_PROMPT = "You are a helpful assistant. Reply with ONLY the answer, no explanation."
    print(f"Warning: {SYSTEM_PROMPT_FILE} not found, using default prompt")


def call_groq(prompt: str, model: str) -> str:
    """Call Groq API and return the response text."""
    response = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
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
    if response.status_code != 200:
        error_detail = response.text
        raise Exception(f"Groq API error {response.status_code}: {error_detail}")
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
                answer = call_groq(prompt, self.model)
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
    if not MODELS:
        sys.exit("Error: No models configured. Edit MODELS in groq_proxy.py")

    print("Groq proxy servers:")
    
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

