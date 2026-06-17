import streamlit as st
import pandas as pd

from client_api import get_battle_logs


def render_log_page():
    st.subheader("🧾 전투 기록")

    try:
        res = get_battle_logs(st.session_state.user_id, st.session_state.cookies)
        if res.status_code != 200:
            st.error(res.json().get("detail", "전투 기록을 불러오지 못했습니다."))
            return

        logs = res.json()
        if not logs:
            st.info("아직 전투 기록이 없습니다.")
            return

        df = pd.DataFrame([
            {
                "시간": log.get("battle_time"),
                "캐릭터": log.get("character_name"),
                "퀘스트": log.get("quest_name") or "-",
                "몬스터": log.get("monster_name") or "-",
                "결과": "승리" if log.get("result") == "victory" else log.get("result"),
                "획득 EXP": log.get("gained_exp", 0),
                "메시지": log.get("message") or "-",
            }
            for log in logs
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"서버 오류: {e}")
