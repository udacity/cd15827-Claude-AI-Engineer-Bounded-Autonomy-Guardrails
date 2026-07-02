"""Central configuration. Threshold and model are constants here, never inlined elsewhere."""
from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# $10,000 is this project's instantiation of the exam's generic "amount exceeds a threshold"
# interception (Task 1.5 S2). Wire transfers strictly above this are redirected to compliance.
TRANSFER_THRESHOLD = Decimal("10000")
THRESHOLD_CURRENCY = "USD"

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR = Path(os.environ.get("TXN_AGENT_DATA_DIR", _DEFAULT_DATA_DIR))
