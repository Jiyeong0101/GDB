from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Text, Float, DateTime
from database import Base
from sqlalchemy import text


# ==========================================
# SQLAlchemy ORM Models (MyRPG Schema 적용)
# ==========================================

class UserModel(Base):
    __tablename__ = "User"

    id = Column(String(20), primary_key=True)
    user_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)


class ActorModel(Base):
    __tablename__ = "Actor"

    id = Column(Integer, primary_key=True, autoincrement=True)


class CharacterModel(Base):
    __tablename__ = "Character"

    actor_id = Column(Integer, ForeignKey("Actor.id"), primary_key=True)
    user_id = Column(String(20), ForeignKey("User.id"), nullable=False)
    character_name = Column(String(255), nullable=False)
    level = Column(Integer, default=1, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    active = Column(Boolean, default=False, nullable=False)


class ItemModel(Base):
    __tablename__ = "Item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)
    sub_type = Column(String(50))
    capacity = Column(Integer, default=-1)


class SpecimenModel(Base):
    __tablename__ = "Specimen"

    type = Column(String(50), primary_key=True)
    name = Column(String(255))
    description = Column(Text)


class CharacterSpecimenModel(Base):
    __tablename__ = "CharacterSpecimen"

    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    type = Column(String(50), ForeignKey("Specimen.type"), primary_key=True)
    fraction = Column(Float, default=100)


class JobModel(Base):
    __tablename__ = "Job"

    type = Column(String(50), primary_key=True)
    name = Column(String(255))
    description = Column(Text)


class CharacterJobModel(Base):
    __tablename__ = "CharacterJob"

    type = Column(String(50), ForeignKey("Job.type"), primary_key=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    obtain_date = Column(DateTime)
    active = Column(Boolean, default=False)


class StatModel(Base):
    __tablename__ = "Stat"

    type = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)


class ActorStatModel(Base):
    __tablename__ = "ActorStat"

    actor_id = Column(Integer, ForeignKey("Actor.id"), primary_key=True)
    stat_type = Column(String(50), ForeignKey("Stat.type"), primary_key=True)
    value = Column(Integer, nullable=False)


class LevelMasterModel(Base):
    __tablename__ = "LevelMaster"

    level = Column(Integer, primary_key=True)
    max_exp_to_next = Column(Integer, nullable=False)
    max_hp = Column(Integer, nullable=False)
    max_mp = Column(Integer, nullable=False)


class LevelBaseStatModel(Base):
    __tablename__ = "LevelBaseStat"

    char_level = Column(Integer, primary_key=True)
    stat_type = Column(String(50), primary_key=True)
    value = Column(Integer, nullable=False)


class SpecimenBaseStatModel(Base):
    __tablename__ = "SpecimenBaseStat"

    specimen_type = Column(String(50), primary_key=True)
    stat_type = Column(String(50), primary_key=True)
    value = Column(Integer, nullable=False)


class InventoryModel(Base):
    __tablename__ = "Inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(Integer, ForeignKey("Character.actor_id"), nullable=False)
    type = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)


class InventoryItemModel(Base):
    __tablename__ = "InventoryItem"

    inventory_id = Column(Integer, ForeignKey("Inventory.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)


class SkillModel(Base):
    __tablename__ = "Skill"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    mp_cost = Column(Integer, nullable=False, default=0)
    cooldown_sec = Column(Integer, nullable=False, default=0)
    unlock_condition_id = Column(Integer)


class CharacterSkillModel(Base):
    __tablename__ = "CharacterSkill"

    skill_id = Column(Integer, ForeignKey("Skill.id"), primary_key=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    skill_level = Column(Float, nullable=False, default=1.0)

# ==========================================
# Quest / Reward / Monster Models
# ==========================================

class QuestModel(Base):
    __tablename__ = "Quest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unlock_condition_id = Column(Integer)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    max_steps = Column(Integer, default=1)
    type = Column(String(50))
    is_repeatable = Column(Boolean, nullable=False, default=False)


class CharacterQuestModel(Base):
    __tablename__ = "CharacterQuest"

    quest_id = Column(Integer, ForeignKey("Quest.id"), primary_key=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), primary_key=True)
    start_time = Column(DateTime)
    status = Column(String(50), nullable=False)
    current_step = Column(Integer, nullable=False, default=0)


class RewardModel(Base):
    __tablename__ = "Reward"

    id = Column(Integer, primary_key=True, autoincrement=True)
    unlock_condition_id = Column(Integer)


class RewardItemModel(Base):
    __tablename__ = "RewardItem"

    reward_id = Column(Integer, ForeignKey("Reward.id"), primary_key=True)
    item_id = Column(Integer, ForeignKey("Item.id"), primary_key=True)
    quantity = Column(Integer, nullable=False, default=1)
    drop_probability = Column(Float)


class RewardExpModel(Base):
    __tablename__ = "RewardExp"

    reward_id = Column(Integer, ForeignKey("Reward.id"), primary_key=True)
    amount = Column(Integer, nullable=False)


class MonsterModel(Base):
    __tablename__ = "Monster"

    actor_id = Column(Integer, ForeignKey("Actor.id"), primary_key=True)
    hp = Column(Integer, nullable=False)
    atk = Column(Integer, nullable=False)
    def_ = Column("def", Integer, nullable=False)
    drop_reward_id = Column(Integer, ForeignKey("Reward.id"))


class QuestMonsterTargetModel(Base):
    __tablename__ = "QuestMonsterTarget"

    quest_id = Column(Integer, ForeignKey("Quest.id"), primary_key=True)
    monster_actor_id = Column(Integer, ForeignKey("Monster.actor_id"), primary_key=True)
    required_count = Column(Integer, nullable=False, default=1)
    target_name = Column(String(255))


class QuestRewardModel(Base):
    __tablename__ = "QuestReward"

    quest_id = Column(Integer, ForeignKey("Quest.id"), primary_key=True)
    reward_id = Column(Integer, ForeignKey("Reward.id"), primary_key=True)

class BattleLogModel(Base):
    __tablename__ = "BattleLog"

    id = Column(Integer, primary_key=True, autoincrement=True)
    char_id = Column(Integer, ForeignKey("Character.actor_id"), nullable=False)
    quest_id = Column(Integer, ForeignKey("Quest.id"))
    monster_actor_id = Column(Integer, ForeignKey("Monster.actor_id"))
    result = Column(String(50), nullable=False)
    gained_exp = Column(Integer, nullable=False, default=0)
    message = Column(String(255))
    battle_time = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
