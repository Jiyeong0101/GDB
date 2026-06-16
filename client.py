import streamlit as st
import requests
import pandas as pd

# FastAPI 서버 주소
BASE_URL = "http://localhost:8000"

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
# 2. 로그아웃 처리 함수
# ==========================================
def perform_logout():
    try:
        requests.post(f"{BASE_URL}/logout", cookies=st.session_state.cookies)
    except Exception as e:
        pass
    
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.cookies = None

# ==========================================
# 3. 화면 렌더링
# ==========================================
st.title("🗡️ My RPG 프로젝트 매니저")

# ------------------------------------------
# 상황 A: 로그인하지 않은 상태 (로그인 / 회원가입 탭)
# ------------------------------------------
if not st.session_state.logged_in:
    tab_login, tab_register = st.tabs(["🔐 로그인", "📝 새 계정 생성"])
    
    # --- [로그인 탭] ---
    with tab_login:
        st.subheader("기존 계정으로 로그인")
        with st.form("login_form"):
            input_id = st.text_input("계정 ID", max_chars=20)
            input_pw = st.text_input("비밀번호", type="password")
            submit_login = st.form_submit_button("로그인하기")
            
            if submit_login:
                if not input_id or not input_pw:
                    st.warning("ID와 비밀번호를 모두 입력해주세요.")
                else:
                    try:
                        # [교정] data= 대신 json= 을 사용하고, 키값을 user_id로 변경
                        response = requests.post(
                            f"{BASE_URL}/login", 
                            json={"user_id": input_id, "password": input_pw}
                        )
                        
                        if response.status_code == 200:
                            # 로그인 성공 메시지 혹은 이미 로그인된 메시지 처리
                            res_json = response.json()
                            st.session_state.logged_in = True
                            
                            # 이미 로그인된 상태일 경우 서버 응답 구조 분기 대응
                            if "user_id" in res_json:
                                st.session_state.user_id = res_json["user_id"]
                            else:
                                st.session_state.user_id = input_id
                                
                            st.session_state.cookies = response.cookies.get_dict()
                            st.success(f"🎉 로그인 성공!")
                            st.rerun()
                        else:
                            detail = response.json().get("detail", "로그인 실패")
                            st.error(f"❌ 로그인 실패: {detail}")
                    except Exception as e:
                        st.error(f"서버 연결 오류: {e}")

    # --- [회원가입 탭] ---
    with tab_register:
        st.subheader("RPG 월드에 처음 오셨나요?")
        with st.form("register_form", clear_on_submit=True):
            reg_id = st.text_input("희망하는 계정 ID", max_chars=20)
            reg_name = st.text_input("사용자 이름 (닉네임)", max_chars=100)
            reg_pw = st.text_input("비밀번호", type="password")
            submit_register = st.form_submit_button("계정 생성하기")
            
            if submit_register:
                if not reg_id or not reg_name or not reg_pw:
                    st.warning("모든 필드를 채워주세요.")
                else:
                    try:
                        # [교정] main.py의 UserCreate 스키마(user_identifier, nickname)와 완벽 연동
                        reg_response = requests.post(
                            f"{BASE_URL}/users",
                            json={
                                "user_identifier": reg_id, 
                                "nickname": reg_name, 
                                "password": reg_pw
                            }
                        )
                        
                        if reg_response.status_code in [200, 201]:
                            st.success("✨ 계정이 성공적으로 생성되었습니다! [로그인] 탭으로 이동해 주세요.")
                        else:
                            detail = reg_response.json().get("detail", "회원가입 실패")
                            st.error(f"❌ 생성 실패: {detail}")
                    except Exception as e:
                        st.error(f"서버 연결 오류: {e}")

# ------------------------------------------
# 상황 B: 로그인 성공 상태 (메인 게임 기능 표시)
# ------------------------------------------
else:
    st.sidebar.title("🎮 플레이어 정보")
    st.sidebar.info(f"현재 접속 계정: **{st.session_state.user_id}**")
    
    if st.sidebar.button("🔓 로그아웃", use_container_width=True):
        perform_logout()
        st.success("로그아웃 되었습니다.")
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚠️ 위험 구역")
    
    confirm_delete = st.sidebar.checkbox("정말로 계정을 삭제하시겠습니까?")
    if st.sidebar.button("❌ 계정 탈퇴 (데이터 영구 삭제)", disabled=not confirm_delete, use_container_width=True):
        try:
            # main.py의 유저 삭제 경로는 @app.delete("/users/me") 입니다.
            delete_res = requests.delete(
                f"{BASE_URL}/users/me",
                cookies=st.session_state.cookies
            )
            
            if delete_res.status_code == 200:
                st.sidebar.success("계정이 완전히 삭제되었습니다.")
                perform_logout()
                st.rerun()
            else:
                detail = delete_res.json().get("detail", "삭제 권한이 없거나 실패했습니다.")
                st.sidebar.error(f"탈퇴 실패: {detail}")
        except Exception as e:
            st.sidebar.error(f"서버 연결 오류: {e}")

    # --- 메인 캐릭터 목록 테이블 ---
    st.subheader("👤 내 캐릭터 목록")
    try:
        char_res = requests.get(
            f"{BASE_URL}/users/{st.session_state.user_id}/characters",
            cookies=st.session_state.cookies
        )
    except Exception as e:
        st.error(f"서버 연결 오류: {e}")
        char_res = None

    if char_res and char_res.status_code == 200:
        characters = char_res.json()
        if characters:
            df = pd.DataFrame(characters)
            df = df[['character_name', 'level', 'exp', 'active']]
            df.columns = ['캐릭터명', '레벨', '경험치', '활성화 여부']
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.subheader("🎯 캐릭터 선택")
            if characters:
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
                            res = requests.patch(
                                f"{BASE_URL}/users/{st.session_state.user_id}/characters/{selected_id}/activate",
                                cookies=st.session_state.cookies
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
                    confirm_char_delete = st.checkbox("삭제 확인", key=f"delete_check_{selected_id}")

                    if st.button("캐릭터 삭제", disabled=not confirm_char_delete):
                        try:
                            delete_res = requests.delete(
                                f"{BASE_URL}/users/{st.session_state.user_id}/characters/{selected_id}",
                                cookies=st.session_state.cookies
                            )

                            if delete_res.status_code == 200:
                                deleted = delete_res.json()
                                st.success(f"🗑️ '{deleted['character_name']}' 캐릭터가 삭제되었습니다.")
                                st.rerun()
                            else:
                                st.error(delete_res.json().get("detail", "캐릭터 삭제 실패"))
                        except Exception as e:
                            st.error(f"서버 오류: {e}")

                st.divider()
                st.subheader("🧬 활성 캐릭터 상세 정보")

                try:
                    detail_res = requests.get(
                        f"{BASE_URL}/users/{st.session_state.user_id}/active-character",
                        cookies=st.session_state.cookies
                    )

                    if detail_res.status_code == 200:
                        char = detail_res.json()

                        if char:
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
                            st.info("아직 활성화된 캐릭터가 없습니다. 대표 캐릭터를 활성화하세요.")

                    else:
                        detail = detail_res.json().get("detail", "캐릭터 상세 정보를 불러오지 못했습니다.")
                        st.error(detail)

                except Exception as e:
                    st.error(f"서버 오류: {e}")
            
        else:
            st.info("아직 생성된 캐릭터가 없습니다. 아래에서 새 캐릭터를 만들어보세요!")
    else:
        st.error("캐릭터 목록을 불러오지 못했습니다.")

    st.divider()

    # --- 새 캐릭터 생성 ---
    st.subheader("✨ 새 캐릭터 생성")
    with st.form("create_character_form", clear_on_submit=True):
        new_char_name = st.text_input("캐릭터 이름")
        
        # [추가됨] 종족 선택 셀렉트박스
        selected_race = st.selectbox("종족 선택", ["HUMAN", "ELF", "ORC"])
        
        create_button = st.form_submit_button("생성하기")
        
        if create_button:
            if not new_char_name:
                st.warning("캐릭터 이름을 입력해주세요.")
            else:
                try:
                    # [수정됨] json 페이로드에 race 필드 추가
                    create_res = requests.post(
                        f"{BASE_URL}/users/{st.session_state.user_id}/characters",
                        json={
                            "character_name": new_char_name,
                            "race": selected_race
                        },
                        cookies=st.session_state.cookies
                    )
                    
                    if create_res.status_code in [200, 201]:
                        # 성공 시 피드백 메시지 강화
                        st.success(f"⚔️ {selected_race} 종족의 '{new_char_name}' 캐릭터가 생성되었습니다! (초보자 직업 자동 부여)")
                        st.rerun()
                    else:
                        detail = create_res.json().get("detail", "생성 실패")
                        st.error(f"생성 실패: {detail}")
                except Exception as e:
                    st.error(f"서버 연결 오류: {e}")