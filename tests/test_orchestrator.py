from fat_loss_agent.agent.orchestrator import AgentOrchestrator
from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate
from fat_loss_agent.llm.base import LLMResult
from fat_loss_agent.services.nutrition_service import MealEstimationResult


class FakeProfileService:
    def get_profile(self, user_id):
        return {"daily_calorie_target": 1800, "daily_protein_target_g": 120}


class FakeMealService:
    def get_today_summary(self, user_id):
        return {"total_calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "meals": []}


class FakeNutritionService:
    def estimate_meal_from_text(self, *, text, profile, today_summary):
        return MealEstimationResult(
            meal=PendingMealEstimate(
                is_food_log=True,
                meal_type="lunch",
                title="鸡蛋",
                items=[
                    MealItemEstimate(
                        name="鸡蛋",
                        amount_text="2个",
                        calories=140,
                        protein_g=12,
                        carbs_g=1,
                        fat_g=10,
                        confidence=0.8,
                        notes="",
                    )
                ],
                total_calories=140,
                protein_g=12,
                carbs_g=1,
                fat_g=10,
                confidence=0.8,
                notes="",
            ),
            llm=LLMResult(
                content_json={},
                raw_text="{}",
                provider="fake",
                model="fake-model",
                prompt_tokens=1,
                completion_tokens=2,
                latency_ms=3,
            ),
        )


class FakeVisionNutritionService:
    def estimate_meal_from_photo(self, *, photo_path, note, profile, today_summary):
        return MealEstimationResult(
            meal=PendingMealEstimate(
                is_food_log=True,
                meal_type="dinner",
                title="照片晚餐",
                items=[
                    MealItemEstimate(
                        name="牛肉",
                        amount_text="1份",
                        calories=220,
                        protein_g=26,
                        carbs_g=4,
                        fat_g=11,
                        confidence=0.7,
                        notes="按照片估算",
                    )
                ],
                total_calories=220,
                protein_g=26,
                carbs_g=4,
                fat_g=11,
                confidence=0.7,
                notes="",
            ),
            llm=LLMResult(
                content_json={},
                raw_text="{}",
                provider="fake",
                model="fake-vision-model",
                prompt_tokens=3,
                completion_tokens=4,
                latency_ms=5,
            ),
        )


class FakeTraceService:
    def __init__(self):
        self.calls = []

    def record_trace(self, **kwargs):
        self.calls.append(kwargs)
        return "trace-1"


def test_orchestrator_returns_pending_meal_and_records_trace():
    trace_service = FakeTraceService()
    orchestrator = AgentOrchestrator(
        profile_service=FakeProfileService(),
        meal_service=FakeMealService(),
        nutrition_service=FakeNutritionService(),
        vision_nutrition_service=FakeVisionNutritionService(),
        trace_service=trace_service,
    )

    result = orchestrator.handle_meal_text("local_user", "午饭吃了两个鸡蛋")

    assert result.meal.title == "鸡蛋"
    assert result.trace_id == "trace-1"
    assert trace_service.calls[0]["intent"] == "meal_log"


def test_orchestrator_handles_photo_meal_and_records_trace():
    trace_service = FakeTraceService()
    orchestrator = AgentOrchestrator(
        profile_service=FakeProfileService(),
        meal_service=FakeMealService(),
        nutrition_service=FakeNutritionService(),
        vision_nutrition_service=FakeVisionNutritionService(),
        trace_service=trace_service,
    )

    result = orchestrator.handle_meal_photo("local_user", "/tmp/lunch.jpg", "少油")

    assert result.meal.title == "照片晚餐"
    assert result.trace_id == "trace-1"
    assert trace_service.calls[0]["intent"] == "meal_photo_log"
