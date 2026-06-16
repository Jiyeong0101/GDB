from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import CharacterModel

router = APIRouter(prefix="/users/{user_id}", tags=["Characters"])


@router.get("/active-character")
def get_active_character(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 후 이용할 수 있습니다."
        )

    # 2. 본인 계정 확인
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 캐릭터 정보는 조회할 수 없습니다."
        )

    # 3. 활성 캐릭터 조회
    character = db.query(CharacterModel).filter(
        CharacterModel.user_id == user_id,
        CharacterModel.active == True
    ).first()

    if not character:
        return None

    # 4. 종족 조회
    specimen_rows = db.execute(
        text("""
            SELECT 
                cs.type AS race_type,
                s.name AS race_name,
                cs.fraction AS fraction
            FROM CharacterSpecimen cs
            JOIN Specimen s ON cs.type = s.type
            WHERE cs.char_id = :char_id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    races = [
        {
            "type": row["race_type"],
            "name": row["race_name"],
            "fraction": float(row["fraction"])
        }
        for row in specimen_rows
    ]

    if races:
        race_label = " / ".join([f"{r['name']}({r['type']})" for r in races])
    else:
        race_label = None

    # 5. 활성 직업 조회
    job_row = db.execute(
        text("""
            SELECT 
                cj.type AS job_type,
                j.name AS job_name,
                j.description AS job_description
            FROM CharacterJob cj
            JOIN Job j ON cj.type = j.type
            WHERE cj.char_id = :char_id
              AND cj.active = TRUE
            LIMIT 1
        """),
        {"char_id": character.actor_id}
    ).mappings().first()

    # 6. 스탯 조회
    stat_rows = db.execute(
        text("""
            SELECT 
                ast.stat_type AS stat_type,
                s.name AS stat_name,
                s.description AS description,
                ast.value AS value
            FROM ActorStat ast
            JOIN Stat s ON ast.stat_type = s.type
            WHERE ast.actor_id = :actor_id
            ORDER BY ast.stat_type
        """),
        {"actor_id": character.actor_id}
    ).mappings().all()

    stats = [
        {
            "stat_type": row["stat_type"],
            "stat_name": row["stat_name"],
            "description": row["description"],
            "value": row["value"]
        }
        for row in stat_rows
    ]

    # 7. 스킬 조회
    skill_rows = db.execute(
        text("""
            SELECT
                s.id AS skill_id,
                s.name AS skill_name,
                s.description AS description,
                s.mp_cost AS mp_cost,
                s.cooldown_sec AS cooldown_sec,
                cs.skill_level AS skill_level
            FROM CharacterSkill cs
            JOIN Skill s ON cs.skill_id = s.id
            WHERE cs.char_id = :char_id
            ORDER BY s.id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    skills = [
        {
            "skill_id": row["skill_id"],
            "skill_name": row["skill_name"],
            "description": row["description"],
            "mp_cost": row["mp_cost"],
            "cooldown_sec": row["cooldown_sec"],
            "skill_level": float(row["skill_level"])
        }
        for row in skill_rows
    ]

    # 8. 인벤토리 조회
    inventory_rows = db.execute(
        text("""
            SELECT
                inv.id AS inventory_id,
                inv.type AS inventory_type,
                inv.capacity AS capacity,
                i.id AS item_id,
                i.name AS item_name,
                i.description AS item_description,
                i.type AS item_type,
                i.sub_type AS item_sub_type,
                ii.quantity AS quantity
            FROM Inventory inv
            JOIN InventoryItem ii ON inv.id = ii.inventory_id
            JOIN Item i ON ii.item_id = i.id
            WHERE inv.owner_id = :char_id
            ORDER BY inv.id, i.id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    inventory = [
        {
            "inventory_id": row["inventory_id"],
            "inventory_type": row["inventory_type"],
            "capacity": row["capacity"],
            "item_id": row["item_id"],
            "item_name": row["item_name"],
            "description": row["item_description"],
            "item_type": row["item_type"],
            "item_sub_type": row["item_sub_type"],
            "quantity": row["quantity"]
        }
        for row in inventory_rows
    ]

    return {
        "actor_id": character.actor_id,
        "character_name": character.character_name,
        "level": character.level,
        "exp": character.exp,
        "race": race_label,
        "races": races,
        "job": job_row["job_type"] if job_row else None,
        "job_name": job_row["job_name"] if job_row else None,
        "stats": stats,
        "skills": skills,
        "inventory": inventory
    }
