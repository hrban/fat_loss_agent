from __future__ import annotations

import streamlit as st

from fat_loss_agent.config import DEFAULT_USER_ID, load_config
from fat_loss_agent.pages.meal_chat_page import render_meal_chat_page
from fat_loss_agent.pages.profile_page import render_profile_page
from fat_loss_agent.repositories.db import init_db


def main() -> None:
    config = load_config()
    init_db(config.db_path)
    st.set_page_config(page_title="个人减脂 Agent", page_icon="🍽️", layout="wide")
    st.sidebar.title("个人减脂 Agent")
    page = st.sidebar.radio("页面", ["饮食记录", "我的档案"])
    if page == "我的档案":
        render_profile_page(config=config, user_id=DEFAULT_USER_ID)
    else:
        render_meal_chat_page(config=config, user_id=DEFAULT_USER_ID)


if __name__ == "__main__":
    main()
