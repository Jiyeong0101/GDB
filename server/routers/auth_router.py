from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from sqlalchemy.orm import Session

from database import get_db
from models import UserModel
from schemas import UserLogin
from auth import get_current_user, create_session, remove_session

router = APIRouter(tags=["Auth"])


@router.post("/login")
def login(
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user:
        return {
            "message": "이미 로그인한 사용자입니다.",
            "user_id": current_user.get("id")
        }

    user = db.query(UserModel).filter(UserModel.id == login_data.user_id).first()

    if not user or user.password != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 아이디 또는 비밀번호가 다릅니다."
        )

    new_session_id = create_session(user)

    response.set_cookie(
        key="session_id",
        value=new_session_id,
        httponly=True,
        max_age=3600,
        samesite="lax"
    )

    return {"message": f"{user.user_name}님, 로그인 성공"}


@router.post("/logout")
def logout(
    response: Response,
    session_id: str | None = Cookie(default=None)
):
    remove_session(session_id)
    response.delete_cookie(key="session_id")
    return {"message": "로그아웃 성공"}
