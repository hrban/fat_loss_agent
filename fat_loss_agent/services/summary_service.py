from __future__ import annotations

from typing import Any


class SummaryService:
    @staticmethod
    def build_dashboard(profile: dict[str, Any] | None, meal_summary: dict[str, Any]) -> dict[str, Any]:
        calorie_target = float(profile["daily_calorie_target"]) if profile else 0
        protein_target = float(profile["daily_protein_target_g"]) if profile else 0
        consumed_calories = float(meal_summary.get("total_calories", 0))
        consumed_protein = float(meal_summary.get("protein_g", 0))
        remaining_calories = round(calorie_target - consumed_calories, 1)
        remaining_protein = round(protein_target - consumed_protein, 1)

        if not profile:
            suggestion = "先完成我的档案，系统才能计算今日剩余额度。"
        elif remaining_protein > 30:
            suggestion = "晚些时候优先补蛋白质，主食按剩余热量控制。"
        elif remaining_calories < 300:
            suggestion = "今日热量空间不多，后续选择低脂高蛋白食物。"
        else:
            suggestion = "今日还有一定空间，保持蛋白质和蔬菜优先。"

        return {
            "daily_calorie_target": calorie_target,
            "daily_protein_target_g": protein_target,
            "consumed_calories": consumed_calories,
            "consumed_protein_g": consumed_protein,
            "remaining_calories": remaining_calories,
            "remaining_protein_g": remaining_protein,
            "meals": meal_summary.get("meals", []),
            "suggestion": suggestion,
        }
