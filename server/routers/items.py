from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import ItemModel
from schemas import ItemCreate, ItemResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db)
):
    new_item = ItemModel(**item.dict())

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return new_item


@router.get("", response_model=List[ItemResponse])
def get_items(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    items = db.query(ItemModel).offset(skip).limit(limit).all()
    return items
