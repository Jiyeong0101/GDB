import streamlit as st
from client_api import login, create_user


def render_login_and_register():
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
                    return

                try:
                    response = login(input_id, input_pw)

                    if response.status_code == 200:
                        res_json = response.json()
                        st.session_state.logged_in = True

                        if "user_id" in res_json:
                            st.session_state.user_id = res_json["user_id"]
                        else:
                            st.session_state.user_id = input_id

                        st.session_state.cookies = response.cookies.get_dict()
                        st.success("🎉 로그인 성공!")
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
                    return

                try:
                    reg_response = create_user(reg_id, reg_name, reg_pw)

                    if reg_response.status_code in [200, 201]:
                        st.success("✨ 계정이 성공적으로 생성되었습니다! [로그인] 탭으로 이동해 주세요.")
                    else:
                        detail = reg_response.json().get("detail", "회원가입 실패")
                        st.error(f"❌ 생성 실패: {detail}")

                except Exception as e:
                    st.error(f"서버 연결 오류: {e}")
