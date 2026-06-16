import streamlit as st

from ui_auth import render_login_and_register
from ui_character import render_main_game_page

# 페이지 기본 설정
st.set_page_config(page_title="My RPG Test Client", layout="centered")


# ==========================================
# 1. 세션 상태 (Session State) 초기화
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "cookies" not in st.session_state:
    st.session_state.cookies = None


# ==========================================
# 2. 화면 렌더링
# ==========================================
st.title("🗡️ My RPG 프로젝트 매니저")

if not st.session_state.logged_in:
    render_login_and_register()
else:
    render_main_game_page()
