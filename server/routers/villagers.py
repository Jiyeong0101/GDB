from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from routers.quests import build_quest_summary
from services.quest_service import get_active_character_or_none

router = APIRouter(prefix="/users/{user_id}/villagers", tags=["Villagers"])


def check_user_permission(user_id: str, current_user):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인 후 이용할 수 있습니다.")
    if current_user.get("id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="다른 사용자의 NPC 정보는 접근할 수 없습니다.")


@router.get("")
def get_villagers(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    rows = db.execute(
        text("""
            SELECT
                v.npc_id AS villager_id,
                pvi.name,
                pvi.role,
                pvi.description
            FROM Villager v
            JOIN ProjectVillagerInfo pvi ON v.npc_id = pvi.villager_id
            ORDER BY v.npc_id
        """)
    ).mappings().all()

    return [
        {
            "villager_id": row["villager_id"],
            "name": row["name"],
            "role": row["role"],
            "description": row["description"],
        }
        for row in rows
    ]


@router.get("/{villager_id}/quests")
def get_villager_quests(
    user_id: str,
    villager_id: int,
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
            FROM VillagerQuest vq
            JOIN Quest q ON vq.quest_id = q.id
            WHERE vq.villager_id = :villager_id
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
        {"villager_id": villager_id, "char_id": character.actor_id}
    ).mappings().all()

    return [build_quest_summary(db, row, source="npc") for row in rows]
