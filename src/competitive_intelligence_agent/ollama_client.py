"""Ollama API Client for local model execution."""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "gemma4:12b"

def call_ollama(
    messages: List[Dict[str, str]],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    response_json: bool = False,
    timeout: float = 45.0
) -> Optional[str]:
    """Call local Ollama chat API. Returns raw content string, or None on failure."""
    print(f"\n[Ollama Client] Firing LLM Request (Model: {model}, Response JSON: {response_json})")
    print(f"[Ollama Client] Messages/Prompts:")
    for msg in messages:
        print(f"  - [{msg['role'].upper()}]: {msg['content'][:300]}...")

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }
    if response_json:
        payload["format"] = "json"

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            content = res_data.get("message", {}).get("content")
            print(f"[Ollama Client] Success Response (Model: {model}): {content[:400]}...\n")
            return content
    except Exception as e:
        print(f"[Ollama Client Warning] Failed to query model '{model}' at {OLLAMA_URL}: {e}")
        if model == "gemma4:12b":
            fallback_model = "gemma3:4b"
            print(f"[Ollama Client Fallback] Attempting automatic fallback to lighter model: '{fallback_model}'")
            return call_ollama(messages, model=fallback_model, temperature=temperature, response_json=response_json, timeout=20.0)
        
        import traceback
        traceback.print_exc()
        return None
