from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate
from fat_loss_agent.repositories.db import init_db
from fat_loss_agent.repositories.meal_repo import MealRepository
from fat_loss_agent.services.meal_service import MealService
from fat_loss_agent.services.summary_service import SummaryService


def build_test_meal() -> PendingMealEstimate:
    return PendingMealEstimate(
        is_food_log=True,
        meal_type="lunch",
        title="鸡蛋米饭",
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
    )


def test_save_meal_and_get_today_summary(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)
    service = MealService(MealRepository(db_path))
    meal = build_test_meal()

    saved_id = service.save_meal_log("local_user", "午饭吃了两个鸡蛋", meal)
    summary = service.get_today_summary("local_user")

    assert saved_id > 0
    assert summary["total_calories"] == 140
    assert summary["protein_g"] == 12
    assert len(summary["meals"]) == 1


def test_save_photo_meal_persists_photo_metadata(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)
    service = MealService(MealRepository(db_path))
    meal = build_test_meal()

    service.save_meal_log(
        "local_user",
        "照片记录：午饭",
        meal,
        input_type="photo",
        photo_path="/tmp/lunch.jpg",
    )
    summary = service.get_today_summary("local_user")

    assert summary["meals"][0]["input_type"] == "photo"
    assert summary["meals"][0]["photo_path"] == "/tmp/lunch.jpg"


def test_summary_service_calculates_remaining_budget():
    dashboard = SummaryService.build_dashboard(
        profile={"daily_calorie_target": 1800, "daily_protein_target_g": 120},
        meal_summary={"total_calories": 650, "protein_g": 42, "carbs_g": 58, "fat_g": 24, "meals": []},
    )

    assert dashboard["remaining_calories"] == 1150
    assert dashboard["remaining_protein_g"] == 78
    assert "蛋白质" in dashboard["suggestion"]
