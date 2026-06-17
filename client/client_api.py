import requests

BASE_URL = "http://localhost:8000"


# ==========================================
# Auth API
# ==========================================

def login(user_id: str, password: str):
    return requests.post(
        f"{BASE_URL}/login",
        json={"user_id": user_id, "password": password}
    )


def logout(cookies):
    return requests.post(f"{BASE_URL}/logout", cookies=cookies)


# ==========================================
# User API
# ==========================================

def create_user(user_identifier: str, nickname: str, password: str):
    return requests.post(
        f"{BASE_URL}/users",
        json={
            "user_identifier": user_identifier,
            "nickname": nickname,
            "password": password
        }
    )


def delete_current_user(cookies):
    return requests.delete(f"{BASE_URL}/users/me", cookies=cookies)


# ==========================================
# Character API
# ==========================================

def get_characters(user_id: str, cookies):
    return requests.get(f"{BASE_URL}/users/{user_id}/characters", cookies=cookies)


def create_character(user_id: str, character_name: str, race: str, cookies):
    return requests.post(
        f"{BASE_URL}/users/{user_id}/characters",
        json={"character_name": character_name, "race": race},
        cookies=cookies
    )


def activate_character(user_id: str, actor_id: int, cookies):
    return requests.patch(
        f"{BASE_URL}/users/{user_id}/characters/{actor_id}/activate",
        cookies=cookies
    )


def delete_character(user_id: str, actor_id: int, cookies):
    return requests.delete(
        f"{BASE_URL}/users/{user_id}/characters/{actor_id}",
        cookies=cookies
    )


def get_active_character(user_id: str, cookies):
    return requests.get(f"{BASE_URL}/users/{user_id}/active-character", cookies=cookies)


# ==========================================
# Quest API
# ==========================================

def get_available_quests(user_id: str, cookies):
    return requests.get(f"{BASE_URL}/users/{user_id}/quests/available", cookies=cookies)


def get_my_quests(user_id: str, cookies):
    return requests.get(f"{BASE_URL}/users/{user_id}/quests/my", cookies=cookies)


def accept_quest(user_id: str, quest_id: int, cookies):
    return requests.post(
        f"{BASE_URL}/users/{user_id}/quests/{quest_id}/accept",
        cookies=cookies
    )


# ==========================================
# Villager / NPC API
# ==========================================

def get_villagers(user_id: str, cookies):
    return requests.get(f"{BASE_URL}/users/{user_id}/villagers", cookies=cookies)


def get_villager_quests(user_id: str, villager_id: int, cookies):
    return requests.get(
        f"{BASE_URL}/users/{user_id}/villagers/{villager_id}/quests",
        cookies=cookies
    )


# ==========================================
# Encounter API
# ==========================================

def start_encounter(user_id: str, quest_id: int, cookies):
    return requests.post(
        f"{BASE_URL}/users/{user_id}/quests/{quest_id}/encounter/start",
        cookies=cookies
    )


def get_encounter(user_id: str, quest_id: int, cookies):
    return requests.get(
        f"{BASE_URL}/users/{user_id}/quests/{quest_id}/encounter",
        cookies=cookies
    )


def attack_encounter(user_id: str, quest_id: int, skill_id: int, cookies):
    return requests.post(
        f"{BASE_URL}/users/{user_id}/quests/{quest_id}/encounter/attack",
        json={"skill_id": skill_id},
        cookies=cookies
    )


# ==========================================
# BattleLog API
# ==========================================

def get_battle_logs(user_id: str, cookies):
    return requests.get(f"{BASE_URL}/users/{user_id}/battle-logs", cookies=cookies)
