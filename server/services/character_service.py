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
)


def initialize_character_defaults(db: Session, actor_id: int, race: str):
    """
    새 캐릭터 생성 시 기본 스탯, 기본 가방, 기본 아이템, 기본 스킬을 지급한다.
    기존 DB 테이블 구조는 수정하지 않고, 데이터만 추가한다.
    """

    # =========================
    # 1. 기본 스탯 생성
    # =========================
    stat_values = {}

    # 모든 스탯을 0으로 먼저 초기화
    all_stats = db.query(StatModel).all()
    for stat in all_stats:
        stat_values[stat.type] = 0

    # 레벨 1의 HP / MP 기준값 적용
    level_master = db.query(LevelMasterModel).filter(
        LevelMasterModel.level == 1
    ).first()

    if level_master:
        stat_values["MAX_HP"] = level_master.max_hp
        stat_values["HP"] = level_master.max_hp
        stat_values["MAX_MP"] = level_master.max_mp
        stat_values["MP"] = level_master.max_mp

    # 레벨 1 기본 능력치 적용
    level_base_stats = db.query(LevelBaseStatModel).filter(
        LevelBaseStatModel.char_level == 1
    ).all()

    for base_stat in level_base_stats:
        stat_values[base_stat.stat_type] = (
            stat_values.get(base_stat.stat_type, 0) + base_stat.value
        )

    # 종족 보너스 적용
    specimen_stats = db.query(SpecimenBaseStatModel).filter(
        SpecimenBaseStatModel.specimen_type == race
    ).all()

    for specimen_stat in specimen_stats:
        stat_values[specimen_stat.stat_type] = (
            stat_values.get(specimen_stat.stat_type, 0) + specimen_stat.value
        )

    # MAX_HP / MAX_MP 보너스가 반영되었으면 현재 HP / MP도 최대치로 맞춤
    stat_values["HP"] = stat_values.get("MAX_HP", stat_values.get("HP", 0))
    stat_values["MP"] = stat_values.get("MAX_MP", stat_values.get("MP", 0))

    # ActorStat 저장
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
        {"item_id": 1, "quantity": 1},  # 초보자의 검
        {"item_id": 6, "quantity": 3},  # 빨간 포션
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
