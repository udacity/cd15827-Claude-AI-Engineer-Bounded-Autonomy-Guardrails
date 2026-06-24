"""US-02 — PostToolUse heterogeneous data normalization hook."""
from __future__ import annotations

from decimal import Decimal

import pytest

from transaction_agent.hooks import normalization_hook
from transaction_agent.models import Money, SessionState
from transaction_agent.money import (
    CurrencyParseError,
    StatusCodeError,
    TimestampParseError,
    normalize_currency,
    normalize_status,
    normalize_timestamp,
)

# --- AC-02-01: currency parsing across formats, exact Decimal ---


@pytest.mark.parametrize(
    ("raw", "amount", "currency"),
    [
        ("$1,234.56", Decimal("1234.56"), "USD"),
        ("1234.56 USD", Decimal("1234.56"), "USD"),
        ("EUR 1.234,56", Decimal("1234.56"), "EUR"),
        ("£999.00", Decimal("999.00"), "GBP"),
        ("45200.00 USD", Decimal("45200.00"), "USD"),
        ("EUR 8.500,75", Decimal("8500.75"), "EUR"),
    ],
)
def test_normalize_currency_formats(raw: str, amount: Decimal, currency: str) -> None:
    money = normalize_currency(raw)
    assert money == Money(amount=amount, currency=currency)
    assert money.amount == amount  # exact Decimal equality, no float drift


def test_normalize_currency_is_decimal_not_float() -> None:
    assert isinstance(normalize_currency("$0.10").amount, Decimal)
    # The classic float trap: 0.1 + 0.2 != 0.3 as float, but Decimal is exact.
    total = normalize_currency("$0.10").amount + normalize_currency("$0.20").amount
    assert total == Decimal("0.30")


# --- AC-02-02: typed errors, no silent default ---


def test_currency_parse_error_carries_raw() -> None:
    with pytest.raises(CurrencyParseError) as exc:
        normalize_currency("not money")
    assert "not money" in str(exc.value)


def test_timestamp_parse_error_carries_raw() -> None:
    with pytest.raises(TimestampParseError) as exc:
        normalize_timestamp("definitely-not-a-date")
    assert "definitely-not-a-date" in str(exc.value)


def test_status_code_error_carries_raw() -> None:
    with pytest.raises(StatusCodeError) as exc:
        normalize_status(99)
    assert "99" in str(exc.value)


# --- AC-02-06: timestamp + status normalizers ---


def test_normalize_timestamp_epoch_to_iso() -> None:
    assert normalize_timestamp(1715212800) == "2024-05-09T00:00:00+00:00"
    assert normalize_timestamp("1715212800") == "2024-05-09T00:00:00+00:00"


def test_normalize_timestamp_iso_passthrough() -> None:
    iso = "2024-05-09T00:00:00+00:00"
    assert normalize_timestamp(iso) == iso


def test_normalize_status_maps_codes() -> None:
    assert normalize_status(1) == "active"
    assert normalize_status(2) == "dormant"
    assert normalize_status(3) == "frozen"


# --- AC-02-03 + AC-02-04: the hook canonicalizes by key family ---


def _customer_result() -> dict[str, object]:
    return {
        "customer_id": "CUST-10293",
        "account_balance": "$12,450.00",
        "verified_at": 1715212800,
        "status": 1,
        "risk_notes": "No adverse history",  # non-currency string passes through
    }


def test_hook_normalizes_all_families() -> None:
    out = normalization_hook("get_customer", _customer_result(), SessionState())
    assert out["account_balance"] == {"amount": "12450.00", "currency": "USD"}
    assert Decimal(out["account_balance"]["amount"]) == Decimal("12450.00")
    assert out["verified_at"] == "2024-05-09T00:00:00+00:00"
    assert out["status"] == "active"
    assert out["risk_notes"] == "No adverse history"  # untouched
    assert out["customer_id"] == "CUST-10293"  # untouched


def test_hook_leaves_non_currency_amounts_and_none() -> None:
    # A transfer result: amount is a number, status is a non-code string, verified_at absent.
    result = {"status": "executed", "amount": 4500.0, "transaction_id": "TXN-1"}
    out = normalization_hook("initiate_transfer", result, SessionState())
    assert out["amount"] == 4500.0  # numeric amount not a currency string -> untouched
    assert out["status"] == "executed"  # not a numeric code -> untouched


def test_hook_handles_null_timestamp() -> None:
    result = {"customer_id": "C", "verified_at": None, "status": 2}
    out = normalization_hook("get_customer", result, SessionState())
    assert out["verified_at"] is None
    assert out["status"] == "dormant"


# --- AC-02-05: idempotency across all families ---


def test_hook_idempotent() -> None:
    once = normalization_hook("get_customer", _customer_result(), SessionState())
    twice = normalization_hook("get_customer", once, SessionState())
    assert twice == once
