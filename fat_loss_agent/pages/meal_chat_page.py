from __future__ import annotations

import streamlit as st

from fat_loss_agent.config import AppConfig


def render_meal_chat_page(*, config: AppConfig, user_id: str) -> None:
    st.title("饮食记录")
    st.info("饮食记录页面将在下一任务接入 Agent。")
