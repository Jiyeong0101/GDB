from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models import (
    ActorStatModel,
    BattleEncounterModel,
    CharacterModel,
    CharacterQuestModel,
    CharacterSkillModel,
    QuestModel,
    SkillModel,
)
from services.quest_service import (
    get_quest_target,
    give_quest_reward,
    create_battle_log,
)


def get_player_atk(db: Session, char_id: int) -> int:
    stat = db.query(ActorStatModel).filter(
        ActorStatModel.actor_id == char_id,
        ActorStatModel.stat_type == "ATK"
    ).first()
    return stat.value if stat else 1

def get_actor_stat(db: Session, actor_id: int, stat_type: str):
    return db.query(ActorStatModel).filter(
        ActorStatModel.actor_id == actor_id,
        ActorStatModel.stat_type == stat_type
    ).first()


def consume_mp(db: Session, char_id: int, mp_cost: int):
    mp_stat = get_actor_stat(
        db=db,
        actor_id=char_id,
        stat_type="MP"
    )

    if not mp_stat:
        raise HTTPException(
            status_code=400,
            detail="캐릭터의 MP 스탯을 찾을 수 없습니다."
        )

    if mp_stat.value < mp_cost:
        raise HTTPException(
            status_code=400,
            detail=f"MP가 부족합니다. 필요 MP: {mp_cost}, 현재 MP: {mp_stat.value}"
        )

    mp_stat.value -= mp_cost

    return mp_stat.value


def get_character_skill(db: Session, char_id: int, skill_id: int):
    return db.execute(
        text("""
            SELECT
                s.id AS skill_id,
                s.name AS skill_name,
                s.description,
                s.mp_cost,
                s.cooldown_sec,
                cs.skill_level
            FROM CharacterSkill cs
            JOIN Skill s ON cs.skill_id = s.id
            WHERE cs.char_id = :char_id
              AND cs.skill_id = :skill_id
        """),
        {"char_id": char_id, "skill_id": skill_id}
    ).mappings().first()


def get_character_skill_options(db: Session, char_id: int):
    rows = db.execute(
        text("""
            SELECT
                s.id AS skill_id,
                s.name AS skill_name,
                s.description,
                s.mp_cost,
                s.cooldown_sec,
                cs.skill_level
            FROM CharacterSkill cs
            JOIN Skill s ON cs.skill_id = s.id
            WHERE cs.char_id = :char_id
            ORDER BY s.id
        """),
        {"char_id": char_id}
    ).mappings().all()

    return [
        {
            "skill_id": row["skill_id"],
            "skill_name": row["skill_name"],
            "description": row["description"],
            "skill_level": float(row["skill_level"]),
            "mp_cost": row["mp_cost"],
            "cooldown_sec": row["cooldown_sec"],
        }
        for row in rows
    ]


def calculate_damage(player_atk: int, skill_id: int, skill_level: float, monster_def: int) -> int:
    # 클릭형 단순 전투: 스킬마다 보정값을 다르게 두어 새 스킬 획득 효과를 보여준다.
    skill_bonus_map = {
        1: 5,    # 기본 베기
        2: 12,   # 연속 베기
        3: 18,   # 분노의 일격
        5: 16,   # 파이어볼
        7: 10,   # 돌진
    }
    base_bonus = skill_bonus_map.get(skill_id, 5)
    level_bonus = int(max(skill_level - 1.0, 0) * 3)
    return max(1, player_atk + base_bonus + level_bonus - monster_def)


def build_encounter_response(db: Session, encounter: BattleEncounterModel):
    quest = db.query(QuestModel).filter(QuestModel.id == encounter.quest_id).first()
    target = get_quest_target(db, encounter.quest_id)

    return {
        "encounter_id": encounter.id,
        "quest_id": encounter.quest_id,
        "quest_name": quest.name if quest else f"Quest {encounter.quest_id}",
        "monster_actor_id": encounter.monster_actor_id,
        "monster_name": target["monster_name"] if target else f"Monster {encounter.monster_actor_id}",
        "monster_current_hp": encounter.monster_current_hp,
        "monster_max_hp": encounter.monster_max_hp,
        "status": encounter.status,
        "turn_count": encounter.turn_count,
        "skills": get_character_skill_options(db, encounter.char_id)
    }


def get_active_or_latest_encounter(db: Session, char_id: int, quest_id: int):
    return db.query(BattleEncounterModel).filter(
        BattleEncounterModel.char_id == char_id,
        BattleEncounterModel.quest_id == quest_id
    ).order_by(BattleEncounterModel.id.desc()).first()


def start_encounter(db: Session, character: CharacterModel, quest_id: int):
    character_quest = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.quest_id == quest_id,
        CharacterQuestModel.char_id == character.actor_id
    ).first()

    if not character_quest:
        raise HTTPException(status_code=400, detail="먼저 퀘스트를 수락해야 합니다.")

    if character_quest.status != "active":
        raise HTTPException(status_code=400, detail="진행 중인 퀘스트만 전투를 시작할 수 있습니다.")

    existing = db.query(BattleEncounterModel).filter(
        BattleEncounterModel.char_id == character.actor_id,
        BattleEncounterModel.quest_id == quest_id,
        BattleEncounterModel.status == "active"
    ).order_by(BattleEncounterModel.id.desc()).first()

    if existing:
        return existing

    target = get_quest_target(db, quest_id)
    if not target:
        raise HTTPException(status_code=400, detail="목표 몬스터가 연결되지 않은 퀘스트입니다.")

    encounter = BattleEncounterModel(
        char_id=character.actor_id,
        quest_id=quest_id,
        monster_actor_id=target["monster_actor_id"],
        monster_current_hp=int(target["hp"]),
        monster_max_hp=int(target["hp"]),
        status="active",
        turn_count=0,
        started_at=datetime.now()
    )
    db.add(encounter)
    db.flush()

    return encounter


def attack_encounter(db: Session, character: CharacterModel, quest_id: int, skill_id: int):
    encounter = db.query(BattleEncounterModel).filter(
        BattleEncounterModel.char_id == character.actor_id,
        BattleEncounterModel.quest_id == quest_id,
        BattleEncounterModel.status == "active"
    ).order_by(BattleEncounterModel.id.desc()).first()

    if not encounter:
        raise HTTPException(status_code=400, detail="진행 중인 전투가 없습니다. 먼저 전투를 시작하세요.")

    character_quest = db.query(CharacterQuestModel).filter(
        CharacterQuestModel.quest_id == quest_id,
        CharacterQuestModel.char_id == character.actor_id
    ).first()

    if not character_quest or character_quest.status != "active":
        raise HTTPException(status_code=400, detail="진행 중인 퀘스트만 공격할 수 있습니다.")

    quest = db.query(QuestModel).filter(QuestModel.id == quest_id).first()
    target = get_quest_target(db, quest_id)
    skill = get_character_skill(db, character.actor_id, skill_id)

    if not target:
        raise HTTPException(status_code=400, detail="목표 몬스터가 연결되지 않은 퀘스트입니다.")

    if not skill:
        raise HTTPException(status_code=400, detail="해당 캐릭터가 보유하지 않은 스킬입니다.")
    
    mp_cost = int(skill["mp_cost"] or 0)

    remaining_mp = consume_mp(
        db=db,
        char_id=character.actor_id,
        mp_cost=mp_cost
    )

    player_atk = get_player_atk(db, character.actor_id)
    damage = calculate_damage(
        player_atk=player_atk,
        skill_id=int(skill["skill_id"]),
        skill_level=float(skill["skill_level"]),
        monster_def=int(target["monster_def"])
    )

    encounter.monster_current_hp = max(0, encounter.monster_current_hp - damage)
    encounter.turn_count += 1

    monster_dead = encounter.monster_current_hp <= 0
    reward = {"exp": 0, "items": []}
    required_count = int(target["required_count"])

    if monster_dead:
        encounter.status = "victory"
        encounter.ended_at = datetime.now()

        character_quest.current_step += 1

        if character_quest.current_step >= required_count:
            character_quest.current_step = required_count
            character_quest.status = "completed"
            reward = give_quest_reward(db, character, quest_id)

            level_text = ""
            if reward.get("level_ups"):
                level_text = " 레벨업: " + ", ".join([f"Lv.{level}" for level in reward["level_ups"]]) + "!"

            skill_text = ""
            if reward.get("learned_skills"):
                skill_names = ", ".join([skill["skill_name"] for skill in reward["learned_skills"]])
                skill_text = f" 신규 스킬 습득: {skill_names}!"

            message = f"{target['monster_name']}을(를) 처치했습니다. {quest.name} 퀘스트 완료!{level_text}{skill_text}"
        else:
            message = f"{target['monster_name']}을(를) 처치했습니다."

        create_battle_log(
            db=db,
            char_id=character.actor_id,
            quest_id=quest_id,
            monster_actor_id=int(target["monster_actor_id"]),
            result="victory",
            gained_exp=reward["exp"],
            message=message
        )
    else:
        message = (
        f"{skill['skill_name']} 사용! "
        f"{target['monster_name']}에게 {damage} 데미지를 주었습니다. "
        f"남은 MP: {remaining_mp}"
)

    return {
        "encounter_id": encounter.id,
        "quest_id": quest_id,
        "quest_name": quest.name if quest else f"Quest {quest_id}",
        "monster_name": target["monster_name"],
        "skill_name": skill["skill_name"],
        "damage": damage,
        "monster_current_hp": encounter.monster_current_hp,
        "monster_max_hp": encounter.monster_max_hp,
        "monster_dead": monster_dead,
        "quest_status": character_quest.status,
        "current_step": character_quest.current_step,
        "required_count": required_count,
        "reward": reward,
        "message": message,
    }
