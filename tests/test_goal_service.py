from fat_loss_agent.services.goal_service import calculate_goals


def test_calculate_goals_for_standard_male_profile():
    result = calculate_goals(
        sex="male",
        age=30,
        height_cm=175,
        current_weight_kg=80,
        target_weight_kg=72,
        activity_level="moderate",
        fat_loss_speed="standard",
    )

    assert 1600 <= result.daily_calorie_target <= 2300
    assert result.daily_protein_target_g == 128
    assert "标准" in result.goal_explanation


def test_calculate_goals_for_conservative_female_profile():
    result = calculate_goals(
        sex="female",
        age=28,
        height_cm=165,
        current_weight_kg=62,
        target_weight_kg=58,
        activity_level="light",
        fat_loss_speed="conservative",
    )

    assert result.bmr_kcal > 1200
    assert result.daily_calorie_target >= 1200
    assert result.daily_protein_target_g == 99
