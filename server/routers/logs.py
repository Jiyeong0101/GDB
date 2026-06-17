from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from schemas import BattleLogResponse
from services.quest_service import get_active_character_or_none

router = APIRouter(prefix="/users/{user_id}/battle-logs", tags=["Battle Logs"])


def check_user_permission(user_id: str, current_user):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인 후 이용할 수 있습니다.")
    if current_user.get("id") != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="다른 사용자의 전투 기록은 조회할 수 없습니다.")


@router.get("", response_model=list[BattleLogResponse])
def get_battle_logs(
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
                bl.id,
                bl.char_id,
                c.character_name,
                bl.quest_id,
                q.name AS quest_name,
                bl.monster_actor_id,
                COALESCE(qmt.target_name, CONCAT('Monster ', bl.monster_actor_id)) AS monster_name,
                bl.result,
                bl.gained_exp,
                bl.message,
                DATE_FORMAT(bl.battle_time, '%Y-%m-%d %H:%i:%s') AS battle_time
            FROM BattleLog bl
            JOIN `Character` c ON bl.char_id = c.actor_id
            LEFT JOIN Quest q ON bl.quest_id = q.id
            LEFT JOIN QuestMonsterTarget qmt
                ON bl.quest_id = qmt.quest_id
               AND bl.monster_actor_id = qmt.monster_actor_id
            WHERE bl.char_id = :char_id
            ORDER BY bl.battle_time DESC, bl.id DESC
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    return [BattleLogResponse(**dict(row)) for row in rows]
