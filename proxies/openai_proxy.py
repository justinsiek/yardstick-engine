#!/usr/bin/env python3
"""
Minimal OpenAI proxy server.

Wraps OpenAI's API into a simple /solve endpoint for benchmarking.

Usage:
    1. Create a .env file with: OPENAI_API_KEY=sk-...
    2. Create a system_prompt.txt file with your prompt
    3. python openai_proxy.py [--port 8001] [--model gpt-4o-mini]
"""

import argparse
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import httpx

# Load .env file from engine root (parent of proxies/)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


# Global system prompt - loaded at startup
SYSTEM_PROMPT = ""


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


class Handler(BaseHTTPRequestHandler):
    model = "gpt-4o-mini"

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
        print(f"[openai] {args[0]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--model", default="gpt-4o-mini")
    # Default to system_prompt.txt in the same directory as this script
    default_prompt = Path(__file__).parent / "system_prompt.txt"
    parser.add_argument("--system-prompt", default=str(default_prompt),
                        help="Path to system prompt file")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Error: OPENAI_API_KEY not set")

    # Load system prompt
    prompt_file = Path(args.system_prompt)
    if prompt_file.exists():
        SYSTEM_PROMPT = prompt_file.read_text().strip()
        print(f"Loaded system prompt from {prompt_file}")
    else:
        print(f"Warning: {prompt_file} not found - using no system prompt")

    Handler.model = args.model
    print(f"OpenAI proxy at http://localhost:{args.port}/solve (model: {args.model})")
    HTTPServer(("localhost", args.port), Handler).serve_forever()

