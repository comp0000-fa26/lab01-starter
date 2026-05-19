"""
Minimal verification: one short completion from Anthropic, OpenAI, and local Ollama.
Loads secrets from environment (optionally via .env if python-dotenv is installed).
"""
from __future__ import annotations

import os
import sys

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


PROMPT = "Reply with exactly: OK"


def check_anthropic() -> str:
    import anthropic

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return "SKIP: ANTHROPIC_API_KEY not set"
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=32,
        messages=[{"role": "user", "content": PROMPT}],
    )
    text = msg.content[0].text if msg.content else ""
    return f"OK anthropic: {text.strip()[:200]}"


def check_openai() -> str:
    from openai import OpenAI

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return "SKIP: OPENAI_API_KEY not set"
    client = OpenAI()
    r = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=32,
        messages=[{"role": "user", "content": PROMPT}],
    )
    text = r.choices[0].message.content or ""
    return f"OK openai: {text.strip()[:200]}"


def check_ollama() -> str:
    import httpx

    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    url = f"{base}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": False,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=120.0)
    except httpx.RequestError as e:
        return f"SKIP ollama (network): {e}"
    if resp.status_code != 200:
        return f"SKIP ollama: HTTP {resp.status_code} {resp.text[:200]}"
    data = resp.json()
    text = (data.get("message") or {}).get("content") or ""
    return f"OK ollama ({model}): {str(text).strip()[:200]}"


def main() -> int:
    lines = [
        check_anthropic(),
        check_openai(),
        check_ollama(),
    ]
    out = "\n".join(lines) + "\n"
    sys.stdout.write(out)
    if any(x.startswith("SKIP") for x in lines):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
