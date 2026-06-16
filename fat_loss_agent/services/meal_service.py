from __future__ import annotations

from datetime import date
from typing import Any

from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.repositories.meal_repo import MealRepository


class MealService:
    def __init__(self, repo: MealRepository):
        self.repo = repo

    def save_meal_log(self, user_id: str, raw_text: str, meal: PendingMealEstimate) -> int:
        return self.repo.save_meal(user_id=user_id, raw_text=raw_text, meal=meal)

    def get_today_summary(self, user_id: str) -> dict[str, Any]:
        meals = self.repo.list_meals_for_day(user_id, date.today())
        return {
            "total_calories": round(sum(row["total_calories"] for row in meals), 1),
            "protein_g": round(sum(row["protein_g"] for row in meals), 1),
            "carbs_g": round(sum(row["carbs_g"] for row in meals), 1),
            "fat_g": round(sum(row["fat_g"] for row in meals), 1),
            "meals": meals,
        }
