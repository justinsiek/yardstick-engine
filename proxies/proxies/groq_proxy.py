"""Groq proxy for proxy_runner."""

import os
import httpx

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_api_key() -> str:
    """Get API key from environment."""
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY not set in .env")
    return key.strip()  # Remove any trailing newlines from .env


def call(model: str, prompt: str, system_prompt: str) -> str:
    """Call Groq API and return the response text."""
    response = httpx.post(
        API_URL,
        headers={"Authorization": f"Bearer {get_api_key()}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 100,
            "temperature": 0,
        },
        timeout=60.0,
    )
    
    if response.status_code != 200:
        raise Exception(f"Groq API error {response.status_code}: {response.text}")
    
    return response.json()["choices"][0]["message"]["content"].strip()

