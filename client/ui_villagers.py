import streamlit as st
import pandas as pd

from client_api import get_villagers, get_villager_quests, accept_quest
from ui_quests import format_target, format_reward


def render_villager_page():
    st.subheader("🧑‍🌾 마을 NPC")

    try:
        res = get_villagers(st.session_state.user_id, st.session_state.cookies)
        if res.status_code != 200:
            st.error(res.json().get("detail", "NPC 목록을 불러오지 못했습니다."))
            return

        villagers = res.json()
        if not villagers:
            st.info("등록된 마을 NPC가 없습니다. populate_project_scenario.sql 실행 여부를 확인하세요.")
            return

        npc_df = pd.DataFrame([
            {
                "NPC ID": v["villager_id"],
                "이름": v["name"],
                "역할": v["role"],
                "설명": v.get("description") or "-",
            }
            for v in villagers
        ])
        st.dataframe(npc_df, use_container_width=True, hide_index=True)

        villager_options = {f"{v['name']} ({v['role']})": v["villager_id"] for v in villagers}
        selected_label = st.selectbox("대화할 NPC 선택", list(villager_options.keys()))
        selected_villager_id = villager_options[selected_label]

        st.markdown("#### 📜 NPC 제공 퀘스트")
        quest_res = get_villager_quests(
            st.session_state.user_id,
            selected_villager_id,
            st.session_state.cookies
        )

        if quest_res.status_code != 200:
            st.error(quest_res.json().get("detail", "NPC 퀘스트를 불러오지 못했습니다."))
            return

        quests = quest_res.json()
        if not quests:
            st.info("이 NPC에게서 새로 받을 수 있는 퀘스트가 없습니다.")
            return

        quest_df = pd.DataFrame([
            {
                "퀘스트ID": q["quest_id"],
                "퀘스트명": q["name"],
                "목표": format_target(q),
                "보상": format_reward(q),
                "설명": q.get("description") or "-",
            }
            for q in quests
        ])
        st.dataframe(quest_df, use_container_width=True, hide_index=True)

        quest_options = {f"{q['name']} - {format_target(q)}": q["quest_id"] for q in quests}
        selected_quest_label = st.selectbox("수락할 NPC 퀘스트 선택", list(quest_options.keys()))
        selected_quest_id = quest_options[selected_quest_label]

        if st.button("퀘스트 수락"):
            accept_res = accept_quest(st.session_state.user_id, selected_quest_id, st.session_state.cookies)
            if accept_res.status_code == 200:
                st.success("✅ NPC 퀘스트를 수락했습니다. 전투 탭에서 전투를 시작하세요.")
                st.rerun()
            else:
                st.error(accept_res.json().get("detail", "퀘스트 수락 실패"))

    except Exception as e:
        st.error(f"서버 오류: {e}")
