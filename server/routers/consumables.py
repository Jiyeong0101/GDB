from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from constants import MAIN_BAG_TYPE, MANA_POTION_DEFAULT_RECOVER, MANA_POTION_ITEM_ID
from models import (
    ActorStatModel,
    InventoryModel,
    InventoryItemModel,
    ItemModel,
    ItemBonusStatModel,
)
from services.quest_service import get_active_character_or_none


router = APIRouter(
    prefix="/users/{user_id}/items",
    tags=["Consumables"]
)



def check_user_permission(user_id: str, current_user):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 후 이용할 수 있습니다."
        )

    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 아이템은 사용할 수 없습니다."
        )


def get_stat(db: Session, actor_id: int, stat_type: str):
    return db.query(ActorStatModel).filter(
        ActorStatModel.actor_id == actor_id,
        ActorStatModel.stat_type == stat_type
    ).first()


@router.post("/mana-potion/use")
def use_mana_potion(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_user_permission(user_id, current_user)

    character = get_active_character_or_none(
        db=db,
        user_id=user_id
    )

    if not character:
        raise HTTPException(
            status_code=400,
            detail="활성 캐릭터가 없습니다."
        )

    inventory = db.query(InventoryModel).filter(
        InventoryModel.owner_id == character.actor_id,
        InventoryModel.type == MAIN_BAG_TYPE
    ).first()

    if not inventory:
        raise HTTPException(
            status_code=400,
            detail="인벤토리가 없습니다."
        )

    inventory_item = db.query(InventoryItemModel).filter(
        InventoryItemModel.inventory_id == inventory.id,
        InventoryItemModel.item_id == MANA_POTION_ITEM_ID
    ).first()

    if not inventory_item or inventory_item.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="마나 포션이 없습니다."
        )

    item = db.query(ItemModel).filter(
        ItemModel.id == MANA_POTION_ITEM_ID
    ).first()

    if not item:
        raise HTTPException(
            status_code=404,
            detail="마나 포션 아이템 정보를 찾을 수 없습니다."
        )

    mp_stat = get_stat(db, character.actor_id, "MP")
    max_mp_stat = get_stat(db, character.actor_id, "MAX_MP")

    if not mp_stat or not max_mp_stat:
        raise HTTPException(
            status_code=400,
            detail="MP 또는 MAX_MP 스탯을 찾을 수 없습니다."
        )

    before_mp = mp_stat.value
    max_mp = max_mp_stat.value

    if before_mp >= max_mp:
        raise HTTPException(
            status_code=400,
            detail="이미 MP가 가득 차 있습니다."
        )

    bonus = db.query(ItemBonusStatModel).filter(
        ItemBonusStatModel.item_id == MANA_POTION_ITEM_ID,
        ItemBonusStatModel.stat_type == "MP"
    ).first()

    recover_amount = bonus.value if bonus else MANA_POTION_DEFAULT_RECOVER

    after_mp = min(max_mp, before_mp + recover_amount)
    real_recovered = after_mp - before_mp

    mp_stat.value = after_mp

    inventory_item.quantity -= 1

    remaining_quantity = inventory_item.quantity

    if inventory_item.quantity <= 0:
        db.delete(inventory_item)
        remaining_quantity = 0

    db.commit()

    return {
        "item_id": MANA_POTION_ITEM_ID,
        "item_name": item.name,
        "stat_type": "MP",
        "before_value": before_mp,
        "after_value": after_mp,
        "max_value": max_mp,
        "recovered_amount": real_recovered,
        "remaining_quantity": remaining_quantity,
        "message": f"{item.name}을 사용해 MP를 {real_recovered} 회복했습니다."
    }