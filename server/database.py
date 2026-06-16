from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 실제 MySQL 계정 정보에 맞게 수정해주세요 (rpg/rpg)
DATABASE_URL = "mysql+pymysql://rpg:rpg@localhost:3306/MyRPG"

# echo=True로 두면 콘솔에서 SQL 로그 확인 가능
engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# DB 세션 의존성 주입 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
