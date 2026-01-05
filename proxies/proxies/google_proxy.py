"""Google Gemini/Gemma proxy for proxy_runner.

Models available (free tier rate limits):
- gemma-3-1b-it: 30 RPM, 14.4K/day (best for free tier!)
- gemma-3-4b-it: 30 RPM, 14.4K/day
- gemini-2.0-flash-lite: 30 RPM
- gemini-2.5-flash: 10 RPM, 250/day

Get a free API key at: https://aistudio.google.com/apikey
Docs: https://ai.google.dev/gemini-api/docs/quickstart
"""

import os
import httpx

API_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def get_api_key() -> str:
    """Get API key from environment."""
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY not set in .env (get free key at https://aistudio.google.com/apikey)")
    return "".join(key.split())


def call(model: str, prompt: str, system_prompt: str) -> str:
    """Call Google Gemini API and return the response text."""
    
    # Gemma models don't support system_instruction - prepend to prompt instead
    is_gemma = model.startswith("gemma")
    if is_gemma:
        full_prompt = f"{system_prompt}\n\nQuestion: {prompt}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 100, "temperature": 0},
        }
    else:
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 100, "temperature": 0},
        }
    
    response = httpx.post(
        f"{API_URL}/{model}:generateContent",
        headers={
            "x-goog-api-key": get_api_key(),
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60.0,
    )
    
    if response.status_code != 200:
        error_msg = f"Google API error {response.status_code}: {response.text}"
        print(f"[Google] {error_msg}")
        raise Exception(error_msg)
    
    result = response.json()
    try:
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()
    except (KeyError, IndexError) as e:
        print(f"[Google] Unexpected response format: {result}")
        raise Exception(f"Failed to parse Google response: {e}")
