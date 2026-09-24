"""Live XAU/USD reference quote fetcher.

Uses the free, key-less gold-api.com endpoint. Standard library only.
The returned price is a *reference* quote: it is not an executable broker
price, an LBMA fixing, or a consolidated spot tape.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

GOLD_API_URL = "https://api.gold-api.com/price/XAU"
USER_AGENT = "rm-gold-quote/0.1 (+https://rmclub.org/research/methodology/)"


class QuoteError(RuntimeError):
    """Raised when no valid quote could be obtained."""


@dataclass(frozen=True)
class GoldQuote:
    symbol: str
    price: float
    currency: str
    observed_at: str          # ISO-8601, UTC, as reported by the source
    retrieved_at: str         # ISO-8601, UTC, when we fetched it
    age_seconds: Optional[int]
    state: str                # "current" (<=90 s), "delayed" (<=180 s) or "stale"
    source: str
    executable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _state(age: Optional[int]) -> str:
    if age is None:
        return "stale"
    if age <= 90:
        return "current"
    if age <= 180:
        return "delayed"
    return "stale"


def fetch_xau_usd(timeout: float = 8.0, retries: int = 2, backoff: float = 0.8) -> GoldQuote:
    """Fetch the current XAU/USD reference price.

    Retries transient network/HTTP errors with exponential backoff and
    validates the value before returning it. Raises QuoteError on failure
    rather than returning a guessed number.
    """
    last_err: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(GOLD_API_URL, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            price = float(data["price"])
            if not 100 < price < 25_000:
                raise QuoteError(f"price {price} outside XAU/USD sanity bounds")
            observed_raw = data.get("updatedAt")
            now = datetime.now(timezone.utc)
            age = None
            observed_iso = observed_raw or now.isoformat()
            if observed_raw:
                observed = datetime.fromisoformat(observed_raw.replace("Z", "+00:00"))
                age = max(0, int((now - observed).total_seconds()))
                observed_iso = observed.astimezone(timezone.utc).isoformat()
            return GoldQuote(
                symbol="XAU/USD",
                price=round(price, 2),
                currency=data.get("currency", "USD"),
                observed_at=observed_iso,
                retrieved_at=now.isoformat(),
                age_seconds=age,
                state=_state(age),
                source="gold-api.com",
            )
        except (OSError, KeyError, ValueError, QuoteError) as exc:  # URLError, TimeoutError and JSONDecodeError are subclasses
            last_err = exc
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
    raise QuoteError(f"could not fetch XAU/USD: {last_err}")
