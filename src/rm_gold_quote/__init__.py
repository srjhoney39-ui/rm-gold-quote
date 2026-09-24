"""rm-gold-quote: a live XAU/USD reference quote, ready to hand to Claude as a tool."""
from .fetcher import GoldQuote, QuoteError, fetch_xau_usd
from .claude_tool import XAU_TOOL, ask, run_tool

__all__ = ["GoldQuote", "QuoteError", "fetch_xau_usd", "XAU_TOOL", "run_tool", "ask"]
__version__ = "0.1.0"
