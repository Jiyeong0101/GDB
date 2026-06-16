import uvicorn
from fastapi import FastAPI

from routers import auth_router, users, characters, active_character, items, quests

# ==========================================
# FastAPI Application
# ==========================================
app = FastAPI(
    title="MyRPG Game Server API",
    description="User, Character, Item 관리 API"
)

# 기능별 Router 등록
app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(characters.router)
app.include_router(active_character.router)
app.include_router(items.router)
app.include_router(quests.router)

@app.get("/")
def root():
    return {"message": "MyRPG Game Server API is running"}


if __name__ == "__main__":
    # server 폴더 안에서 실행:
    # python main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
