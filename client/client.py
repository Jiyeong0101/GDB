import streamlit as st

from ui_auth import render_login_and_register
from ui_character import render_sidebar, render_character_page
from ui_quests import render_quest_page
from ui_villagers import render_villager_page
from ui_battle import render_battle_page
from ui_logs import render_log_page

st.set_page_config(page_title="My RPG Test Client", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "cookies" not in st.session_state:
    st.session_state.cookies = None
if "last_attack_result" not in st.session_state:
    st.session_state.last_attack_result = None

st.title("🗡️ My RPG 프로젝트 매니저")

if not st.session_state.logged_in:
    render_login_and_register()
else:
    render_sidebar()

    page = st.sidebar.radio(
        "메뉴",
        [
            "👤 캐릭터",
            "📜 내 퀘스트",
            "🧑‍🌾 마을 NPC",
            "⚔️ 전투",
            "🧾 기록"
        ]
    )

    if page == "👤 캐릭터":
        render_character_page()

    elif page == "📜 내 퀘스트":
        render_quest_page()

    elif page == "🧑‍🌾 마을 NPC":
        render_villager_page()

    elif page == "⚔️ 전투":
        render_battle_page()

    elif page == "🧾 기록":
        render_log_page()
