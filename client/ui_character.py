import streamlit as st
import pandas as pd
from ui_scenario import render_quest_scenario

from client_api import (
    logout,
    delete_current_user,
    get_characters,
    activate_character,
    delete_character,
    get_active_character,
    create_character,
)


def perform_logout():
    try:
        logout(st.session_state.cookies)
    except Exception:
        pass

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.cookies = None


def render_sidebar():
    st.sidebar.title("🎮 플레이어 정보")
    st.sidebar.info(f"현재 접속 계정: **{st.session_state.user_id}**")

    if st.sidebar.button("🔓 로그아웃", use_container_width=True):
        perform_logout()
        st.success("로그아웃 되었습니다.")
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚠️ 위험 구역")

    confirm_delete = st.sidebar.checkbox("정말로 계정을 삭제하시겠습니까?")

    if st.sidebar.button(
        "❌ 계정 탈퇴 (데이터 영구 삭제)",
        disabled=not confirm_delete,
        use_container_width=True
    ):
        try:
            delete_res = delete_current_user(st.session_state.cookies)

            if delete_res.status_code == 200:
                st.sidebar.success("계정이 완전히 삭제되었습니다.")
                perform_logout()
                st.rerun()
            else:
                detail = delete_res.json().get("detail", "삭제 권한이 없거나 실패했습니다.")
                st.sidebar.error(f"탈퇴 실패: {detail}")

        except Exception as e:
            st.sidebar.error(f"서버 연결 오류: {e}")


def render_active_character_detail():
    st.divider()
    st.subheader("🧬 활성 캐릭터 상세 정보")

    try:
        detail_res = get_active_character(
            st.session_state.user_id,
            st.session_state.cookies
        )

        if detail_res.status_code == 200:
            char = detail_res.json()

            if not char:
                st.info("아직 활성화된 캐릭터가 없습니다. 대표 캐릭터를 활성화하세요.")
                return

            st.markdown(f"### 🧝 {char['character_name']}")

            basic_info = pd.DataFrame([
                {
                    "종족": char.get("race") or "-",
                    "직업": char.get("job_name") or char.get("job") or "-",
                    "레벨": char.get("level", 0),
                    "경험치": char.get("exp", 0)
                }
            ])

            st.dataframe(
                basic_info,
                use_container_width=True,
                hide_index=True
            )

            # -----------------------------
            # 스탯 표시
            # -----------------------------
            st.markdown("#### 📊 스탯")

            stats = char.get("stats", [])
            if stats:
                stat_df = pd.DataFrame(stats)
                stat_df = stat_df[["stat_type", "stat_name", "value", "description"]]
                stat_df.columns = ["스탯 코드", "스탯 이름", "수치", "설명"]
                st.dataframe(stat_df, use_container_width=True, hide_index=True)
            else:
                st.info("등록된 스탯이 없습니다.")

            # -----------------------------
            # 스킬 표시
            # -----------------------------
            st.markdown("#### 🧠 스킬")

            skills = char.get("skills", [])
            if skills:
                skill_df = pd.DataFrame(skills)
                skill_df = skill_df[[
                    "skill_name",
                    "skill_level",
                    "mp_cost",
                    "cooldown_sec",
                    "description"
                ]]
                skill_df.columns = ["스킬명", "스킬 레벨", "MP 소모", "쿨타임", "설명"]
                st.dataframe(skill_df, use_container_width=True, hide_index=True)
            else:
                st.info("습득한 스킬이 없습니다.")

            # -----------------------------
            # 인벤토리 표시
            # -----------------------------
            st.markdown("#### 🎒 인벤토리")

            inventory = char.get("inventory", [])
            if inventory:
                inventory_df = pd.DataFrame(inventory)
                inventory_df = inventory_df[[
                    "inventory_type",
                    "item_name",
                    "item_type",
                    "item_sub_type",
                    "quantity",
                    "capacity"
                ]]
                inventory_df.columns = [
                    "가방 종류",
                    "아이템명",
                    "아이템 타입",
                    "세부 타입",
                    "수량",
                    "가방 용량"
                ]
                st.dataframe(inventory_df, use_container_width=True, hide_index=True)
            else:
                st.info("인벤토리에 아이템이 없습니다.")

        else:
            detail = detail_res.json().get("detail", "캐릭터 상세 정보를 불러오지 못했습니다.")
            st.error(detail)

    except Exception as e:
        st.error(f"서버 오류: {e}")


def render_character_list():
    st.subheader("👤 내 캐릭터 목록")

    try:
        char_res = get_characters(
            st.session_state.user_id,
            st.session_state.cookies
        )
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        return

    if not char_res or char_res.status_code != 200:
        st.error("캐릭터 목록을 불러오지 못했습니다.")
        return

    characters = char_res.json()

    if not characters:
        st.info("아직 생성된 캐릭터가 없습니다. 아래에서 새 캐릭터를 만들어보세요!")
        return

    df = pd.DataFrame(characters)
    df = df[["character_name", "level", "exp", "active"]]
    df.columns = ["캐릭터명", "레벨", "경험치", "활성화 여부"]
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.subheader("🎯 캐릭터 선택")

    char_options = {
        f"{c['character_name']} (Lv.{c['level']})": c["actor_id"]
        for c in characters
    }

    selected_label = st.selectbox("플레이할 캐릭터 선택", list(char_options.keys()))
    selected_id = char_options[selected_label]

    col1, col2 = st.columns(2)

    # 활성화 API 호출
    with col1:
        if st.button("대표 캐릭터로 활성화"):
            try:
                res = activate_character(
                    st.session_state.user_id,
                    selected_id,
                    st.session_state.cookies
                )

                if res.status_code == 200:
                    st.success("✅ 대표 캐릭터로 활성화되었습니다!")
                    st.rerun()
                else:
                    st.error(res.json().get("detail", "활성화 실패"))

            except Exception as e:
                st.error(f"서버 오류: {e}")

    # 캐릭터 삭제 API 호출
    with col2:
        confirm_char_delete = st.checkbox(
            "삭제 확인",
            key=f"delete_check_{selected_id}"
        )

        if st.button("캐릭터 삭제", disabled=not confirm_char_delete):
            try:
                delete_res = delete_character(
                    st.session_state.user_id,
                    selected_id,
                    st.session_state.cookies
                )

                if delete_res.status_code == 200:
                    deleted = delete_res.json()
                    st.success(f"🗑️ '{deleted['character_name']}' 캐릭터가 삭제되었습니다.")
                    st.rerun()
                else:
                    st.error(delete_res.json().get("detail", "캐릭터 삭제 실패"))

            except Exception as e:
                st.error(f"서버 오류: {e}")

    render_active_character_detail()


def render_create_character_form():
    st.divider()
    st.subheader("✨ 새 캐릭터 생성")

    with st.form("create_character_form", clear_on_submit=True):
        new_char_name = st.text_input("캐릭터 이름")
        selected_race = st.selectbox("종족 선택", ["HUMAN", "ELF", "ORC"])

        create_button = st.form_submit_button("생성하기")

        if create_button:
            if not new_char_name:
                st.warning("캐릭터 이름을 입력해주세요.")
                return

            try:
                create_res = create_character(
                    st.session_state.user_id,
                    new_char_name,
                    selected_race,
                    st.session_state.cookies
                )

                if create_res.status_code in [200, 201]:
                    st.success(
                        f"⚔️ {selected_race} 종족의 '{new_char_name}' 캐릭터가 생성되었습니다! "
                        "(초보자 직업 자동 부여)"
                    )
                    st.rerun()
                else:
                    detail = create_res.json().get("detail", "생성 실패")
                    st.error(f"생성 실패: {detail}")

            except Exception as e:
                st.error(f"서버 연결 오류: {e}")
                

def render_main_game_page():
    render_sidebar()
    render_character_list()
    render_quest_scenario()
    render_create_character_form()
