from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.db import get_connection


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProfileRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_by_user_id(self, user_id: str) -> dict[str, Any] | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert(self, profile: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        existing = self.get_by_user_id(profile["user_id"])
        data = {**profile, "updated_at": now}
        if existing:
            assignments = ", ".join(f"{key} = ?" for key in data if key != "user_id")
            values = [value for key, value in data.items() if key != "user_id"]
            values.append(profile["user_id"])
            with get_connection(self.db_path) as conn:
                conn.execute(f"UPDATE profiles SET {assignments} WHERE user_id = ?", values)
            return self.get_by_user_id(profile["user_id"]) or data

        data["created_at"] = now
        columns = ", ".join(data.keys())
        bind_marks = ", ".join("?" for _ in data)
        with get_connection(self.db_path) as conn:
            conn.execute(
                f"INSERT INTO profiles ({columns}) VALUES ({bind_marks})",
                list(data.values()),
            )
        return self.get_by_user_id(profile["user_id"]) or data
