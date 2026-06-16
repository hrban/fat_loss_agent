from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from fat_loss_agent.agent.prompts import MEAL_ESTIMATION_SYSTEM_PROMPT, build_meal_estimation_user_prompt
from fat_loss_agent.agent.schemas import PendingMealEstimate
from fat_loss_agent.llm.base import LLMClient, LLMResult


@dataclass(frozen=True)
class MealEstimationResult:
    meal: PendingMealEstimate
    llm: LLMResult


class NutritionService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def estimate_meal_from_text(
        self,
        *,
        text: str,
        profile: dict[str, Any] | None,
        today_summary: dict[str, Any],
    ) -> MealEstimationResult:
        llm_result = self.llm_client.generate_json(
            system_prompt=MEAL_ESTIMATION_SYSTEM_PROMPT,
            user_prompt=build_meal_estimation_user_prompt(text, profile or {}, today_summary),
            schema_name="PendingMealEstimate",
        )
        try:
            meal = PendingMealEstimate.model_validate(llm_result.content_json)
        except ValidationError as exc:
            raise ValueError(f"invalid meal estimate schema: {exc}") from exc
        return MealEstimationResult(meal=meal, llm=llm_result)
