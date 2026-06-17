import uvicorn
from fastapi import FastAPI

from routers import (
    auth_router,
    users,
    characters,
    active_character,
    items,
    quests,
    villagers,
    encounters,
    logs,
    consumables,
)

app = FastAPI(
    title="MyRPG Game Server API",
    description="User, Character, Item, Quest, NPC, Encounter 관리 API"
)

app.include_router(auth_router.router)
app.include_router(users.router)
app.include_router(characters.router)
app.include_router(active_character.router)
app.include_router(items.router)
app.include_router(quests.router)
app.include_router(villagers.router)
app.include_router(encounters.router)
app.include_router(logs.router)
app.include_router(consumables.router)


@app.get("/")
def root():
    return {"message": "MyRPG Game Server API is running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
