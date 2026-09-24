import json
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from rm_gold_quote import XAU_TOOL, fetch_xau_usd, run_tool
from rm_gold_quote.fetcher import QuoteError


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _payload(price=4270.5, age=5):
    ts = (datetime.now(timezone.utc) - timedelta(seconds=age)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"currency": "USD", "name": "Gold", "price": price, "symbol": "XAU", "updatedAt": ts}


def test_current_quote():
    with mock.patch("urllib.request.urlopen", return_value=_Resp(_payload())):
        q = fetch_xau_usd()
    assert q.price == 4270.5 and q.state == "current" and q.executable is False


def test_stale_quote_is_flagged():
    with mock.patch("urllib.request.urlopen", return_value=_Resp(_payload(age=600))):
        assert fetch_xau_usd().state == "stale"


def test_rejects_absurd_price():
    with mock.patch("urllib.request.urlopen", return_value=_Resp(_payload(price=12))), mock.patch("time.sleep"):
        with pytest.raises(QuoteError):
            fetch_xau_usd()


def test_tool_returns_error_not_guess():
    with mock.patch("urllib.request.urlopen", side_effect=OSError("down")), mock.patch("time.sleep"):
        out = run_tool(XAU_TOOL["name"], {})
    assert "error" in out and "price" not in out


def test_tool_schema_is_object():
    assert XAU_TOOL["input_schema"]["type"] == "object"
