from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from fat_loss_agent.agent.prompts import MEAL_PHOTO_ESTIMATION_SYSTEM_PROMPT, build_meal_photo_estimation_user_prompt
from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.llm.base import LLMClient
from fat_loss_agent.services.nutrition_service import MealEstimationResult


class VisionNutritionService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def estimate_meal_from_photo(
        self,
        *,
        photo_path: str | Path,
        note: str,
        profile: dict[str, Any] | None,
        today_summary: dict[str, Any],
    ) -> MealEstimationResult:
        llm_result = self.llm_client.generate_json_with_image(
            system_prompt=MEAL_PHOTO_ESTIMATION_SYSTEM_PROMPT,
            user_prompt=build_meal_photo_estimation_user_prompt(note, profile or {}, today_summary),
            image_path=photo_path,
            schema_name="PendingMealEstimate",
        )
        try:
            meal = PendingMealEstimate.model_validate(llm_result.content_json)
        except ValidationError as exc:
            raise ValueError(f"invalid meal photo estimate schema: {exc}") from exc
        return MealEstimationResult(meal=meal, llm=llm_result)
