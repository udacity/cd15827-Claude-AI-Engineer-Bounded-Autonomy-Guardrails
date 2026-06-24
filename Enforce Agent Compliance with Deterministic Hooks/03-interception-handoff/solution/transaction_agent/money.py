"""Heterogeneous-format normalizers: currency strings, timestamps, numeric status codes.

These exist because upstream tools emit data in whatever format their source system uses. The
PostToolUse normalization hook is the single place that canonicalizes them, so the model only
ever reasons over one representation. Currency amounts are exact ``Decimal`` — never ``float``.
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
    has_dot = "." in numeric
    has_comma = "," in numeric
    if has_dot and has_comma:
        # The separator that appears last is the decimal separator; the other is thousands.
        decimal_sep = "." if numeric.rfind(".") > numeric.rfind(",") else ","
        thousands_sep = "," if decimal_sep == "." else "."
        normalized = numeric.replace(thousands_sep, "").replace(decimal_sep, ".")
    elif has_comma:
        # Only commas: grouped thousands (1,234) → strip; otherwise a decimal comma (1,56) → dot.
        if re.fullmatch(r"\d{1,3}(,\d{3})+", numeric):
            normalized = numeric.replace(",", "")
        else:
            normalized = numeric.replace(",", ".")
    else:
        normalized = numeric  # only dot (decimal) or plain integer
    try:
        return Decimal(normalized)
    except InvalidOperation as exc:
        raise CurrencyParseError(raw) from exc


def normalize_currency(raw: str) -> Money:
    """Parse a currency string in any supported format into an exact :class:`Money`."""
    currency = _detect_currency(raw)
    numeric = re.sub(r"[^0-9.,]", "", raw)
    if not numeric:
        raise CurrencyParseError(raw)
    return Money(amount=_parse_amount(numeric, raw), currency=currency)


def normalize_timestamp(raw: object) -> str:
    """Convert a Unix epoch (int / float / numeric string) to an ISO-8601 UTC string.

    Already-ISO-8601 input is returned unchanged (so the hook is idempotent).
    """
    if isinstance(raw, bool):  # bool is an int subclass; reject it explicitly
        raise TimestampParseError(raw)
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(float(raw), UTC).isoformat()
    if isinstance(raw, str):
        if raw.isdigit():
            return datetime.fromtimestamp(int(raw), UTC).isoformat()
        try:
            datetime.fromisoformat(raw)
        except ValueError as exc:
            raise TimestampParseError(raw) from exc
        return raw
    raise TimestampParseError(raw)


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
    if isinstance(raw, str) and raw in _STATUS_LABELS.values():
        return raw
    if isinstance(raw, bool):
        raise StatusCodeError(raw)
    code = int(raw) if isinstance(raw, str) and raw.isdigit() else raw
    if isinstance(code, int) and code in _STATUS_LABELS:
        return _STATUS_LABELS[code]
    raise StatusCodeError(raw)
