#!/usr/bin/env python3
"""CLI agent that calls an LLM and returns a structured JSON answer."""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import httpx


def load_config() -> dict[str, str]:
    """Load LLM configuration from .env.agent.secret."""
    env_file = Path(".env.agent.secret")
    if not env_file.exists():
        print(f"Error: {env_file} not found", file=sys.stderr)
        print(
            "Copy .env.agent.example to .env.agent.secret and fill in your credentials",
            file=sys.stderr,
        )
        sys.exit(1)

    config = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        config[key] = value

    required = ["LLM_API_KEY", "LLM_API_BASE", "LLM_MODEL"]
    missing = [k for k in required if k not in config or not config[k]]
    if missing:
        print(f"Error: Missing required config keys: {missing}", file=sys.stderr)
        sys.exit(1)

    return config


async def call_llm(question: str, config: dict[str, str]) -> str:
    """Call the LLM API and return the answer text."""
    api_base = config["LLM_API_BASE"]
    api_key = config["LLM_API_KEY"]
    model = config["LLM_MODEL"]

    url = f"{api_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": question},
        ],
    }

    print(f"Calling LLM at {url}...", file=sys.stderr)

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        print(f"Error: API returned status {response.status_code}", file=sys.stderr)
        print(f"Response: {response.text[:200]}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        print(f"Error: Unexpected API response format: {e}", file=sys.stderr)
        print(f"Full response: {data}", file=sys.stderr)
        sys.exit(1)

    return answer


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LLM-powered question answering agent")
    parser.add_argument("question", help="The question to answer")
    args = parser.parse_args()

    config = load_config()
    answer = asyncio.run(call_llm(args.question, config))

    result = {
        "answer": answer,
        "tool_calls": [],
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
