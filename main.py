import uuid
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Response, Cookie, status
from sqlalchemy import create_engine, Column, String, Integer, Boolean, ForeignKey, Text, text, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
from typing import List, Optional

# ==========================================
# 1. Database & PyMySQL Setup
# ==========================================
# 실제 MySQL 계정 정보에 맞게 수정해주세요 (rpg/rpg)
DATABASE_URL = "mysql+pymysql://rpg:rpg@localhost:3306/MyRPG"

# 동기식 Engine 생성
engine = create_engine(DATABASE_URL, echo=True) # echo=True로 두면 콘솔에서 SQL 로그 확인 가능
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DB 세션 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

session_store = {}

# ==========================================
# 2. SQLAlchemy ORM Models (MyRPG Schema 적용)
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

# ==========================================
# 3. Pydantic Schemas (API 입출력 검증용)
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
        orm_mode = False  # SQLAlchemy 객체를 Pydantic으로 자동 변환

class UserDeletionResponse(BaseModel):
    user_id: str

class CharacterCreate(BaseModel):
    character_name: str
    race: str   # 추가

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
#추가 
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
# 4. FastAPI Application & REST APIs
# ==========================================
app = FastAPI(title="MyRPG Game Server API", description="User, Character, Item 관리 API")

def get_current_user(session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if not session_id:
        return None
    return session_store.get(session_id)

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
        stat_values[base_stat.stat_type] = stat_values.get(base_stat.stat_type, 0) + base_stat.value

    # 종족 보너스 적용
    specimen_stats = db.query(SpecimenBaseStatModel).filter(
        SpecimenBaseStatModel.specimen_type == race
    ).all()

    for specimen_stat in specimen_stats:
        stat_values[specimen_stat.stat_type] = stat_values.get(specimen_stat.stat_type, 0) + specimen_stat.value

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
    
    
# ----- [ User API ] -----
@app.post("/login", tags=["Auth"])
def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    if current_user:
        return { "message": "이미 로그인한 사용자입니다.", "user_id": current_user.get('id') }
    
    user = db.query(UserModel).filter(UserModel.id == login_data.user_id).first()
    if not user or user.password != login_data.password:
        raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail="사용자 아이디 또는 비밀번호가 다릅니다."
        )
    characters = []
    new_session_id = str(uuid.uuid4())
    session_store[new_session_id] = { "id": user.id, "name": user.user_name, "characters": characters}
    response.set_cookie(
        key = "session_id",
        value = new_session_id,
        httponly = True, max_age = 3600, samesite="lax"
    )
    return {"message": f"{user.user_name}님, 로그인 성공"}

@app.post("/logout", tags=["Auth"])
def logout(response : Response, session_id: str | None = Cookie(default=None)):
    if session_id and session_id in session_store:
        del session_store[session_id]
    response.delete_cookie( key="session_id")
    return {"message": "로그아웃 성공"}

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user.user_identifier).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 유저 ID입니다.")
    
    new_user = UserModel(id=user.user_identifier, user_name=user.nickname, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    res_user = UserResponse(user_id = new_user.id, name=new_user.user_name)
    return res_user

@app.get("/users", response_model=List[UserResponse], tags=["Users"])
def get_users(skip: int = 2, limit: int = 1, db: Session = Depends(get_db)):
    sql = text("SELECT id, user_name FROM User LIMIT :limit OFFSET :skip")
    users = db.execute(sql, { "skip": skip, "limit": limit}).all()
    
    #users = db.query(UserModel).offset(skip).limit(limit).all()
    
    res_users = [ UserResponse(user_id=user.id, name=user.user_name) for user in users ]
    
    return res_users

@app.delete("/users/me", response_model=UserDeletionResponse, tags=["Users"])
def delete_user(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인하지 않은 사용자는 자신을 삭제할 수 없습니다."
        )
    try:
        user_id = current_user.get("id")
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            return UserDeletionResponse(user_id="존재하지 않는 사용자입니다.")
        
        # 1. 무결성 보장: 해당 유저의 모든 캐릭터 목록 조회
        characters = db.query(CharacterModel).filter(CharacterModel.user_id == user_id).all()
        
        # 2. 역순 삭제: 자식 테이블(Character) 삭제 후 부모 테이블(Actor) 삭제
        for char in characters:
            actor_id = char.actor_id

            # Character 삭제 → 나머지는 DB가 자동 처리
            db.delete(char)
            db.flush()

            # Actor만 수동 삭제 (이건 CASCADE 안 걸려 있음)
            db.query(ActorModel).filter(ActorModel.id == actor_id).delete()
            
        # 3. 자식 데이터들이 모두 지워졌으므로 최종적으로 유저(User) 삭제
        db.delete(user)
        
        # 4. 트랜잭션 완료 (전체 일괄 적용)
        db.commit()
        return UserDeletionResponse(user_id=user_id)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"유저 삭제 중 오류가 발생하여 롤백되었습니다: {str(e)}"
        )
   

# ----- [ Character API ] -----
@app.post("/users/{user_id}/characters", response_model=CharacterResponse, status_code=status.HTTP_201_CREATED, tags=["Characters"])
def create_character(user_id: str, char_data: CharacterCreate, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")

    try:
        # 1. Actor 생성
        new_actor = ActorModel()
        db.add(new_actor)
        db.flush()

        # 2. Character 생성
        new_character = CharacterModel(
            actor_id=new_actor.id,
            user_id=user_id,
            character_name=char_data.character_name
        )
        db.add(new_character)
        db.flush()

        # 3. 종족 선택 처리
        specimen = db.query(SpecimenModel).filter(
            SpecimenModel.type == char_data.race
        ).first()

        if not specimen:
            raise HTTPException(status_code=400, detail="존재하지 않는 종족입니다.")

        char_specimen = CharacterSpecimenModel(
            char_id=new_actor.id,
            type=specimen.type,
            fraction=1.0
        )
        db.add(char_specimen)

        # 4. 초보자 직업 자동 부여
        beginner_job = db.query(JobModel).filter(
            JobModel.type == "NOVICE"
        ).first()

        if not beginner_job:
            raise HTTPException(status_code=500, detail="기본 직업이 존재하지 않습니다.")

        char_job = CharacterJobModel(
            char_id=new_actor.id,
            type=beginner_job.type,
            active=True
        )
        db.add(char_job)

        # 5. 기본 스탯 / 인벤토리 / 아이템 / 스킬 자동 생성
        initialize_character_defaults(
            db=db,
            actor_id=new_actor.id,
            race=specimen.type
        )

        db.commit()
        db.refresh(new_character)

        return new_character

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"캐릭터 생성 실패: {str(e)}")

@app.get("/users/{user_id}/characters", response_model=List[CharacterResponse], tags=["Characters"])
def get_user_characters(user_id: str, db: Session = Depends(get_db)):
    characters = db.query(CharacterModel).filter(CharacterModel.user_id == user_id).all()
    return characters

@app.patch("/users/{user_id}/characters/{actor_id}/activate", tags=["Characters"])
def activate_character(
    user_id: str,
    actor_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 후 캐릭터를 활성화할 수 있습니다."
        )

    # 2. 본인 계정 확인
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 캐릭터는 활성화할 수 없습니다."
        )

    # 3. 활성화할 캐릭터가 실제로 존재하는지 확인
    character = db.query(CharacterModel).filter(
        CharacterModel.actor_id == actor_id,
        CharacterModel.user_id == user_id
    ).first()

    if not character:
        raise HTTPException(
            status_code=404,
            detail="활성화할 캐릭터를 찾을 수 없습니다."
        )

    try:
        # 4. 해당 유저의 모든 캐릭터 비활성화
        db.query(CharacterModel).filter(
            CharacterModel.user_id == user_id
        ).update({"active": False})

        # 5. 선택한 캐릭터만 활성화
        character.active = True

        db.commit()

        return {
            "message": "대표 캐릭터로 활성화되었습니다.",
            "actor_id": character.actor_id,
            "character_name": character.character_name
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 활성화 중 오류가 발생하여 롤백되었습니다: {str(e)}"
        )

@app.get("/users/{user_id}/active-character")
def get_active_character(
    user_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 후 이용할 수 있습니다."
        )

    # 2. 본인 계정 확인
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 캐릭터 정보는 조회할 수 없습니다."
        )

    # 3. 활성 캐릭터 조회
    character = db.query(CharacterModel).filter(
        CharacterModel.user_id == user_id,
        CharacterModel.active == True
    ).first()

    if not character:
        return None

    # 4. 종족 조회
    specimen_rows = db.execute(
        text("""
            SELECT 
                cs.type AS race_type,
                s.name AS race_name,
                cs.fraction AS fraction
            FROM CharacterSpecimen cs
            JOIN Specimen s ON cs.type = s.type
            WHERE cs.char_id = :char_id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    races = [
        {
            "type": row["race_type"],
            "name": row["race_name"],
            "fraction": float(row["fraction"])
        }
        for row in specimen_rows
    ]

    if races:
        race_label = " / ".join([f"{r['name']}({r['type']})" for r in races])
    else:
        race_label = None

    # 5. 활성 직업 조회
    job_row = db.execute(
        text("""
            SELECT 
                cj.type AS job_type,
                j.name AS job_name,
                j.description AS job_description
            FROM CharacterJob cj
            JOIN Job j ON cj.type = j.type
            WHERE cj.char_id = :char_id
              AND cj.active = TRUE
            LIMIT 1
        """),
        {"char_id": character.actor_id}
    ).mappings().first()

    # 6. 스탯 조회
    stat_rows = db.execute(
        text("""
            SELECT 
                ast.stat_type AS stat_type,
                s.name AS stat_name,
                s.description AS description,
                ast.value AS value
            FROM ActorStat ast
            JOIN Stat s ON ast.stat_type = s.type
            WHERE ast.actor_id = :actor_id
            ORDER BY ast.stat_type
        """),
        {"actor_id": character.actor_id}
    ).mappings().all()

    stats = [
        {
            "stat_type": row["stat_type"],
            "stat_name": row["stat_name"],
            "description": row["description"],
            "value": row["value"]
        }
        for row in stat_rows
    ]

    # 7. 스킬 조회
    skill_rows = db.execute(
        text("""
            SELECT
                s.id AS skill_id,
                s.name AS skill_name,
                s.description AS description,
                s.mp_cost AS mp_cost,
                s.cooldown_sec AS cooldown_sec,
                cs.skill_level AS skill_level
            FROM CharacterSkill cs
            JOIN Skill s ON cs.skill_id = s.id
            WHERE cs.char_id = :char_id
            ORDER BY s.id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    skills = [
        {
            "skill_id": row["skill_id"],
            "skill_name": row["skill_name"],
            "description": row["description"],
            "mp_cost": row["mp_cost"],
            "cooldown_sec": row["cooldown_sec"],
            "skill_level": float(row["skill_level"])
        }
        for row in skill_rows
    ]

    # 8. 인벤토리 조회
    inventory_rows = db.execute(
        text("""
            SELECT
                inv.id AS inventory_id,
                inv.type AS inventory_type,
                inv.capacity AS capacity,
                i.id AS item_id,
                i.name AS item_name,
                i.description AS item_description,
                i.type AS item_type,
                i.sub_type AS item_sub_type,
                ii.quantity AS quantity
            FROM Inventory inv
            JOIN InventoryItem ii ON inv.id = ii.inventory_id
            JOIN Item i ON ii.item_id = i.id
            WHERE inv.owner_id = :char_id
            ORDER BY inv.id, i.id
        """),
        {"char_id": character.actor_id}
    ).mappings().all()

    inventory = [
        {
            "inventory_id": row["inventory_id"],
            "inventory_type": row["inventory_type"],
            "capacity": row["capacity"],
            "item_id": row["item_id"],
            "item_name": row["item_name"],
            "description": row["item_description"],
            "item_type": row["item_type"],
            "item_sub_type": row["item_sub_type"],
            "quantity": row["quantity"]
        }
        for row in inventory_rows
    ]

    return {
        "actor_id": character.actor_id,
        "character_name": character.character_name,
        "level": character.level,
        "exp": character.exp,
        "race": race_label,
        "races": races,
        "job": job_row["job_type"] if job_row else None,
        "job_name": job_row["job_name"] if job_row else None,
        "stats": stats,
        "skills": skills,
        "inventory": inventory
    }

@app.delete(
    "/users/{user_id}/characters/{actor_id}",
    response_model=CharacterDeletionResponse,
    tags=["Characters"]
)
def delete_character(
    user_id: str,
    actor_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. 로그인 확인
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인하지 않은 사용자는 캐릭터를 삭제할 수 없습니다."
        )

    # 2. 본인 계정인지 확인
    if current_user.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="다른 사용자의 캐릭터는 삭제할 수 없습니다."
        )

    # 3. 삭제할 캐릭터 조회
    character = db.query(CharacterModel).filter(
        CharacterModel.actor_id == actor_id,
        CharacterModel.user_id == user_id
    ).first()

    if not character:
        raise HTTPException(
            status_code=404,
            detail="삭제할 캐릭터를 찾을 수 없습니다."
        )

    deleted_name = character.character_name

    try:
        # 4. Character 삭제
        # CharacterSpecimen, CharacterJob 등은 DB의 ON DELETE CASCADE로 함께 삭제됨
        db.delete(character)
        db.flush()

        # 5. Actor 삭제
        db.query(ActorModel).filter(
            ActorModel.id == actor_id
        ).delete()

        db.commit()

        return CharacterDeletionResponse(
            actor_id=actor_id,
            character_name=deleted_name,
            message="캐릭터 삭제 완료"
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"캐릭터 삭제 중 오류가 발생하여 롤백되었습니다: {str(e)}"
        )

# ----- [ Item API ] -----
@app.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED, tags=["Items"])
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = ItemModel(**item.dict())
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@app.get("/items", response_model=List[ItemResponse], tags=["Items"])
def get_items(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    items = db.query(ItemModel).offset(skip).limit(limit).all()
    return items

# ==========================================
# 5. Uvicorn Server Execution
# ==========================================
if __name__ == "__main__":
    # 파이썬 스크립트 직접 실행 시 Uvicorn 서버 구동
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)