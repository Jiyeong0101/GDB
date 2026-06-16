from sqlalchemy import text
from sqlalchemy.orm import Session

from models import (
    CharacterModel,
    CharacterQuestModel,
    InventoryModel,
    InventoryItemModel,
    ItemModel,
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
                COALESCE(qmt.target_name, c.character_name) AS monster_name
            FROM QuestMonsterTarget qmt
            JOIN Monster m ON qmt.monster_actor_id = m.actor_id
            LEFT JOIN `Character` c ON c.actor_id = m.actor_id
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
        InventoryModel.type == "MAIN_BAG"
    ).first()

    if inventory:
        return inventory

    default_bag = db.query(ItemModel).filter(ItemModel.id == 13).first()
    capacity = default_bag.capacity if default_bag else 20

    inventory = InventoryModel(
        owner_id=char_id,
        type="MAIN_BAG",
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

    return reward
