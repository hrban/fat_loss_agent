from __future__ import annotations

from typing import Any

from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.services.goal_service import calculate_goals


class ProfileService:
    def __init__(self, repo: ProfileRepository):
        self.repo = repo

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.repo.get_by_user_id(user_id)

    def save_profile(
        self,
        *,
        user_id: str,
        nickname: str,
        sex: str,
        age: int,
        height_cm: float,
        current_weight_kg: float,
        target_weight_kg: float,
        activity_level: str,
        fat_loss_speed: str,
        diet_preferences: str,
    ) -> dict[str, Any]:
        goals = calculate_goals(
            sex=sex,
            age=age,
            height_cm=height_cm,
            current_weight_kg=current_weight_kg,
            target_weight_kg=target_weight_kg,
            activity_level=activity_level,
            fat_loss_speed=fat_loss_speed,
        )
        return self.repo.upsert(
            {
                "user_id": user_id,
                "nickname": nickname,
                "sex": sex,
                "age": age,
                "height_cm": height_cm,
                "current_weight_kg": current_weight_kg,
                "target_weight_kg": target_weight_kg,
                "activity_level": activity_level,
                "fat_loss_speed": fat_loss_speed,
                "diet_preferences": diet_preferences,
                "bmr_kcal": goals.bmr_kcal,
                "daily_calorie_target": goals.daily_calorie_target,
                "daily_protein_target_g": goals.daily_protein_target_g,
                "goal_explanation": goals.goal_explanation,
            }
        )
