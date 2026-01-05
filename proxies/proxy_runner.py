#!/usr/bin/env python3
"""
Unified proxy runner for all LLM providers.

Start all your model proxies from one file:
    python proxies/proxy_runner.py

Edit the MODELS configuration below to add/remove models.
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import httpx


# === CONFIGURATION ===

# All models to serve (provider, model name, port)
MODELS = [
    # OpenAI
    {"provider": "openai", "model": "gpt-4o-mini", "port": 8001},
    
    # Groq (free)
    {"provider": "groq", "model": "llama-3.1-8b-instant", "port": 8002},
]

# System prompt file (shared across all providers)
SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"


# === IMPLEMENTATION ===

# Load .env file
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

# API endpoints
PROVIDERS = {
    "openai": {
        "url": "https://api.openai.com/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
    },
}


def call_llm(provider: str, model: str, prompt: str) -> str:
    """Call an LLM provider and return the response text."""
    config = PROVIDERS[provider]
    api_key = os.environ.get(config["key_env"])
    
    if not api_key:
        raise Exception(f"{config['key_env']} not set in .env")
    
    response = httpx.post(
        config["url"],
        headers={"Authorization": f"Bearer {api_key}"},
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
        raise Exception(f"{provider} API error {response.status_code}: {response.text}")
    
    return response.json()["choices"][0]["message"]["content"].strip()


def make_handler(provider: str, model: str):
    """Create a handler class for a specific provider/model."""
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/solve":
                self.send_error(404)
                return

            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            data = json.loads(body)
            prompt = data.get("question") or data.get("prompt", "")

            try:
                answer = call_llm(provider, model, prompt)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"answer": answer}).encode())
            except Exception as e:
                self.send_error(500, str(e))

        def log_message(self, fmt, *args):
            print(f"[{provider}/{model}] {args[0]}")

    return Handler


def run_server(provider: str, model: str, port: int):
    """Run a server for a single model."""
    handler = make_handler(provider, model)
    server = HTTPServer(("localhost", port), handler)
    server.serve_forever()


def check_api_keys():
    """Check that required API keys are set."""
    providers_needed = set(m["provider"] for m in MODELS)
    missing = []
    
    for provider in providers_needed:
        key_env = PROVIDERS[provider]["key_env"]
        if not os.environ.get(key_env):
            missing.append(key_env)
    
    if missing:
        sys.exit(f"Error: Missing API keys in .env: {', '.join(missing)}")


def check_port_conflicts():
    """Check for duplicate ports."""
    ports = [m["port"] for m in MODELS]
    if len(ports) != len(set(ports)):
        sys.exit("Error: Duplicate ports in MODELS configuration")


if __name__ == "__main__":
    if not MODELS:
        sys.exit("Error: No models configured. Edit MODELS in proxy_runner.py")
    
    check_api_keys()
    check_port_conflicts()
    
    print("Starting proxy servers:\n")
    for config in MODELS:
        print(f"  {config['provider']}/{config['model']}: http://localhost:{config['port']}/solve")
    print()
    
    # Start all but the last server in background threads
    for config in MODELS[:-1]:
        thread = threading.Thread(
            target=run_server,
            args=(config["provider"], config["model"], config["port"]),
            daemon=True
        )
        thread.start()

    # Run the last server in the main thread (blocks)
    last = MODELS[-1]
    run_server(last["provider"], last["model"], last["port"])

