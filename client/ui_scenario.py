import streamlit as st
import pandas as pd

from client_api import (
    get_available_quests,
    get_my_quests,
    accept_quest,
    run_quest_battle,
)


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


def render_available_quests():
    st.markdown("#### 📜 받을 수 있는 퀘스트")

    try:
        res = get_available_quests(
            st.session_state.user_id,
            st.session_state.cookies
        )

        if res.status_code != 200:
            st.error(res.json().get("detail", "퀘스트 목록을 불러오지 못했습니다."))
            return

        quests = res.json()

        if not quests:
            st.info("현재 받을 수 있는 퀘스트가 없습니다.")
            return

        df = pd.DataFrame([
            {
                "퀘스트ID": q["quest_id"],
                "퀘스트명": q["name"],
                "타입": q.get("type") or "-",
                "목표": format_target(q),
                "보상": format_reward(q),
            }
            for q in quests
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        quest_options = {
            f"{q['name']} - {format_target(q)}": q["quest_id"]
            for q in quests
        }

        selected_label = st.selectbox(
            "수락할 퀘스트 선택",
            list(quest_options.keys()),
            key="available_quest_select"
        )
        selected_quest_id = quest_options[selected_label]

        if st.button("퀘스트 수락", key="accept_quest_button"):
            accept_res = accept_quest(
                st.session_state.user_id,
                selected_quest_id,
                st.session_state.cookies
            )

            if accept_res.status_code == 200:
                st.success("✅ 퀘스트를 수락했습니다.")
                st.rerun()
            else:
                st.error(accept_res.json().get("detail", "퀘스트 수락 실패"))

    except Exception as e:
        st.error(f"서버 오류: {e}")


def render_my_quests():
    st.markdown("#### 🧭 진행 중 / 완료한 퀘스트")

    try:
        res = get_my_quests(
            st.session_state.user_id,
            st.session_state.cookies
        )

        if res.status_code != 200:
            st.error(res.json().get("detail", "내 퀘스트 목록을 불러오지 못했습니다."))
            return

        quests = res.json()

        if not quests:
            st.info("아직 수락한 퀘스트가 없습니다.")
            return

        df = pd.DataFrame([
            {
                "퀘스트ID": q["quest_id"],
                "퀘스트명": q["name"],
                "상태": q.get("status") or "-",
                "진행도": f"{q.get('current_step', 0)} / {q.get('target', {}).get('required_count', q.get('max_steps', 1))}",
                "목표": format_target(q),
                "보상": format_reward(q),
            }
            for q in quests
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        active_quests = [q for q in quests if q.get("status") == "active"]

        if not active_quests:
            st.info("현재 전투를 진행할 활성 퀘스트가 없습니다.")
            return

        quest_options = {
            f"{q['name']} - {format_target(q)}": q["quest_id"]
            for q in active_quests
        }

        selected_label = st.selectbox(
            "전투를 진행할 퀘스트 선택",
            list(quest_options.keys()),
            key="battle_quest_select"
        )
        selected_quest_id = quest_options[selected_label]

        if st.button("⚔️ 전투 실행", key="battle_button"):
            battle_res = run_quest_battle(
                st.session_state.user_id,
                selected_quest_id,
                st.session_state.cookies
            )

            if battle_res.status_code == 200:
                result = battle_res.json()
                st.success(result.get("message", "전투 완료"))
                st.write(f"처치 몬스터: {result['monster_name']}")
                st.write(f"진행도: {result['current_step']} / {result['required_count']}")
                st.write(f"퀘스트 상태: {result['quest_status']}")

                reward = result.get("reward", {})
                if reward.get("exp", 0) > 0:
                    st.write(f"획득 경험치: {reward['exp']}")

                items = reward.get("items", [])
                if items:
                    item_text = ", ".join([
                        f"{item['item_name']} x{item['quantity']}"
                        for item in items
                    ])
                    st.write(f"획득 아이템: {item_text}")

                st.info("활성 캐릭터 상세 정보에서 경험치와 인벤토리 반영 결과를 확인할 수 있습니다.")
                st.rerun()
            else:
                st.error(battle_res.json().get("detail", "전투 실행 실패"))

    except Exception as e:
        st.error(f"서버 오류: {e}")


def render_quest_scenario():
    st.divider()
    st.subheader("🗺️ 퀘스트 / 전투 시나리오")

    render_available_quests()
    render_my_quests()
