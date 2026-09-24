"""Expose the live XAU/USD quote to Claude as a tool.

`XAU_TOOL` is the JSON-schema tool definition Claude sees, `run_tool` executes
a tool call, and `ask` is a complete, minimal agent loop using the Anthropic
Python SDK (`pip install rm-gold-quote[claude]`).
"""
from __future__ import annotations

import json
import os
from typing import Any

from .fetcher import QuoteError, fetch_xau_usd

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5-5")

XAU_TOOL: dict[str, Any] = {
    "name": "fetch_live_xau_usd",
    "description": (
        "Fetches the current XAU/USD (spot gold in US dollars) reference price with its "
        "timestamp, freshness state and source. Use whenever the user asks for the current "
        "gold price or anything that depends on where gold trades now. The price is a "
        "reference quote, not an executable price."
    ),
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

SYSTEM = (
    "You answer questions about the gold market. Call fetch_live_xau_usd for any "
    "current price instead of relying on memory, quote the timestamp and source it "
    "returns, and say so if the result is stale or an error. Do not give personalised "
    "investment advice."
)


def run_tool(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Execute one tool call and return a JSON-serialisable result."""
    if name != XAU_TOOL["name"]:
        return {"error": f"unknown tool {name!r}"}
    try:
        return fetch_xau_usd().to_dict()
    except QuoteError as exc:
        return {"error": str(exc)}


def ask(question: str, model: str = DEFAULT_MODEL, max_rounds: int = 3) -> str:
    """Ask Claude a gold-market question; Claude may call the live-quote tool."""
    from anthropic import Anthropic  # optional dependency

    client = Anthropic()  # reads ANTHROPIC_API_KEY
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    for _ in range(max_rounds + 1):
        resp = client.messages.create(model=model, max_tokens=1024, system=SYSTEM, tools=[XAU_TOOL], messages=messages)
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text").strip()
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                out = run_tool(block.name, block.input or {})
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(out),
                    "is_error": "error" in out,
                })
        messages.append({"role": "user", "content": results})
    raise RuntimeError("Claude did not finish within the tool-round limit")
