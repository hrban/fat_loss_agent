from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoalResult:
    bmr_kcal: int
    daily_calorie_target: int
    daily_protein_target_g: int
    goal_explanation: str


ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}

DEFICITS = {
    "conservative": 300,
    "standard": 500,
    "aggressive": 700,
}

SPEED_LABELS = {
    "conservative": "保守",
    "standard": "标准",
    "aggressive": "激进",
}


def calculate_goals(
    *,
    sex: str,
    age: int,
    height_cm: float,
    current_weight_kg: float,
    target_weight_kg: float,
    activity_level: str,
    fat_loss_speed: str,
) -> GoalResult:
    if sex == "male":
        bmr = 10 * current_weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * current_weight_kg + 6.25 * height_cm - 5 * age - 161

    factor = ACTIVITY_FACTORS.get(activity_level, ACTIVITY_FACTORS["light"])
    deficit = DEFICITS.get(fat_loss_speed, DEFICITS["standard"])
    tdee = bmr * factor
    min_calories = 1500 if sex == "male" else 1200
    calorie_target = max(int(round(tdee - deficit)), min_calories)
    protein_target = int(round(current_weight_kg * 1.6))
    label = SPEED_LABELS.get(fat_loss_speed, SPEED_LABELS["standard"])
    explanation = (
        f"按 Mifflin-St Jeor 公式估算 BMR，活动系数 {factor}，"
        f"{label}减脂每日约 {deficit} kcal 缺口。"
    )

    return GoalResult(
        bmr_kcal=int(round(bmr)),
        daily_calorie_target=calorie_target,
        daily_protein_target_g=protein_target,
        goal_explanation=explanation,
    )
