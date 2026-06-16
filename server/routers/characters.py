from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import get_current_user
from models import (
    UserModel,
    ActorModel,
    CharacterModel,
    SpecimenModel,
    CharacterSpecimenModel,
    JobModel,
    CharacterJobModel,
)
from schemas import (
    CharacterCreate,
    CharacterResponse,
    CharacterDeletionResponse,
)
from services.character_service import initialize_character_defaults

router = APIRouter(prefix="/users/{user_id}/characters", tags=["Characters"])


@router.post("", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED)
def create_character(
    user_id: str,
    char_data: CharacterCreate,
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    try:
        # 1. Actor 생성
        new_actor = ActorModel()
        db.add(new_actor)
        db.flush()

        # 2. Character 생성
        new_character = CharacterModel(
            actor_id=new_actor.id,
            user_id=user_id,
            character_name=char_data.character_name
        )
        db.add(new_character)
        db.flush()

        # 3. 종족 선택 처리
        specimen = db.query(SpecimenModel).filter(
            SpecimenModel.type == char_data.race
        ).first()

        if not specimen:
            raise HTTPException(status_code=400, detail="존재하지 않는 종족입니다.")

        char_specimen = CharacterSpecimenModel(
            char_id=new_actor.id,
            type=specimen.type,
            fraction=1.0
        )
        db.add(char_specimen)

        # 4. 초보자 직업 자동 부여
        beginner_job = db.query(JobModel).filter(
            JobModel.type == "NOVICE"
        ).first()

        if not beginner_job:
            raise HTTPException(status_code=500, detail="기본 직업이 존재하지 않습니다.")

        char_job = CharacterJobModel(
            char_id=new_actor.id,
            type=beginner_job.type,
            active=True
        )
        db.add(char_job)

        # 5. 기본 스탯 / 인벤토리 / 아이템 / 스킬 자동 생성
        initialize_character_defaults(
            db=db,
            actor_id=new_actor.id,
            race=specimen.type
        )

        db.commit()
        db.refresh(new_character)

        return new_character

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 생성 실패: {str(e)}"
        )


@router.get("", response_model=List[CharacterResponse])
def get_user_characters(
    user_id: str,
    db: Session = Depends(get_db)
):
    characters = db.query(CharacterModel).filter(
        CharacterModel.user_id == user_id
    ).all()

    return characters


@router.patch("/{actor_id}/activate")
def activate_character(
    user_id: str,
    actor_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 후 캐릭터를 활성화할 수 있습니다."
        )

    # 2. 본인 계정 확인
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 캐릭터는 활성화할 수 없습니다."
        )

    # 3. 활성화할 캐릭터가 실제로 존재하는지 확인
    character = db.query(CharacterModel).filter(
        CharacterModel.actor_id == actor_id,
        CharacterModel.user_id == user_id
    ).first()

    if not character:
        raise HTTPException(
            status_code=404,
            detail="활성화할 캐릭터를 찾을 수 없습니다."
        )

    try:
        # 4. 해당 유저의 모든 캐릭터 비활성화
        db.query(CharacterModel).filter(
            CharacterModel.user_id == user_id
        ).update({"active": False})

        # 5. 선택한 캐릭터만 활성화
        character.active = True
        db.commit()

        return {
            "message": "대표 캐릭터로 활성화되었습니다.",
            "actor_id": character.actor_id,
            "character_name": character.character_name
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 활성화 중 오류가 발생하여 롤백되었습니다: {str(e)}"
        )


@router.delete("/{actor_id}", response_model=CharacterDeletionResponse)
def delete_character(
    user_id: str,
    actor_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인하지 않은 사용자는 캐릭터를 삭제할 수 없습니다."
        )

    # 2. 본인 계정인지 확인
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 캐릭터는 삭제할 수 없습니다."
        )

    # 3. 삭제할 캐릭터 조회
    character = db.query(CharacterModel).filter(
        CharacterModel.actor_id == actor_id,
        CharacterModel.user_id == user_id
    ).first()

    if not character:
        raise HTTPException(
            status_code=404,
            detail="삭제할 캐릭터를 찾을 수 없습니다."
        )

    deleted_name = character.character_name

    try:
        db.delete(character)
        db.flush()

        db.query(ActorModel).filter(
            ActorModel.id == actor_id
        ).delete()

        db.commit()

        return CharacterDeletionResponse(
            actor_id=actor_id,
            character_name=deleted_name,
            message="캐릭터 삭제 완료"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 삭제 중 오류가 발생하여 롤백되었습니다: {str(e)}"
        )
