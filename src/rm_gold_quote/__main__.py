"""CLI: `python -m rm_gold_quote` prints the live quote as JSON.
`python -m rm_gold_quote --ask "What is gold doing today?"` asks Claude (needs ANTHROPIC_API_KEY)."""
import argparse
import json
import sys

from .fetcher import QuoteError, fetch_xau_usd


def main() -> int:
    p = argparse.ArgumentParser(prog="rm_gold_quote", description="Live XAU/USD reference quote")
    p.add_argument("--ask", metavar="QUESTION", help="ask Claude a question; it can call the live-quote tool")
    args = p.parse_args()
    if args.ask:
        from .claude_tool import ask
        print(ask(args.ask))
        return 0
    try:
        print(json.dumps(fetch_xau_usd().to_dict(), indent=2))
        return 0
    except QuoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
