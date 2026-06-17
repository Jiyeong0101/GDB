import streamlit as st
import pandas as pd

from client_api import get_available_quests, get_my_quests


def format_reward(quest):
    parts = []
    if quest.get("reward_exp", 0):
        parts.append(f"EXP {quest['reward_exp']}")
    for item in quest.get("reward_items", []):
        parts.append(f"{item['item_name']} x{item['quantity']}")
    return ", ".join(parts) if parts else "-"


def format_target(quest):
    target = quest.get("target")
    if not target:
        return "-"
    return f"{target['monster_name']} {target['required_count']}마리"


def format_status(status):
    if status == "active":
        return "진행 중"
    if status == "completed":
        return "완료"
    if status == "failed":
        return "실패"
    return status or "-"


def format_source(source):
    if source == "system":
        return "자동 지급"
    if source == "npc":
        return "NPC 수락"
    return source or "-"


def format_progress(quest):
    target = quest.get("target") or {}
    required_count = target.get("required_count", quest.get("max_steps", 1))
    current_step = quest.get("current_step", 0)
    return f"{current_step} / {required_count}"


def render_my_quests():
    st.subheader("📜 내 퀘스트")

    try:
        res = get_my_quests(st.session_state.user_id, st.session_state.cookies)
        if res.status_code != 200:
            st.error(res.json().get("detail", "내 퀘스트 목록을 불러오지 못했습니다."))
            return

        quests = res.json()
        if not quests:
            st.info("아직 수락하거나 지급받은 퀘스트가 없습니다.")
            return

        df = pd.DataFrame([
            {
                "퀘스트ID": q["quest_id"],
                "퀘스트명": q["name"],
                "획득 방식": format_source(q.get("source")),
                "상태": format_status(q.get("status")),
                "진행도": format_progress(q),
                "목표": format_target(q),
                "보상": format_reward(q),
            }
            for q in quests
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        active_quests = [q for q in quests if q.get("status") == "active"]
        if active_quests:
            st.markdown("#### 진행 중인 퀘스트")
            for q in active_quests:
                target = q.get("target") or {}
                required_count = target.get("required_count", q.get("max_steps", 1))
                current_step = q.get("current_step", 0)
                progress_value = current_step / required_count if required_count else 0
                st.write(f"{q['name']} — {current_step}/{required_count}")
                st.progress(progress_value)

    except Exception as e:
        st.error(f"서버 오류: {e}")


def render_system_available_quests():
    st.divider()
    st.subheader("📌 자동/시스템 제공 퀘스트")
    st.caption("NPC가 제공하지 않는 시스템 퀘스트만 표시됩니다. 첫 전투 훈련은 새 캐릭터 생성 시 자동 지급됩니다.")

    try:
        res = get_available_quests(st.session_state.user_id, st.session_state.cookies)
        if res.status_code != 200:
            st.error(res.json().get("detail", "퀘스트 목록을 불러오지 못했습니다."))
            return

        quests = res.json()
        if not quests:
            st.info("현재 새로 받을 수 있는 시스템 퀘스트가 없습니다.")
            return

        df = pd.DataFrame([
            {
                "퀘스트ID": q["quest_id"],
                "퀘스트명": q["name"],
                "목표": format_target(q),
                "보상": format_reward(q),
            }
            for q in quests
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"서버 오류: {e}")


def render_quest_page():
    render_my_quests()
    render_system_available_quests()
