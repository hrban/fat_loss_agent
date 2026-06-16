from __future__ import annotations

from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.repositories.db import get_connection


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MealRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def save_meal(self, user_id: str, raw_text: str, meal: PendingMealEstimate) -> int:
        now = utc_now_iso()
        with get_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO meal_logs (
                    user_id, logged_at, meal_type, raw_text, title,
                    total_calories, protein_g, carbs_g, fat_g,
                    confidence, notes, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    now,
                    meal.meal_type,
                    raw_text,
                    meal.title,
                    meal.total_calories,
                    meal.protein_g,
                    meal.carbs_g,
                    meal.fat_g,
                    meal.confidence,
                    meal.notes,
                    now,
                    now,
                ),
            )
            meal_log_id = int(cursor.lastrowid)
            for item in meal.items:
                conn.execute(
                    """
                    INSERT INTO meal_items (
                        meal_log_id, name, amount_text, calories,
                        protein_g, carbs_g, fat_g, confidence, notes
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        meal_log_id,
                        item.name,
                        item.amount_text,
                        item.calories,
                        item.protein_g,
                        item.carbs_g,
                        item.fat_g,
                        item.confidence,
                        item.notes,
                    ),
                )
        return meal_log_id

    def list_meals_for_day(self, user_id: str, target_date: date) -> list[dict[str, Any]]:
        start = datetime.combine(target_date, time.min, tzinfo=timezone.utc).isoformat()
        end = datetime.combine(target_date, time.max, tzinfo=timezone.utc).isoformat()
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM meal_logs
                WHERE user_id = ? AND logged_at BETWEEN ? AND ?
                ORDER BY logged_at ASC
                """,
                (user_id, start, end),
            ).fetchall()
        return [dict(row) for row in rows]
