"""
Measure end-to-end latency (wall clock) for three backends, repeated N times (default 3).
Writes latency_comparison.csv in the working directory.

Methodology (for lab report):
- Record one timestamp before the HTTP/SDK call and one after the response is fully received.
- Latency = t_after - t_before (seconds), store milliseconds in CSV.
- With n=3 runs, report p50 as median of the three samples; p95 is not statistically stable;
  we still compute numpy-style percentile linear interpolation when numpy is available,
  otherwise fall back to max-of-three as an upper tail proxy for tiny n.
"""
from __future__ import annotations

import csv
import os
import sys
import time
from typing import Callable, List
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

PROMPT = "In one short sentence, define the term 'agentic AI' for a CS class."
api_key = "Use your own API key"
base_url = "https://genai.hkbu.edu.hk/api/v0/rest"
model_name = "gpt-4.1"
api_version = "2024-12-01-preview"


def percentile_linear(sorted_vals: List[float], p: float) -> float:
    """p in [0,100]. Linear interpolation between closest ranks (common textbook definition)."""
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    d0 = sorted_vals[f] * (c - k)
    d1 = sorted_vals[c] * (k - f)
    return d0 + d1



def bench_hkbuapi() -> float:
    system_message = (
        "You are a friendly helper! Talk to the user like they are 3 years old. "
        "Use very simple words, be super excited and happy, and explain everything in a fun way "
        "that a little kid would understand!"
    )
    t0 = time.perf_counter()
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": PROMPT},
    ]

    url = f"{base_url}/deployments/{model_name}/chat/completions?api-version={api_version}"
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "api-key": api_key,
    }
    payload = {"messages": messages, "temperature": 0.7, "max_tokens": 150, "top_p": 1, "stream": False}
    response = requests.post(url, json=payload, headers=headers, timeout=300.0)
    response.raise_for_status()
    return time.perf_counter() - t0


def bench_ollama() -> float:
    import httpx

    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    t0 = time.perf_counter()
    r = httpx.post(
        f"{base}/api/generate",
        json={
            "model": model,
            "messages": [{"role": "user", "content": PROMPT}],
            "stream": False,
        },
        timeout=300.0,
    )
    r.raise_for_status()
    return time.perf_counter() - t0


def run_backend(name: str, fn: Callable[[], float], runs: int) -> List[float]:
    latencies: List[float] = []
    for i in range(runs):
        dt = fn()
        latencies.append(dt)
        print(f"{name} run {i+1}/{runs}: {dt*1000:.1f} ms")
    return latencies


def main() -> int:
    runs = int(os.environ.get("BENCH_RUNS", "3"))
    rows: list[dict[str, object]] = []

    backends: list[tuple[str, Callable[[], float]]] = []
    

    backends.append(
        (
            f"ollama_{os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')}",
            bench_ollama,
        )
    )

    backends.append(
        (
            f"HKBU_API_gpt-4.1",
            bench_hkbuapi,
        )
    )

    summary: list[tuple[str, float, float]] = []

    for name, fn in backends:
        try:
            samples = run_backend(name, fn, runs)
        except Exception as e:
            print(f"{name} FAILED: {e}", file=sys.stderr)
            continue
        ms = [s * 1000.0 for s in samples]
        ms_sorted = sorted(ms)
        p50 = percentile_linear(ms_sorted, 50)
        p95 = percentile_linear(ms_sorted, 95)
        summary.append((name, p50, p95))
        for idx, s in enumerate(samples):
            rows.append(
                {
                    "backend": name,
                    "run_index": idx + 1,
                    "latency_ms": round(s * 1000.0, 3),
                    "prompt_sha256": "fixed_prompt_v1",
                }
            )

    out_path = os.environ.get("BENCH_CSV", "latency_comparison.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["backend", "run_index", "latency_ms", "prompt_sha256"],
        )
        w.writeheader()
        w.writerows(rows)

    print("\nSummary (ms), wall-clock client observed:")
    for name, p50, p95 in summary:
        print(f"  {name}: p50={p50:.1f} ms  p95={p95:.1f} ms  (n={runs})")
    print(f"\nWrote {out_path}")

    return 0 if rows else 2


if __name__ == "__main__":
    raise SystemExit(main())
