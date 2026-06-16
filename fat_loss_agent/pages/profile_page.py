from __future__ import annotations

import streamlit as st

from fat_loss_agent.config import AppConfig
from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.services.profile_service import ProfileService


SEX_OPTIONS = {"男": "male", "女": "female"}
ACTIVITY_OPTIONS = {
    "久坐": "sedentary",
    "轻度活动": "light",
    "中等活动": "moderate",
    "高活动": "active",
}
SPEED_OPTIONS = {"保守": "conservative", "标准": "standard", "激进": "aggressive"}


def render_profile_page(*, config: AppConfig, user_id: str) -> None:
    service = ProfileService(ProfileRepository(config.db_path))
    existing = service.get_profile(user_id) or {}

    st.title("我的档案")
    with st.form("profile_form"):
        nickname = st.text_input("昵称", value=existing.get("nickname", ""))
        sex_label = st.selectbox("性别", list(SEX_OPTIONS.keys()), index=0 if existing.get("sex") != "female" else 1)
        age = st.number_input("年龄", min_value=10, max_value=100, value=int(existing.get("age", 30)))
        height_cm = st.number_input(
            "身高 cm",
            min_value=100.0,
            max_value=230.0,
            value=float(existing.get("height_cm", 175.0)),
        )
        current_weight_kg = st.number_input(
            "当前体重 kg",
            min_value=30.0,
            max_value=250.0,
            value=float(existing.get("current_weight_kg", 80.0)),
        )
        target_weight_kg = st.number_input(
            "目标体重 kg",
            min_value=30.0,
            max_value=250.0,
            value=float(existing.get("target_weight_kg", 72.0)),
        )
        activity_label = st.selectbox("活动水平", list(ACTIVITY_OPTIONS.keys()))
        speed_label = st.selectbox("减脂速度", list(SPEED_OPTIONS.keys()), index=1)
        diet_preferences = st.text_area("饮食偏好或忌口", value=existing.get("diet_preferences", ""))
        submitted = st.form_submit_button("保存档案")

    if submitted:
        saved = service.save_profile(
            user_id=user_id,
            nickname=nickname or "本地用户",
            sex=SEX_OPTIONS[sex_label],
            age=int(age),
            height_cm=float(height_cm),
            current_weight_kg=float(current_weight_kg),
            target_weight_kg=float(target_weight_kg),
            activity_level=ACTIVITY_OPTIONS[activity_label],
            fat_loss_speed=SPEED_OPTIONS[speed_label],
            diet_preferences=diet_preferences,
        )
        st.success("档案已保存")
        st.metric("每日热量目标", f"{int(saved['daily_calorie_target'])} kcal")
        st.metric("每日蛋白质目标", f"{int(saved['daily_protein_target_g'])} g")
        st.info(saved["goal_explanation"])
