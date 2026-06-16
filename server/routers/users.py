from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import UserModel, CharacterModel, ActorModel
from schemas import UserCreate, UserResponse, UserDeletionResponse
from auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user.user_identifier).first()

    if db_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 유저 ID입니다.")

    new_user = UserModel(
        id=user.user_identifier,
        user_name=user.nickname,
        password=user.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(user_id=new_user.id, name=new_user.user_name)


@router.get("", response_model=List[UserResponse])
def get_users(skip: int = 2, limit: int = 1, db: Session = Depends(get_db)):
    sql = text("SELECT id, user_name FROM User LIMIT :limit OFFSET :skip")
    users = db.execute(sql, {"skip": skip, "limit": limit}).all()

    return [
        UserResponse(user_id=user.id, name=user.user_name)
        for user in users
    ]


@router.delete("/me", response_model=UserDeletionResponse)
def delete_user(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인하지 않은 사용자는 자신을 삭제할 수 없습니다."
        )

    try:
        user_id = current_user.get("id")
        user = db.query(UserModel).filter(UserModel.id == user_id).first()

        if not user:
            return UserDeletionResponse(user_id="존재하지 않는 사용자입니다.")

        # 해당 유저의 모든 캐릭터 목록 조회
        characters = db.query(CharacterModel).filter(
            CharacterModel.user_id == user_id
        ).all()

        # 자식 테이블(Character) 삭제 후 부모 테이블(Actor) 삭제
        for char in characters:
            actor_id = char.actor_id

            db.delete(char)
            db.flush()

            db.query(ActorModel).filter(
                ActorModel.id == actor_id
            ).delete()

        db.delete(user)
        db.commit()

        return UserDeletionResponse(user_id=user_id)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"유저 삭제 중 오류가 발생하여 롤백되었습니다: {str(e)}"
        )
