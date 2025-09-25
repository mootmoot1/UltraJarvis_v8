# core/cloud_bridge.py
import os, time, sys
from typing import Optional

PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()
VERBOSE = os.getenv("LLM_VERBOSE", "1") == "1"


def _log(msg: str):
    if VERBOSE:
        print(f"[cloud_bridge] {msg}", file=sys.stderr)


def ask_cloud_ai(prompt: str) -> str:
    """Return model text or '' on failure (but log why)."""
    if PROVIDER == "openai":
        try:
            from openai import OpenAI

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        except Exception as e:
            _log(f"OpenAI init failed: {e}")
            return ""

        for attempt in range(3):
            try:
                r = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Be precise. Return the required FILES block only.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                out = (r.choices[0].message.content or "").strip()
                if not out:
                    _log("OpenAI returned empty content")
                return out
            except Exception as e:
                _log(f"OpenAI call failed (try {attempt+1}/3): {e}")
                time.sleep(1.0)
        return ""

    # local server (LM Studio / Ollama-compatible)
    try:
        import requests

        base = os.getenv("LMSTUDIO_BASE", "http://localhost:1234")
        model = os.getenv("LMSTUDIO_MODEL", "llama-3.1-8b-instruct")
        for attempt in range(3):
            try:
                res = requests.post(
                    f"{base}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Be precise. Return the required FILES block only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.2,
                    },
                    timeout=120,
                )
                res.raise_for_status()
                data = res.json()
                out = (data["choices"][0]["message"]["content"] or "").strip()
                if not out:
                    _log("Local LLM returned empty content")
                return out
            except Exception as e:
                _log(f"Local LLM call failed (try {attempt+1}/3): {e}")
                time.sleep(1.0)
        return ""
    except Exception as e:
        _log(f"Local LLM not available: {e}")
        return ""
