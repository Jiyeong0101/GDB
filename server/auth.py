from fastapi import Cookie
import uuid

# 현재 프로젝트에서는 간단한 메모리 기반 세션 저장소를 사용한다.
# 서버를 재시작하면 로그인 세션은 초기화된다.
session_store = {}


def create_session(user):
    new_session_id = str(uuid.uuid4())
    session_store[new_session_id] = {
        "id": user.id,
        "name": user.user_name,
        "characters": []
    }
    return new_session_id


def remove_session(session_id: str | None):
    if session_id and session_id in session_store:
        del session_store[session_id]


def get_current_user(session_id: str | None = Cookie(default=None)):
    if not session_id:
        return None
    return session_store.get(session_id)
