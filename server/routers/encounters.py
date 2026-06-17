from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from schemas import EncounterResponse, AttackRequest, AttackResponse
from services.quest_service import get_active_character_or_none
from services.battle_service import (
    start_encounter,
    build_encounter_response,
    get_active_or_latest_encounter,
    attack_encounter,
)

router = APIRouter(prefix="/users/{user_id}/quests/{quest_id}/encounter", tags=["Encounters"])


def check_user_permission(user_id: str, current_user):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인 후 이용할 수 있습니다.")
    if current_user.get("id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="다른 사용자의 전투 정보는 접근할 수 없습니다.")


@router.post("/start", response_model=EncounterResponse)
def start_quest_encounter(
    user_id: str,
    quest_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    encounter = start_encounter(db, character, quest_id)
    db.commit()
    db.refresh(encounter)

    return build_encounter_response(db, encounter)


@router.get("", response_model=EncounterResponse)
def get_quest_encounter(
    user_id: str,
    quest_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    encounter = get_active_or_latest_encounter(db, character.actor_id, quest_id)
    if not encounter:
        raise HTTPException(status_code=404, detail="해당 퀘스트의 전투가 아직 시작되지 않았습니다.")

    return build_encounter_response(db, encounter)


@router.post("/attack", response_model=AttackResponse)
def attack_quest_encounter(
    user_id: str,
    quest_id: int,
    attack: AttackRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    result = attack_encounter(
        db=db,
        character=character,
        quest_id=quest_id,
        skill_id=attack.skill_id
    )
    db.commit()

    return result
