from pydantic import BaseModel
from typing import Optional


# ==========================================
# Pydantic Schemas (API 입출력 검증용)
# ==========================================

class UserLogin(BaseModel):
    user_id: str
    password: str


class UserCreate(BaseModel):
    user_identifier: str
    nickname: str
    password: str


class UserResponse(BaseModel):
    user_id: str
    name: str

    class Config:
        orm_mode = False


class UserDeletionResponse(BaseModel):
    user_id: str


class CharacterCreate(BaseModel):
    character_name: str
    race: str


class CharacterResponse(BaseModel):
    actor_id: int
    user_id: str
    character_name: str
    level: int
    exp: int
    active: bool

    class Config:
        orm_mode = True


class CharacterDeletionResponse(BaseModel):
    actor_id: int
    character_name: str
    message: str


class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    sub_type: Optional[str] = None
    capacity: Optional[int] = -1


class ItemResponse(ItemCreate):
    id: int

    class Config:
        orm_mode = True

# ==========================================
# Quest / Battle Schemas
# ==========================================

class QuestTargetResponse(BaseModel):
    monster_actor_id: int
    monster_name: str
    required_count: int


class QuestRewardItemResponse(BaseModel):
    item_id: int
    item_name: str
    quantity: int


class QuestSummaryResponse(BaseModel):
    quest_id: int
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    max_steps: int
    status: Optional[str] = None
    current_step: int = 0
    target: Optional[QuestTargetResponse] = None
    reward_exp: int = 0
    reward_items: list[QuestRewardItemResponse] = []


class QuestAcceptResponse(BaseModel):
    quest_id: int
    char_id: int
    status: str
    message: str


class BattleRewardResponse(BaseModel):
    exp: int = 0
    items: list[QuestRewardItemResponse] = []


class BattleResponse(BaseModel):
    quest_id: int
    quest_name: str
    monster_name: str
    victory: bool
    before_step: int
    current_step: int
    required_count: int
    quest_status: str
    reward: BattleRewardResponse
    message: str
