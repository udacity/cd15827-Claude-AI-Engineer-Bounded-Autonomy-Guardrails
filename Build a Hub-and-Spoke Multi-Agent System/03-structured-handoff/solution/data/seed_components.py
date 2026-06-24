"""Seed the components.sqlite table used by the supplier subagent's sqlite_lookup tool.

Run with: `.venv/bin/python data/seed_components.py`
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

SEED_ROWS: list[tuple[str, str, str, str, str]] = [
    # component_id, supplier, lot_id, received_at, prior_incidents (csv)
    ("IC-REG-7805", "PrecisionSilicon Ltd", "LOT-PSL-2026-04-118", "2026-04-12T08:00:00", ""),
    ("IC-REG-7805", "PrecisionSilicon Ltd", "LOT-PSL-2026-03-072", "2026-03-04T08:00:00", "INC-2026-03-019"),
    ("RES-100-OHM", "Eastside Passive", "LOT-EP-2026-05-204", "2026-05-02T10:30:00", ""),
    ("CAP-10UF-A", "Maple Components", "LOT-MC-2026-04-301", "2026-04-22T11:00:00", "INC-2026-04-014,INC-2026-04-022"),
    ("CAP-10UF-A", "Maple Components", "LOT-MC-2026-03-115", "2026-03-11T11:00:00", ""),
    ("LED-RED-T0805", "BrightOptics Co", "LOT-BO-2026-05-051", "2026-05-09T09:15:00", ""),
    ("XTAL-16MHZ", "Riverside Quartz", "LOT-RQ-2026-04-007", "2026-04-30T14:45:00", "INC-2026-05-001"),
]


def main() -> None:
    db_path = Path(__file__).parent / "components.sqlite"
    if db_path.exists():
        db_path.unlink()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE components (
                component_id TEXT NOT NULL,
                supplier TEXT NOT NULL,
                lot_id TEXT NOT NULL,
                received_at TEXT NOT NULL,
                prior_incidents TEXT NOT NULL DEFAULT ''
            )
            """
        )
        conn.execute(
            "CREATE INDEX idx_components_lookup ON components(component_id, received_at)"
        )
        conn.executemany(
            "INSERT INTO components VALUES (?, ?, ?, ?, ?)",
            SEED_ROWS,
        )
    print(f"seeded {db_path} with {len(SEED_ROWS)} rows")


if __name__ == "__main__":
    main()
