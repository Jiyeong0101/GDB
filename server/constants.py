"""
프로젝트에서 반복해서 사용하는 고정 ID와 설정값을 모아둔 파일입니다.

"""

# Quest
TUTORIAL_QUEST_ID = 100

# Inventory / Item
MAIN_BAG_TYPE = "MAIN_BAG"
DEFAULT_BAG_ITEM_ID = 13
DEFAULT_BAG_CAPACITY = 20
MANA_POTION_ITEM_ID = 7
MANA_POTION_DEFAULT_RECOVER = 30

# Skill / Battle
DEFAULT_SKILL_DAMAGE_BONUS = 5
SKILL_DAMAGE_BONUS = {
    1: 5,    # 기본 베기
    2: 12,   # 연속 베기
    3: 18,   # 분노의 일격
    5: 16,   # 파이어볼
    7: 10,   # 돌진
}
