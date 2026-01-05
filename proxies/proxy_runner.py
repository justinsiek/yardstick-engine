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

# Import proxies (add parent to path for direct script execution)
sys.path.insert(0, str(Path(__file__).parent.parent))
from proxies.proxies import openai_proxy, groq_proxy, google_proxy


# === CONFIGURATION ===

# All models to serve (provider, model name, port)
MODELS = [
    # OpenAI
    {"provider": "openai", "model": "gpt-4o-mini", "port": 8001},
    
    # Groq (free, 8B minimum)
    {"provider": "groq", "model": "llama-3.1-8b-instant", "port": 8002},
    
    # Google Gemma (free tier: 30 RPM for gemma-3 models)
    {"provider": "google", "model": "gemma-3-1b-it", "port": 8003},
]

# System prompt file (shared across all providers)
SYSTEM_PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"


# === IMPLEMENTATION ===

# Proxy registry - maps provider name to module
PROXIES = {
    "openai": openai_proxy,
    "groq": groq_proxy,
    "google": google_proxy,
}

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


def call_llm(provider: str, model: str, prompt: str) -> str:
    """Call an LLM provider and return the response text."""
    proxy_module = PROXIES[provider]
    return proxy_module.call(model, prompt, SYSTEM_PROMPT)


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
                # Sanitize error message - newlines break HTTP headers
                error_msg = str(e).replace("\n", " ").replace("\r", " ")[:200]
                print(f"[{provider}/{model}] Error: {e}")
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": error_msg}).encode())

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
    
    for provider in providers_needed:
        proxy_module = PROXIES[provider]
        try:
            proxy_module.get_api_key()
        except ValueError as e:
            sys.exit(f"Error: {e}")


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
