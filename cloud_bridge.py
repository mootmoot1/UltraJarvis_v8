import os
import time
import json
import requests
from typing import Optional


def ask_cloud_ai(prompt: str) -> str:
    """Provider-agnostic cloud AI interface"""
    provider = os.getenv("MODEL_PROVIDER", "openai").lower()

    if provider == "openai":
        return _ask_openai(prompt)
    elif provider in ("lmstudio", "ollama"):
        return _ask_lmstudio(prompt)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _ask_openai(prompt: str) -> str:
    """OpenAI API implementation"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable required")

    model = os.getenv("MODEL_NAME", "gpt-4o-mini")

    for attempt in range(3):
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == 2:
                raise Exception(f"OpenAI API failed after 3 attempts: {e}")
            time.sleep(0.5 * (2**attempt))


def _ask_lmstudio(prompt: str) -> str:
    """LM Studio/Ollama implementation"""
    base_url = os.getenv("LMSTUDIO_BASE", "http://localhost:1234")
    model = os.getenv("MODEL_NAME", "llama-3.2-3b-instruct")

    for attempt in range(3):
        try:
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == 2:
                raise Exception(f"LM Studio API failed after 3 attempts: {e}")
            time.sleep(0.5 * (2**attempt))
