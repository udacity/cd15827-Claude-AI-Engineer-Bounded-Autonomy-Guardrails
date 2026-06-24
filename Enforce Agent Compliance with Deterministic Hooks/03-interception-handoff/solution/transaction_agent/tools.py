"""Simulated banking tools over local JSON customer records.

These stand in for a bank's core systems. They emit data in deliberately heterogeneous formats
(currency strings, Unix-epoch timestamps, numeric status codes) so the PostToolUse normalization
hook has real work to do. Transaction ids are derived deterministically from inputs — no clock,
no randomness — so the suite is reproducible.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from transaction_agent.config import DATA_DIR


class CustomerNotFoundError(KeyError):
    """Raised when a customer id has no record on disk."""


def load_customer(customer_id: str, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    path = data_dir / "customers" / f"{customer_id}.json"
    if not path.exists():
        raise CustomerNotFoundError(customer_id)
    record: dict[str, Any] = json.loads(path.read_text())
    return record


def verify_kyc(customer_id: str, **_: Any) -> dict[str, Any]:
    customer = load_customer(customer_id)
    verified = customer["kyc_status"] == "verified"
    return {
        "customer_id": customer_id,
        "kyc_verified": verified,
        "verified_at": customer.get("verified_at"),
    }


def get_customer(customer_id: str, **_: Any) -> dict[str, Any]:
    return load_customer(customer_id)


def initiate_transfer(
    customer_id: str, amount: Any, origin_account: str, destination_account: str, **_: Any
) -> dict[str, Any]:
    return {
        "status": "executed",
        "transaction_id": f"TXN-{origin_account}-{destination_account}-{amount}",
        "amount": amount,
        "customer_id": customer_id,
    }


def adjust_balance(customer_id: str, amount: Any, **_: Any) -> dict[str, Any]:
    return {"status": "executed", "customer_id": customer_id, "adjustment": amount}


def resolve_dispute(customer_id: str, **_: Any) -> dict[str, Any]:
    return {"status": "resolved", "customer_id": customer_id}


def build_registry() -> dict[str, Callable[..., dict[str, Any]]]:
    """The tool registry the engine dispatches against."""
    return {
        "verify_kyc": verify_kyc,
        "get_customer": get_customer,
        "initiate_transfer": initiate_transfer,
        "adjust_balance": adjust_balance,
        "resolve_dispute": resolve_dispute,
    }


def _customer_id_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {"customer_id": {"type": "string"}},
        "required": ["customer_id"],
    }


def tool_schemas() -> list[dict[str, Any]]:
    """Anthropic tool definitions (JSON-Schema ``input_schema``) for the agentic loop."""
    transfer_props = {
        "customer_id": {"type": "string"},
        "amount": {"type": "number"},
        "origin_account": {"type": "string"},
        "destination_account": {"type": "string"},
        "destination_country": {"type": "string"},
    }
    return [
        {
            "name": "verify_kyc",
            "description": "Verify a customer's KYC status; required before money movement.",
            "input_schema": _customer_id_schema(),
        },
        {
            "name": "get_customer",
            "description": "Fetch a customer's record (balance, status, home country).",
            "input_schema": _customer_id_schema(),
        },
        {
            "name": "initiate_transfer",
            "description": "Initiate a wire transfer from the customer's account.",
            "input_schema": {
                "type": "object",
                "properties": transfer_props,
                "required": ["customer_id", "amount", "origin_account", "destination_account"],
            },
        },
        {
            "name": "adjust_balance",
            "description": "Apply an account adjustment for the customer.",
            "input_schema": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}, "amount": {"type": "number"}},
                "required": ["customer_id", "amount"],
            },
        },
        {
            "name": "resolve_dispute",
            "description": "Resolve a dispute for the customer.",
            "input_schema": _customer_id_schema(),
        },
    ]


def load_request(request_id: str, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    filename = request_id.lower().replace("-", "_") + ".json"
    record: dict[str, Any] = json.loads((data_dir / "requests" / filename).read_text())
    return record


def load_scenarios(data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    data = json.loads((data_dir / "scenarios.json").read_text())
    scenarios: list[dict[str, Any]] = data["scenarios"]
    return scenarios
