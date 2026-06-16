import pytest

from fat_loss_agent.llm.base import LLMResult
from fat_loss_agent.services.vision_nutrition_service import VisionNutritionService


class FakeVisionLLM:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def generate_json_with_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_path,
        schema_name: str,
    ) -> LLMResult:
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "image_path": image_path,
                "schema_name": schema_name,
            }
        )
        return LLMResult(
            content_json=self.payload,
            raw_text="{}",
            provider="fake",
            model="fake-vision-model",
            prompt_tokens=1,
            completion_tokens=2,
            latency_ms=3,
        )


def valid_payload():
    return {
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
        "notes": "按可见份量估算",
    }


def test_estimate_meal_from_photo_returns_valid_pending_meal():
    llm = FakeVisionLLM(valid_payload())
    service = VisionNutritionService(llm)

    result = service.estimate_meal_from_photo(
        photo_path="/tmp/lunch.jpg",
        note="少油",
        profile={"daily_calorie_target": 1800},
        today_summary={"total_calories": 0},
    )

    assert result.meal.title == "鸡蛋米饭"
    assert result.llm.model == "fake-vision-model"
    assert llm.calls[0]["image_path"] == "/tmp/lunch.jpg"
    assert "少油" in llm.calls[0]["user_prompt"]
    assert llm.calls[0]["schema_name"] == "PendingMealEstimate"


def test_estimate_meal_from_photo_rejects_invalid_schema():
    service = VisionNutritionService(FakeVisionLLM({"is_food_log": True, "items": []}))

    with pytest.raises(ValueError):
        service.estimate_meal_from_photo(
            photo_path="/tmp/lunch.jpg",
            note="",
            profile={},
            today_summary={},
        )
