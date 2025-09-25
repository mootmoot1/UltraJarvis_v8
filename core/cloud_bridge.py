import os
import time
import sys

PROVIDER = os.getenv("MODEL_PROVIDER", "openai").lower()


def process_request(prompt):
    out = ""
    try:
        # Simulate API call
        model = "gpt-3.5-turbo"
        messages = [
            {
                "role": "system",
                "content": "Be precise. Return the required FILES block only.",
            },
            {"role": "user", "content": prompt},
        ]
        # Simulated response
        out = (messages[0]["content"] or "").strip()
        if not out:
            print("OpenAI returned empty content")
            return out
        return out
    except Exception as e:
        print(f"OpenAI returned error: {e}")
        return ""


# Another example of fixing E701


def another_example():
    try:
        data = {}  # Simulated data
        out = (
            data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
        ).strip()
        if not out:
            print("Local LLM returned empty content")
            return out
        return out
    except Exception as e:
        print(f"Local LLM returned error: {e}")
        return ""
