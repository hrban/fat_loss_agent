from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.db import get_connection


class ChatRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def add_message(
        self,
        *,
        user_id: str,
        role: str,
        content: str,
        message_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO chat_messages (
                    user_id, role, content, message_type, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    role,
                    content,
                    message_type,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )

    def list_recent(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return list(reversed([dict(row) for row in rows]))
