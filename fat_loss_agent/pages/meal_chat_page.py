from __future__ import annotations

import streamlit as st

from fat_loss_agent.agent.orchestrator import AgentOrchestrator
from fat_loss_agent.agent.schemas import MealItemEstimate, PendingMealEstimate
from fat_loss_agent.config import AppConfig
from fat_loss_agent.llm.qwen_client import MissingQwenApiKeyError, QwenClient
from fat_loss_agent.repositories.chat_repo import ChatRepository
from fat_loss_agent.repositories.meal_repo import MealRepository
from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.repositories.trace_repo import TraceRepository
from fat_loss_agent.services.meal_service import MealService
from fat_loss_agent.services.nutrition_service import NutritionService
from fat_loss_agent.services.profile_service import ProfileService
from fat_loss_agent.services.summary_service import SummaryService
from fat_loss_agent.services.trace_service import TraceService


def build_services(config: AppConfig):
    profile_service = ProfileService(ProfileRepository(config.db_path))
    meal_service = MealService(MealRepository(config.db_path))
    trace_service = TraceService(TraceRepository(config.db_path), config.trace_log_path)
    qwen_client = QwenClient(
        api_key=config.qwen_api_key,
        base_url=config.qwen_base_url,
        model=config.qwen_model,
    )
    nutrition_service = NutritionService(qwen_client)
    orchestrator = AgentOrchestrator(
        profile_service=profile_service,
        meal_service=meal_service,
        nutrition_service=nutrition_service,
        trace_service=trace_service,
    )
    return profile_service, meal_service, orchestrator


def edit_pending_meal(meal: PendingMealEstimate) -> PendingMealEstimate:
    st.subheader("待确认餐食")
    meal_types = ["breakfast", "lunch", "dinner", "snack", "unknown"]
    meal_type = st.selectbox(
        "餐次",
        meal_types,
        index=meal_types.index(meal.meal_type),
    )
    title = st.text_input("标题", value=meal.title)
    total_calories = st.number_input("总热量 kcal", min_value=0.0, value=float(meal.total_calories))
    protein_g = st.number_input("蛋白质 g", min_value=0.0, value=float(meal.protein_g))
    carbs_g = st.number_input("碳水 g", min_value=0.0, value=float(meal.carbs_g))
    fat_g = st.number_input("脂肪 g", min_value=0.0, value=float(meal.fat_g))
    confidence = st.slider("整体置信度", min_value=0.0, max_value=1.0, value=float(meal.confidence))
    notes = st.text_area("备注", value=meal.notes)

    edited_items: list[MealItemEstimate] = []
    for index, item in enumerate(meal.items):
        with st.expander(f"食物 {index + 1}: {item.name}", expanded=True):
            name = st.text_input("名称", value=item.name, key=f"item_name_{index}")
            amount_text = st.text_input("份量", value=item.amount_text, key=f"item_amount_{index}")
            calories = st.number_input("热量 kcal", min_value=0.0, value=float(item.calories), key=f"item_cal_{index}")
            item_protein = st.number_input(
                "蛋白质 g",
                min_value=0.0,
                value=float(item.protein_g),
                key=f"item_protein_{index}",
            )
            item_carbs = st.number_input(
                "碳水 g",
                min_value=0.0,
                value=float(item.carbs_g),
                key=f"item_carbs_{index}",
            )
            item_fat = st.number_input("脂肪 g", min_value=0.0, value=float(item.fat_g), key=f"item_fat_{index}")
            item_confidence = st.slider("置信度", 0.0, 1.0, float(item.confidence), key=f"item_conf_{index}")
            item_notes = st.text_area("备注", value=item.notes, key=f"item_notes_{index}")
            edited_items.append(
                MealItemEstimate(
                    name=name,
                    amount_text=amount_text,
                    calories=calories,
                    protein_g=item_protein,
                    carbs_g=item_carbs,
                    fat_g=item_fat,
                    confidence=item_confidence,
                    notes=item_notes,
                )
            )

    return PendingMealEstimate(
        is_food_log=True,
        meal_type=meal_type,
        title=title,
        items=edited_items,
        total_calories=total_calories,
        protein_g=protein_g,
        carbs_g=carbs_g,
        fat_g=fat_g,
        confidence=confidence,
        notes=notes,
    )


def render_dashboard(profile_service: ProfileService, meal_service: MealService, user_id: str) -> None:
    profile = profile_service.get_profile(user_id)
    meal_summary = meal_service.get_today_summary(user_id)
    dashboard = SummaryService.build_dashboard(profile, meal_summary)

    st.subheader("今日摘要")
    col1, col2 = st.columns(2)
    col1.metric("剩余热量", f"{dashboard['remaining_calories']:.0f} kcal")
    col2.metric("还差蛋白质", f"{dashboard['remaining_protein_g']:.0f} g")
    st.caption(dashboard["suggestion"])
    if dashboard["meals"]:
        st.write("今日已记录")
        for meal in dashboard["meals"]:
            st.write(f"- {meal['title']}：{meal['total_calories']:.0f} kcal，蛋白质 {meal['protein_g']:.0f} g")


def render_meal_chat_page(*, config: AppConfig, user_id: str) -> None:
    st.title("饮食记录")
    left, right = st.columns([2, 1])

    with right:
        profile_service = ProfileService(ProfileRepository(config.db_path))
        meal_service = MealService(MealRepository(config.db_path))
        render_dashboard(profile_service, meal_service, user_id)

    with left:
        text = st.chat_input("输入你吃了什么，例如：午饭吃了两个鸡蛋、一碗米饭、一份牛肉")
        if text:
            ChatRepository(config.db_path).add_message(
                user_id=user_id,
                role="user",
                content=text,
                message_type="user_text",
            )
            try:
                profile_service, meal_service, orchestrator = build_services(config)
                result = orchestrator.handle_meal_text(user_id, text)
                st.session_state["pending_meal"] = result.meal.model_dump()
                st.session_state["pending_raw_text"] = text
                st.success(f"已生成估算，trace_id={result.trace_id}")
            except MissingQwenApiKeyError:
                st.error("未配置 QWEN_API_KEY 或 DASHSCOPE_API_KEY，无法调用 Qwen。")
            except Exception as exc:
                st.error(f"估算失败：{exc}")

        pending = st.session_state.get("pending_meal")
        if pending:
            meal = PendingMealEstimate.model_validate(pending)
            edited = edit_pending_meal(meal)
            if st.button("确认保存"):
                meal_service = MealService(MealRepository(config.db_path))
                meal_service.save_meal_log(user_id, st.session_state.get("pending_raw_text", ""), edited)
                ChatRepository(config.db_path).add_message(
                    user_id=user_id,
                    role="assistant",
                    content=f"已保存：{edited.title}",
                    message_type="assistant_text",
                    metadata=edited.model_dump(),
                )
                st.session_state.pop("pending_meal", None)
                st.session_state.pop("pending_raw_text", None)
                st.success("餐食已保存")
                st.rerun()
