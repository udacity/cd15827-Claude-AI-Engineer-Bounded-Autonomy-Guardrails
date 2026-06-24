"""Heterogeneous-format normalizers: currency strings, timestamps, numeric status codes.

These exist because upstream tools emit data in whatever format their source system uses. The
PostToolUse normalization hook is the single place that canonicalizes them, so the model only
ever reasons over one representation. Currency amounts are exact ``Decimal`` — never ``float``.

In this exercise you implement the four normalizers (``_parse_amount``, ``normalize_currency``,
``normalize_timestamp``, ``normalize_status``). The currency-detection helper, the typed error
classes, the lookup tables, and ``coerce_money`` are provided.
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from transaction_agent.config import THRESHOLD_CURRENCY
from transaction_agent.models import Money

#: Symbol / ISO-code → ISO-4217 currency.
_SYMBOL_CURRENCY = {"$": "USD", "£": "GBP", "€": "EUR"}
_KNOWN_CODES = {"USD", "EUR", "GBP"}

#: Numeric account status codes → canonical labels.
_STATUS_LABELS = {1: "active", 2: "dormant", 3: "frozen"}


class CurrencyParseError(ValueError):
    """Raised when a currency string cannot be parsed. Carries the offending raw value."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"cannot parse currency value: {raw!r}")
        self.raw = raw


class TimestampParseError(ValueError):
    """Raised when a timestamp cannot be parsed. Carries the offending raw value."""

    def __init__(self, raw: object) -> None:
        super().__init__(f"cannot parse timestamp value: {raw!r}")
        self.raw = raw


class StatusCodeError(ValueError):
    """Raised on an unknown numeric status code. Carries the offending raw value."""

    def __init__(self, raw: object) -> None:
        super().__init__(f"unknown status code: {raw!r}")
        self.raw = raw


def _detect_currency(raw: str) -> str:
    for symbol, code in _SYMBOL_CURRENCY.items():
        if symbol in raw:
            return code
    for code in _KNOWN_CODES:
        if code in raw.upper():
            return code
    raise CurrencyParseError(raw)


def _parse_amount(numeric: str, raw: str) -> Decimal:
    # TODO US-02 (LO-3): Turn the digits-and-separators string ``numeric`` into an exact Decimal.
    # The hard part is that separators mean different things in different locales:
    #   "$1,234.56" -> comma=thousands, dot=decimal  -> 1234.56
    #   "EUR 1.234,56" -> dot=thousands, comma=decimal -> 1234.56
    # A naive numeric.replace(",", "") silently corrupts the European format, and float() loses
    # cents. Rule that handles both: when BOTH separators are present, the one that appears LAST
    # is the decimal separator and the other is thousands. When only commas are present, decide
    # whether it is grouped thousands (1,234) or a decimal comma (1,56). Build a normalized
    # string with "." as the decimal point and no thousands separators, then return
    # Decimal(normalized). Raise CurrencyParseError(raw) (chaining from InvalidOperation) if the
    # result is not a valid Decimal.
    raise NotImplementedError("TODO US-02: parse the amount into an exact Decimal")


def normalize_currency(raw: str) -> Money:
    """Parse a currency string in any supported format into an exact :class:`Money`."""
    # TODO US-02 (LO-3): Detect the currency with _detect_currency(raw), strip everything except
    # digits and separators (re.sub(r"[^0-9.,]", "", raw)), raise CurrencyParseError(raw) if
    # nothing numeric remains, and return Money(amount=_parse_amount(numeric, raw),
    # currency=<detected code>).
    raise NotImplementedError("TODO US-02: implement currency normalization")


def normalize_timestamp(raw: object) -> str:
    """Convert a Unix epoch (int / float / numeric string) to an ISO-8601 UTC string.

    Already-ISO-8601 input is returned unchanged (so the hook is idempotent).
    """
    # TODO US-02 (LO-3): Reject bool explicitly (it is an int subclass). For int/float, return
    # datetime.fromtimestamp(float(raw), UTC).isoformat(). For a str: if it is all digits, treat
    # it as an epoch; otherwise validate it parses as ISO-8601 (datetime.fromisoformat) and
    # return it unchanged. Anything else raises TimestampParseError(raw).
    raise NotImplementedError("TODO US-02: implement timestamp normalization")


def coerce_money(value: object) -> Money:
    """Coerce a tool-input amount (number, currency string, or Money dict) to exact :class:`Money`.

    Bare numbers are assumed to be in the threshold currency (USD-equivalent).
    """
    if isinstance(value, Money):
        return value
    if isinstance(value, bool):
        raise CurrencyParseError(str(value))
    if isinstance(value, str):
        return normalize_currency(value)
    if isinstance(value, (int, float)):
        return Money(amount=Decimal(str(value)), currency=THRESHOLD_CURRENCY)
    if isinstance(value, dict) and set(value) == {"amount", "currency"}:
        return Money(amount=Decimal(str(value["amount"])), currency=str(value["currency"]))
    raise CurrencyParseError(str(value))


def normalize_status(raw: object) -> str:
    """Map a numeric status code to its canonical label. Raises on an unknown numeric code.

    String labels already in the canonical vocabulary are returned unchanged (idempotent).
    """
    # TODO US-02 (LO-3): If raw is already a canonical label string (in _STATUS_LABELS.values()),
    # return it unchanged. Reject bool. Convert numeric-string codes to int, look the code up in
    # _STATUS_LABELS, and return the label. Raise StatusCodeError(raw) on any unknown code.
    raise NotImplementedError("TODO US-02: implement status normalization")
