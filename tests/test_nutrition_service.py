import pytest

from fat_loss_agent.llm.base import LLMResult
from fat_loss_agent.services.nutrition_service import NutritionService


class FakeLLM:
    def __init__(self, payload):
        self.payload = payload

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> LLMResult:
        return LLMResult(
            content_json=self.payload,
            raw_text="{}",
            provider="fake",
            model="fake-model",
            prompt_tokens=1,
            completion_tokens=2,
            latency_ms=3,
        )


def test_estimate_meal_from_text_returns_valid_pending_meal():
    service = NutritionService(
        FakeLLM(
            {
                "is_food_log": True,
                "meal_type": "lunch",
                "title": "鸡蛋米饭",
                "items": [
                    {
                        "name": "鸡蛋",
                        "amount_text": "2个",
                        "calories": 140,
                        "protein_g": 12,
                        "carbs_g": 1,
                        "fat_g": 10,
                        "confidence": 0.8,
                        "notes": "",
                    }
                ],
                "total_calories": 140,
                "protein_g": 12,
                "carbs_g": 1,
                "fat_g": 10,
                "confidence": 0.8,
                "notes": "",
            }
        )
    )

    result = service.estimate_meal_from_text(
        text="午饭吃了两个鸡蛋",
        profile={"daily_calorie_target": 1800},
        today_summary={"total_calories": 0},
    )

    assert result.meal.title == "鸡蛋米饭"
    assert result.llm.provider == "fake"


def test_estimate_meal_rejects_invalid_schema():
    service = NutritionService(FakeLLM({"is_food_log": True, "items": []}))

    with pytest.raises(ValueError):
        service.estimate_meal_from_text(
            text="午饭吃了两个鸡蛋",
            profile={},
            today_summary={},
        )
