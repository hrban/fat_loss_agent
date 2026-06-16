from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.db import get_connection


class TraceRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def insert(self, trace: dict[str, Any]) -> None:
        trace = {**trace, "created_at": datetime.now(timezone.utc).isoformat()}
        columns = ", ".join(trace.keys())
        bind_marks = ", ".join("?" for _ in trace)
        with get_connection(self.db_path) as conn:
            conn.execute(
                f"INSERT INTO agent_traces ({columns}) VALUES ({bind_marks})",
                list(trace.values()),
            )

    def list_recent(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM agent_traces
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [dict(row) for row in rows]
