import streamlit as st

from client_api import get_my_quests, start_encounter, get_encounter, attack_encounter, get_active_character, use_mana_potion
from ui_quests import format_target


def _active_quest_options(quests):
    active_quests = [q for q in quests if q.get("status") == "active"]
    return {f"{q['name']} - {format_target(q)}": q["quest_id"] for q in active_quests}


def render_last_attack_result():
    result = st.session_state.get("last_attack_result")
    if not result:
        return

    if result.get("monster_dead"):
        st.success(result.get("message", "몬스터 처치!"))
    else:
        st.info(result.get("message", "공격 완료"))

    st.write(f"사용 스킬: {result.get('skill_name')}")
    st.write(f"데미지: {result.get('damage')}")
    st.write(f"몬스터 HP: {result.get('monster_current_hp')} / {result.get('monster_max_hp')}")
    st.write(f"퀘스트 상태: {result.get('quest_status')}")

    reward = result.get("reward", {})
    if reward.get("exp", 0) > 0:
        st.write(f"획득 경험치: {reward['exp']}")
    if reward.get("items"):
        items = ", ".join([f"{item['item_name']} x{item['quantity']}" for item in reward["items"]])
        st.write(f"획득 아이템: {items}")

    if reward.get("level_ups"):
        levels = ", ".join([f"Lv.{level}" for level in reward["level_ups"]])
        st.write(f"🎉 레벨업: {levels}")

    if reward.get("learned_skills"):
        skills = ", ".join([
            f"{skill['skill_name']} Lv.{skill['skill_level']}"
            for skill in reward["learned_skills"]
        ])
        st.write(f"🧠 신규 스킬 습득: {skills}")

    if st.button("전투 결과 확인 완료"):
        st.session_state.last_attack_result = None
        st.rerun()


def render_battle_page():
    st.subheader("⚔️ 전투")
    st.caption("슬라임과 고블린 모두 플레이어 스탯/스킬을 사용하는 클릭형 전투 시스템으로 처리됩니다.")

    render_last_attack_result()

    try:
        quest_res = get_my_quests(st.session_state.user_id, st.session_state.cookies)
        if quest_res.status_code != 200:
            st.error(quest_res.json().get("detail", "퀘스트 목록을 불러오지 못했습니다."))
            return

        quests = quest_res.json()
        quest_options = _active_quest_options(quests)

        if not quest_options:
            st.info("전투를 시작할 진행 중 퀘스트가 없습니다.")
            return

        selected_label = st.selectbox("전투를 진행할 퀘스트 선택", list(quest_options.keys()))
        selected_quest_id = quest_options[selected_label]

        col1, col2 = st.columns(2)

        with col1:
            if st.button("전투 시작"):
                start_res = start_encounter(
                    st.session_state.user_id,
                    selected_quest_id,
                    st.session_state.cookies
                )
                if start_res.status_code == 200:
                    st.success("전투가 시작되었습니다.")
                    st.rerun()
                else:
                    st.error(start_res.json().get("detail", "전투 시작 실패"))

        with col2:
            if st.button("전투 상태 새로고침"):
                st.rerun()

        encounter_res = get_encounter(
            st.session_state.user_id,
            selected_quest_id,
            st.session_state.cookies
        )

        if encounter_res.status_code == 404:
            st.info("아직 이 퀘스트의 전투가 시작되지 않았습니다.")
            return

        if encounter_res.status_code != 200:
            st.error(encounter_res.json().get("detail", "전투 상태를 불러오지 못했습니다."))
            return

        encounter = encounter_res.json()

        st.markdown(f"### 몬스터: {encounter['monster_name']}")
        st.write(f"전투 상태: {encounter['status']}")
        st.write(f"턴 수: {encounter['turn_count']}")

        hp_ratio = 0
        if encounter["monster_max_hp"] > 0:
            hp_ratio = encounter["monster_current_hp"] / encounter["monster_max_hp"]
        st.write(f"HP: {encounter['monster_current_hp']} / {encounter['monster_max_hp']}")
        st.progress(hp_ratio)

        render_mana_potion_panel()

        if encounter["status"] != "active":
            st.info("이 전투는 종료되었습니다. 퀘스트/기록 탭에서 결과를 확인하세요.")
            return

        skills = encounter.get("skills", [])
        if not skills:
            st.warning("사용 가능한 스킬이 없습니다.")
            return

        skill_options = {f"{s['skill_name']} Lv.{s['skill_level']}": s["skill_id"] for s in skills}
        selected_skill_label = st.selectbox("사용할 스킬 선택", list(skill_options.keys()))
        selected_skill_id = skill_options[selected_skill_label]

        if st.button("공격하기"):
            attack_res = attack_encounter(
                st.session_state.user_id,
                selected_quest_id,
                selected_skill_id,
                st.session_state.cookies
            )
            if attack_res.status_code == 200:
                st.session_state.last_attack_result = attack_res.json()
                st.rerun()
            else:
                st.error(attack_res.json().get("detail", "공격 실패"))

    except Exception as e:
        st.error(f"서버 오류: {e}")


def get_stat_value(character, stat_type):
    for stat in character.get("stats", []):
        if stat.get("stat_type") == stat_type:
            return stat.get("value", 0)
    return 0

def get_item_quantity(character, item_name):
    total = 0

    for item in character.get("inventory", []):
        if item.get("item_name") == item_name:
            total += item.get("quantity", 0)

    return total


def render_mana_potion_panel():
    st.markdown("#### 🧪 마나 회복")

    detail_res = get_active_character(
        st.session_state.user_id,
        st.session_state.cookies
    )

    if detail_res.status_code != 200:
        st.warning("캐릭터 MP 정보를 불러오지 못했습니다.")
        return

    character = detail_res.json()

    current_mp = get_stat_value(character, "MP")
    max_mp = get_stat_value(character, "MAX_MP")
    potion_count = get_item_quantity(character, "마나 포션")

    st.write(f"현재 MP: {current_mp} / {max_mp}")
    st.write(f"보유 마나 포션: {potion_count}개")

    disabled = potion_count <= 0 or current_mp >= max_mp

    if st.button("마나 포션 사용", disabled=disabled):
        use_res = use_mana_potion(
            st.session_state.user_id,
            st.session_state.cookies
        )

        if use_res.status_code == 200:
            result = use_res.json()
            st.success(result.get("message", "마나 포션을 사용했습니다."))
            st.rerun()
        else:
            st.error(
                use_res.json().get(
                    "detail",
                    "마나 포션 사용 실패"
                )
            )
