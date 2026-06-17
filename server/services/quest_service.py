from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

from constants import (
    DEFAULT_BAG_CAPACITY,
    DEFAULT_BAG_ITEM_ID,
    MAIN_BAG_TYPE,
)
from models import (
    ActorStatModel,
    BattleLogModel,
    CharacterModel,
    CharacterSkillModel,
    InventoryModel,
    InventoryItemModel,
    ItemModel,
    LevelBaseStatModel,
    LevelMasterModel,
    ProjectLevelSkillRewardModel,
    SkillModel,
)


def get_active_character_or_none(db: Session, user_id: str):
    return db.query(CharacterModel).filter(
        CharacterModel.user_id == user_id,
        CharacterModel.active == True
    ).first()


def get_quest_target(db: Session, quest_id: int):
    return db.execute(
        text("""
            SELECT
                qmt.quest_id,
                qmt.monster_actor_id,
                qmt.required_count,
                qmt.target_name,
                m.hp,
                m.atk,
                m.def AS monster_def,
                COALESCE(qmt.target_name, CONCAT('Monster ', qmt.monster_actor_id)) AS monster_name
            FROM QuestMonsterTarget qmt
            JOIN Monster m ON qmt.monster_actor_id = m.actor_id
            WHERE qmt.quest_id = :quest_id
            LIMIT 1
        """),
        {"quest_id": quest_id}
    ).mappings().first()


def get_quest_reward_summary(db: Session, quest_id: int):
    exp_row = db.execute(
        text("""
            SELECT COALESCE(SUM(re.amount), 0) AS exp_amount
            FROM QuestReward qr
            JOIN RewardExp re ON qr.reward_id = re.reward_id
            WHERE qr.quest_id = :quest_id
        """),
        {"quest_id": quest_id}
    ).mappings().first()

    item_rows = db.execute(
        text("""
            SELECT
                i.id AS item_id,
                i.name AS item_name,
                SUM(ri.quantity) AS quantity
            FROM QuestReward qr
            JOIN RewardItem ri ON qr.reward_id = ri.reward_id
            JOIN Item i ON ri.item_id = i.id
            WHERE qr.quest_id = :quest_id
            GROUP BY i.id, i.name
            ORDER BY i.id
        """),
        {"quest_id": quest_id}
    ).mappings().all()

    return {
        "exp": int(exp_row["exp_amount"] or 0),
        "items": [
            {
                "item_id": row["item_id"],
                "item_name": row["item_name"],
                "quantity": int(row["quantity"]),
            }
            for row in item_rows
        ]
    }


def ensure_main_inventory(db: Session, char_id: int):
    inventory = db.query(InventoryModel).filter(
        InventoryModel.owner_id == char_id,
        InventoryModel.type == MAIN_BAG_TYPE
    ).first()

    if inventory:
        return inventory

    default_bag = db.query(ItemModel).filter(ItemModel.id == DEFAULT_BAG_ITEM_ID).first()
    capacity = default_bag.capacity if default_bag else DEFAULT_BAG_CAPACITY

    inventory = InventoryModel(
        owner_id=char_id,
        type=MAIN_BAG_TYPE,
        capacity=capacity
    )
    db.add(inventory)
    db.flush()

    return inventory


def add_item_to_inventory(db: Session, inventory_id: int, item_id: int, quantity: int):
    inventory_item = db.query(InventoryItemModel).filter(
        InventoryItemModel.inventory_id == inventory_id,
        InventoryItemModel.item_id == item_id
    ).first()

    if inventory_item:
        inventory_item.quantity += quantity
    else:
        db.add(
            InventoryItemModel(
                inventory_id=inventory_id,
                item_id=item_id,
                quantity=quantity
            )
        )


def get_or_create_actor_stat(db: Session, actor_id: int, stat_type: str):
    actor_stat = db.query(ActorStatModel).filter(
        ActorStatModel.actor_id == actor_id,
        ActorStatModel.stat_type == stat_type
    ).first()

    if actor_stat:
        return actor_stat

    actor_stat = ActorStatModel(
        actor_id=actor_id,
        stat_type=stat_type,
        value=0
    )
    db.add(actor_stat)
    db.flush()

    return actor_stat


def add_actor_stat_value(db: Session, actor_id: int, stat_type: str, delta: int):
    if delta == 0:
        return

    actor_stat = get_or_create_actor_stat(
        db=db,
        actor_id=actor_id,
        stat_type=stat_type
    )
    actor_stat.value += int(delta)


def get_level_base_stat_dict(db: Session, level: int):
    rows = db.query(LevelBaseStatModel).filter(
        LevelBaseStatModel.char_level == level
    ).all()

    return {
        row.stat_type: row.value
        for row in rows
    }


def apply_level_stat_growth(db: Session, character: CharacterModel, old_level: int, new_level: int):
    """
    레벨업 시 MAX_HP/MAX_MP는 LevelMaster 차이만큼 증가시키고,
    ATK/DEF/INT 등은 LevelBaseStat의 이전 레벨 대비 증가분만 적용한다.
    """
    old_master = db.query(LevelMasterModel).filter(
        LevelMasterModel.level == old_level
    ).first()
    new_master = db.query(LevelMasterModel).filter(
        LevelMasterModel.level == new_level
    ).first()

    if old_master and new_master:
        hp_delta = int(new_master.max_hp - old_master.max_hp)
        mp_delta = int(new_master.max_mp - old_master.max_mp)

        add_actor_stat_value(db, character.actor_id, "MAX_HP", hp_delta)
        # HP는 레벨업 보상 체감을 위해 증가분만큼 현재 HP도 회복한다.
        add_actor_stat_value(db, character.actor_id, "HP", hp_delta)

        add_actor_stat_value(db, character.actor_id, "MAX_MP", mp_delta)
        # MP는 스킬 자원이므로 레벨업 시 현재 MP는 자동 회복하지 않는다.
        # add_actor_stat_value(db, character.actor_id, "MP", mp_delta)

    old_base = get_level_base_stat_dict(db, old_level)
    new_base = get_level_base_stat_dict(db, new_level)

    for stat_type in set(old_base.keys()) | set(new_base.keys()):
        delta = int(new_base.get(stat_type, 0) - old_base.get(stat_type, 0))
        add_actor_stat_value(db, character.actor_id, stat_type, delta)


def learn_level_skills(db: Session, character: CharacterModel, level: int):
    reward_rows = db.query(ProjectLevelSkillRewardModel).filter(
        ProjectLevelSkillRewardModel.level == level
    ).all()

    learned_skills = []

    for reward_row in reward_rows:
        existing = db.query(CharacterSkillModel).filter(
            CharacterSkillModel.char_id == character.actor_id,
            CharacterSkillModel.skill_id == reward_row.skill_id
        ).first()

        skill = db.query(SkillModel).filter(
            SkillModel.id == reward_row.skill_id
        ).first()

        if not skill:
            continue

        if existing:
            if existing.skill_level < reward_row.skill_level:
                existing.skill_level = reward_row.skill_level
            continue

        db.add(
            CharacterSkillModel(
                char_id=character.actor_id,
                skill_id=reward_row.skill_id,
                skill_level=reward_row.skill_level
            )
        )

        learned_skills.append(
            {
                "skill_id": skill.id,
                "skill_name": skill.name,
                "skill_level": float(reward_row.skill_level),
                "description": skill.description,
            }
        )

    return learned_skills


def process_level_up(db: Session, character: CharacterModel):
    """
    Character.exp는 현재 레벨에서 다음 레벨까지의 진행 경험치로 사용한다.
    LevelMaster.max_exp_to_next 이상이면 레벨을 올리고 남은 EXP를 보존한다.
    """
    level_ups = []
    learned_skills = []

    # 무한 루프 방지용. 현재 프로젝트 레벨 테이블 규모에서는 충분하다.
    for _ in range(20):
        current_master = db.query(LevelMasterModel).filter(
            LevelMasterModel.level == character.level
        ).first()
        next_master = db.query(LevelMasterModel).filter(
            LevelMasterModel.level == character.level + 1
        ).first()

        if not current_master or not next_master:
            break

        if character.exp < current_master.max_exp_to_next:
            break

        character.exp -= current_master.max_exp_to_next
        old_level = character.level
        character.level += 1
        new_level = character.level

        apply_level_stat_growth(
            db=db,
            character=character,
            old_level=old_level,
            new_level=new_level
        )

        level_ups.append(new_level)
        learned_skills.extend(
            learn_level_skills(
                db=db,
                character=character,
                level=new_level
            )
        )

    return {
        "level_ups": level_ups,
        "learned_skills": learned_skills,
    }


def give_quest_reward(db: Session, character: CharacterModel, quest_id: int):
    reward = get_quest_reward_summary(db, quest_id)

    if reward["exp"] > 0:
        character.exp += reward["exp"]

    inventory = ensure_main_inventory(db, character.actor_id)

    for item in reward["items"]:
        add_item_to_inventory(
            db=db,
            inventory_id=inventory.id,
            item_id=item["item_id"],
            quantity=item["quantity"]
        )

    level_result = process_level_up(db, character)

    reward["level_ups"] = level_result["level_ups"]
    reward["learned_skills"] = level_result["learned_skills"]

    return reward


def create_battle_log(
    db: Session,
    char_id: int,
    quest_id: int,
    monster_actor_id: int,
    result: str,
    gained_exp: int,
    message: str
):
    battle_log = BattleLogModel(
        char_id=char_id,
        quest_id=quest_id,
        monster_actor_id=monster_actor_id,
        result=result,
        gained_exp=gained_exp,
        message=message,
        battle_time=datetime.now()
    )
    db.add(battle_log)
