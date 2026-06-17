from sqlalchemy.orm import Session
from models import (
    StatModel,
    ActorStatModel,
    LevelMasterModel,
    LevelBaseStatModel,
    SpecimenBaseStatModel,
    InventoryModel,
    InventoryItemModel,
    ItemModel,
    SkillModel,
    CharacterSkillModel,
    QuestModel,
    CharacterQuestModel,
)


TUTORIAL_QUEST_ID = 100


def initialize_character_defaults(db: Session, actor_id: int, race: str):
    """
    새 캐릭터 생성 시 기본 스탯, 기본 가방, 기본 아이템, 기본 스킬,
    튜토리얼 퀘스트를 자동 지급한다.
    """

    # =========================
    # 1. 기본 스탯 생성
    # =========================
    stat_values = {}

    all_stats = db.query(StatModel).all()
    for stat in all_stats:
        stat_values[stat.type] = 0

    level_master = db.query(LevelMasterModel).filter(
        LevelMasterModel.level == 1
    ).first()

    if level_master:
        stat_values["MAX_HP"] = level_master.max_hp
        stat_values["HP"] = level_master.max_hp
        stat_values["MAX_MP"] = level_master.max_mp
        stat_values["MP"] = level_master.max_mp

    level_base_stats = db.query(LevelBaseStatModel).filter(
        LevelBaseStatModel.char_level == 1
    ).all()

    for base_stat in level_base_stats:
        stat_values[base_stat.stat_type] = (
            stat_values.get(base_stat.stat_type, 0) + base_stat.value
        )

    specimen_stats = db.query(SpecimenBaseStatModel).filter(
        SpecimenBaseStatModel.specimen_type == race
    ).all()

    for specimen_stat in specimen_stats:
        stat_values[specimen_stat.stat_type] = (
            stat_values.get(specimen_stat.stat_type, 0) + specimen_stat.value
        )

    stat_values["HP"] = stat_values.get("MAX_HP", stat_values.get("HP", 0))
    stat_values["MP"] = min(10, stat_values.get("MAX_MP", 10))

    for stat_type, value in stat_values.items():
        db.add(
            ActorStatModel(
                actor_id=actor_id,
                stat_type=stat_type,
                value=int(value)
            )
        )

    # =========================
    # 2. 기본 인벤토리 생성
    # =========================
    default_bag_item = db.query(ItemModel).filter(ItemModel.id == 13).first()
    bag_capacity = default_bag_item.capacity if default_bag_item else 20

    new_inventory = InventoryModel(
        owner_id=actor_id,
        type="MAIN_BAG",
        capacity=bag_capacity
    )

    db.add(new_inventory)
    db.flush()

    # =========================
    # 3. 기본 아이템 지급
    # =========================
    default_items = [
        {"item_id": 1, "quantity": 1},
        {"item_id": 6, "quantity": 1},
        {"item_id": 7, "quantity": 1},  # 마나 포션
    ]

    for default_item in default_items:
        item = db.query(ItemModel).filter(
            ItemModel.id == default_item["item_id"]
        ).first()

        if item:
            db.add(
                InventoryItemModel(
                    inventory_id=new_inventory.id,
                    item_id=item.id,
                    quantity=default_item["quantity"]
                )
            )

    # =========================
    # 4. 기본 스킬 지급
    # =========================
    beginner_skill = db.query(SkillModel).filter(SkillModel.id == 1).first()

    if beginner_skill:
        db.add(
            CharacterSkillModel(
                char_id=actor_id,
                skill_id=beginner_skill.id,
                skill_level=1.0
            )
        )

    # =========================
    # 5. 튜토리얼 퀘스트 자동 지급
    # =========================
    tutorial_quest = db.query(QuestModel).filter(
        QuestModel.id == TUTORIAL_QUEST_ID
    ).first()

    if tutorial_quest:
        db.add(
            CharacterQuestModel(
                quest_id=TUTORIAL_QUEST_ID,
                char_id=actor_id,
                status="active",
                current_step=0
            )
        )
