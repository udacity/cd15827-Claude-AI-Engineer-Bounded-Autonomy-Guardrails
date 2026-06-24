"""Tools exposed to subagents.

Only the supplier subagent uses an external tool (the SQLite component-sourcing
lookup). The Anthropic runner wires this in dynamically based on each subagent's
`allowed_tools`.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from manufacturing_qc.models import ComponentRecord


def sqlite_lookup(db_path: Path, component_id: str) -> ComponentRecord | None:
    """Return the most recent component record matching `component_id`, or None."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT component_id, supplier, lot_id, received_at, prior_incidents
            FROM components
            WHERE component_id = ?
            ORDER BY received_at DESC
            LIMIT 1
            """,
            (component_id,),
        ).fetchone()
    if row is None:
        return None
    incidents = [s for s in (row["prior_incidents"] or "").split(",") if s]
    return ComponentRecord(
        component_id=row["component_id"],
        supplier=row["supplier"],
        lot_id=row["lot_id"],
        received_at=row["received_at"],
        prior_incidents=incidents,
    )


SQLITE_LOOKUP_TOOL_SCHEMA: dict[str, object] = {
    "name": "sqlite_lookup",
    "description": (
        "Look up the most recent sourcing record for a single component_id in the "
        "BrightCircuit components database. Returns supplier, lot_id, received_at, "
        "and any prior incident IDs associated with that component."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "component_id": {
                "type": "string",
                "description": "The component_id to look up, e.g. 'IC-REG-7805'.",
            }
        },
        "required": ["component_id"],
    },
}
