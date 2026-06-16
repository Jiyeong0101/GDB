from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import CharacterQuestModel, QuestModel
from schemas import QuestAcceptResponse, BattleResponse
from services.quest_service import (
    get_active_character_or_none,
    get_quest_target,
    get_quest_reward_summary,
    give_quest_reward,
)

router = APIRouter(prefix="/users/{user_id}/quests", tags=["Quests"])


def check_user_permission(user_id: str, current_user):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 후 이용할 수 있습니다."
        )

    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 퀘스트 정보는 접근할 수 없습니다."
        )


def build_quest_summary(db: Session, quest_row, status=None, current_step=0):
    target_row = get_quest_target(db, quest_row["quest_id"])
    reward = get_quest_reward_summary(db, quest_row["quest_id"])

    target = None
    if target_row:
        target = {
            "monster_actor_id": target_row["monster_actor_id"],
            "monster_name": target_row["monster_name"] or f"Monster {target_row['monster_actor_id']}",
            "required_count": target_row["required_count"],
        }

    return {
        "quest_id": quest_row["quest_id"],
        "name": quest_row["name"],
        "description": quest_row["description"],
        "type": quest_row["type"],
        "max_steps": quest_row["max_steps"],
        "status": status,
        "current_step": current_step,
        "target": target,
        "reward_exp": reward["exp"],
        "reward_items": reward["items"],
    }


@router.get("/available")
def get_available_quests(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    rows = db.execute(
        text("""
            SELECT
                q.id AS quest_id,
                q.name,
                q.description,
                q.max_steps,
                q.type,
                q.is_repeatable
            FROM Quest q
            WHERE EXISTS (
                SELECT 1
                FROM QuestMonsterTarget qmt
                WHERE qmt.quest_id = q.id
            )
            AND EXISTS (
                SELECT 1
                FROM QuestReward qr
                WHERE qr.quest_id = q.id
            )
            AND NOT EXISTS (
                SELECT 1
                FROM CharacterQuest cq
                WHERE cq.quest_id = q.id
                  AND cq.char_id = :char_id
                  AND cq.status IN ('active', 'completed')
                  AND q.is_repeatable = FALSE
            )
            ORDER BY q.id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    return [build_quest_summary(db, row) for row in rows]


@router.get("/my")
def get_my_quests(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    rows = db.execute(
        text("""
            SELECT
                q.id AS quest_id,
                q.name,
                q.description,
                q.max_steps,
                q.type,
                cq.status,
                cq.current_step
            FROM CharacterQuest cq
            JOIN Quest q ON cq.quest_id = q.id
            WHERE cq.char_id = :char_id
            ORDER BY cq.start_time DESC, q.id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    return [
        build_quest_summary(
            db=db,
            quest_row=row,
            status=row["status"],
            current_step=row["current_step"]
        )
        for row in rows
    ]


@router.post("/{quest_id}/accept", response_model=QuestAcceptResponse)
def accept_quest(
    user_id: str,
    quest_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    quest = db.query(QuestModel).filter(QuestModel.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="퀘스트를 찾을 수 없습니다.")

    if not get_quest_target(db, quest_id):
        raise HTTPException(status_code=400, detail="목표 몬스터가 연결되지 않은 퀘스트입니다.")

    existing = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.quest_id == quest_id,
        CharacterQuestModel.char_id == character.actor_id
    ).first()

    if existing:
        if existing.status == "active":
            raise HTTPException(status_code=400, detail="이미 진행 중인 퀘스트입니다.")
        if existing.status == "completed" and not quest.is_repeatable:
            raise HTTPException(status_code=400, detail="이미 완료한 퀘스트입니다.")

        existing.status = "active"
        existing.current_step = 0
    else:
        db.add(
            CharacterQuestModel(
                quest_id=quest_id,
                char_id=character.actor_id,
                status="active",
                current_step=0
            )
        )

    db.commit()

    return QuestAcceptResponse(
        quest_id=quest_id,
        char_id=character.actor_id,
        status="active",
        message="퀘스트를 수락했습니다."
    )


@router.post("/{quest_id}/battle", response_model=BattleResponse)
def run_quest_battle(
    user_id: str,
    quest_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(db, user_id)
    if not character:
        raise HTTPException(status_code=400, detail="활성 캐릭터가 없습니다.")

    character_quest = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.quest_id == quest_id,
        CharacterQuestModel.char_id == character.actor_id
    ).first()

    if not character_quest:
        raise HTTPException(status_code=400, detail="먼저 퀘스트를 수락해야 합니다.")

    if character_quest.status != "active":
        raise HTTPException(status_code=400, detail="진행 중인 퀘스트만 전투를 실행할 수 있습니다.")

    quest = db.query(QuestModel).filter(QuestModel.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="퀘스트를 찾을 수 없습니다.")

    target = get_quest_target(db, quest_id)
    if not target:
        raise HTTPException(status_code=400, detail="목표 몬스터가 연결되지 않은 퀘스트입니다.")

    before_step = character_quest.current_step
    character_quest.current_step += 1

    required_count = int(target["required_count"])
    reward = {"exp": 0, "items": []}

    if character_quest.current_step >= required_count:
        character_quest.current_step = required_count
        character_quest.status = "completed"
        reward = give_quest_reward(db, character, quest_id)

    db.commit()

    monster_name = target["monster_name"] or f"Monster {target['monster_actor_id']}"

    return BattleResponse(
        quest_id=quest_id,
        quest_name=quest.name,
        monster_name=monster_name,
        victory=True,
        before_step=before_step,
        current_step=character_quest.current_step,
        required_count=required_count,
        quest_status=character_quest.status,
        reward=reward,
        message=f"{monster_name} 처치 성공!" if character_quest.status == "active" else "퀘스트 완료! 보상을 획득했습니다."
    )
