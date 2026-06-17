from pydantic import BaseModel
from typing import Optional


# ==========================================
# User / Auth Schemas
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


# ==========================================
# Character / Item Schemas
# ==========================================

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
# Quest / Reward Schemas
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
    source: Optional[str] = None
    target: Optional[QuestTargetResponse] = None
    reward_exp: int = 0
    reward_items: list[QuestRewardItemResponse] = []


class QuestAcceptResponse(BaseModel):
    quest_id: int
    char_id: int
    status: str
    message: str




class LearnedSkillResponse(BaseModel):
    skill_id: int
    skill_name: str
    skill_level: float
    description: Optional[str] = None


class BattleRewardResponse(BaseModel):
    exp: int = 0
    items: list[QuestRewardItemResponse] = []
    level_ups: list[int] = []
    learned_skills: list[LearnedSkillResponse] = []


# ==========================================
# NPC Schemas
# ==========================================

class VillagerResponse(BaseModel):
    villager_id: int
    name: str
    role: str
    description: Optional[str] = None


# ==========================================
# Encounter / Battle Schemas
# ==========================================

class SkillOptionResponse(BaseModel):
    skill_id: int
    skill_name: str
    description: Optional[str] = None
    skill_level: float
    mp_cost: int
    cooldown_sec: int


class EncounterResponse(BaseModel):
    encounter_id: int
    quest_id: int
    quest_name: str
    monster_actor_id: int
    monster_name: str
    monster_current_hp: int
    monster_max_hp: int
    status: str
    turn_count: int
    skills: list[SkillOptionResponse] = []


class AttackRequest(BaseModel):
    skill_id: int


class AttackResponse(BaseModel):
    encounter_id: int
    quest_id: int
    quest_name: str
    monster_name: str
    skill_name: str
    damage: int
    monster_current_hp: int
    monster_max_hp: int
    monster_dead: bool
    quest_status: str
    current_step: int
    required_count: int
    reward: BattleRewardResponse
    message: str


class BattleLogResponse(BaseModel):
    id: int
    char_id: int
    character_name: str
    quest_id: Optional[int] = None
    quest_name: Optional[str] = None
    monster_actor_id: Optional[int] = None
    monster_name: Optional[str] = None
    result: str
    gained_exp: int
    message: Optional[str] = None
    battle_time: Optional[str] = None
