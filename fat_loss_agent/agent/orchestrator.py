from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fat_loss_agent.agent.schemas import PendingMealEstimate


@dataclass(frozen=True)
class OrchestratorMealResult:
    meal: PendingMealEstimate
    trace_id: str


class AgentOrchestrator:
    def __init__(self, *, profile_service: Any, meal_service: Any, nutrition_service: Any, trace_service: Any):
        self.profile_service = profile_service
        self.meal_service = meal_service
        self.nutrition_service = nutrition_service
        self.trace_service = trace_service

    def handle_meal_text(self, user_id: str, text: str) -> OrchestratorMealResult:
        profile = self.profile_service.get_profile(user_id)
        today_summary = self.meal_service.get_today_summary(user_id)
        tool_calls = [
            {"name": "profile_service.get_profile"},
            {"name": "meal_service.get_today_summary"},
            {"name": "nutrition_service.estimate_meal_from_text"},
        ]
        try:
            estimation = self.nutrition_service.estimate_meal_from_text(
                text=text,
                profile=profile,
                today_summary=today_summary,
            )
            trace_id = self.trace_service.record_trace(
                user_id=user_id,
                user_input=text,
                intent="meal_log",
                tool_calls=tool_calls,
                llm_provider=estimation.llm.provider,
                llm_model=estimation.llm.model,
                llm_prompt_tokens=estimation.llm.prompt_tokens,
                llm_completion_tokens=estimation.llm.completion_tokens,
                llm_latency_ms=estimation.llm.latency_ms,
                status="success",
                error_message="",
            )
            return OrchestratorMealResult(meal=estimation.meal, trace_id=trace_id)
        except Exception as exc:
            self.trace_service.record_trace(
                user_id=user_id,
                user_input=text,
                intent="meal_log",
                tool_calls=tool_calls,
                llm_provider="unknown",
                llm_model="unknown",
                llm_prompt_tokens=0,
                llm_completion_tokens=0,
                llm_latency_ms=0,
                status="error",
                error_message=str(exc),
            )
            raise
