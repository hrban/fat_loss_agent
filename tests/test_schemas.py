import pytest
from pydantic import ValidationError

from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate


def test_pending_meal_accepts_valid_qwen_shape():
    meal = PendingMealEstimate(
        is_food_log=True,
        meal_type="lunch",
        title="鸡蛋和米饭",
        items=[
            MealItemEstimate(
                name="鸡蛋",
                amount_text="2个",
                calories=140,
                protein_g=12,
                carbs_g=1,
                fat_g=10,
                confidence=0.8,
                notes="按水煮蛋估算",
            )
        ],
        total_calories=140,
        protein_g=12,
        carbs_g=1,
        fat_g=10,
        confidence=0.8,
        notes="份量明确",
    )

    assert meal.items[0].name == "鸡蛋"
    assert meal.total_calories == 140


def test_pending_meal_rejects_negative_nutrition():
    with pytest.raises(ValidationError):
        MealItemEstimate(
            name="米饭",
            amount_text="一碗",
            calories=-1,
            protein_g=4,
            carbs_g=55,
            fat_g=1,
            confidence=0.6,
            notes="非法热量",
        )


def test_pending_meal_requires_item_when_food_log():
    with pytest.raises(ValidationError):
        PendingMealEstimate(
            is_food_log=True,
            meal_type="dinner",
            title="空餐食",
            items=[],
            total_calories=0,
            protein_g=0,
            carbs_g=0,
            fat_g=0,
            confidence=0.2,
            notes="没有明细",
        )
