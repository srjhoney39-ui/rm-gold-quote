# rm-gold-quote

A small, dependency-free Python package that fetches a **live XAU/USD (spot gold) reference price** and exposes it as a **Claude tool**, so a language model can check where gold trades instead of guessing.

It is one fragment of the research stack behind [RM Intelligence](https://rmclub.org/research/methodology/), released so developers can reuse the pattern.

```bash
pip install "rm-gold-quote[claude]"      # or: pip install rm-gold-quote   (fetcher only)
python -m rm_gold_quote                  # prints the live quote as JSON
```

```json
{
  "symbol": "XAU/USD",
  "price": 4270.5,
  "currency": "USD",
  "observed_at": "2026-09-24T12:53:51+00:00",
  "retrieved_at": "2026-09-24T12:53:52+00:00",
  "age_seconds": 1,
  "state": "current",
  "source": "gold-api.com",
  "executable": false
}
```

## Use it in Python

```python
from rm_gold_quote import fetch_xau_usd

q = fetch_xau_usd()
print(q.price, q.state, q.observed_at)
```

`fetch_xau_usd()` retries transient errors, sanity-checks the value, and **raises `QuoteError` instead of returning a guessed number**. Every quote carries its own timestamp and a freshness `state` (`current` ≤ 90 s, `delayed` ≤ 180 s, else `stale`).

## Give it to Claude

```python
from rm_gold_quote import ask   # needs ANTHROPIC_API_KEY

print(ask("What's the current price of gold, and how fresh is that number?"))
```

Or wire the pieces into your own agent loop:

```python
from rm_gold_quote import XAU_TOOL, run_tool

# 1. pass tools=[XAU_TOOL] to client.messages.create(...)
# 2. when stop_reason == "tool_use", call run_tool(block.name, block.input)
# 3. send the result back as a tool_result block and ask Claude to continue
```

The default model is `claude-opus-5-5`; override it with the `ANTHROPIC_MODEL` environment variable or `ask(..., model=...)`.

## What this is not

- **Not an execution price.** The quote is a reference from a public composite feed, not a broker quote, an LBMA fixing or a consolidated spot tape.
- **Not advice.** Nothing here tells you what to buy or sell.
- **Not the full system.** The RM Intelligence workstation adds a four-pillar composable model (data, multi-factor alpha, a fail-closed risk gate and paper execution), live charts, and a research copilot with price, technicals and model tools. See the [methodology](https://rmclub.org/research/methodology/) and the free [daily XAU/USD macro report](https://rmclub.org/research/gold-macro-report/).

## Development

```bash
pip install -e ".[test]"
pytest
```

## License

MIT. Price data is provided by [gold-api.com](https://gold-api.com/) under its own terms. Check them before commercial use.
