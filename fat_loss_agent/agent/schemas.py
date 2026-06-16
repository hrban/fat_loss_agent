from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


MealType = Literal["breakfast", "lunch", "dinner", "snack", "unknown"]


class MealItemEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    amount_text: str = Field(min_length=1)
    calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    notes: str = ""


class PendingMealEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_food_log: bool
    meal_type: MealType = "unknown"
    title: str = ""
    items: list[MealItemEstimate] = Field(default_factory=list)
    total_calories: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    carbs_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)
    confidence: float = Field(ge=0, le=1)
    notes: str = ""

    @model_validator(mode="after")
    def require_items_for_food_log(self) -> "PendingMealEstimate":
        if self.is_food_log and not self.items:
            raise ValueError("food log estimates must include at least one item")
        return self
