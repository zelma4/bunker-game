"""
Логіка раундів та голосувань згідно офіційних правил
"""

# Таблиця голосувань для кожного раунду (5 раундів)
# Ключ = кількість гравців, значення = список голосувань для кожного раунду
ROUNDS_TABLE = {
    4: [
        0,
        1,
        1,
        1,
        1,
    ],  # 4 гравці: раунд 1 без голосування, раунди 2-5 по 1 голосуванню
    5: [0, 1, 1, 1, 1],
    6: [0, 1, 1, 1, 1],
    7: [0, 1, 1, 1, 1],
    8: [0, 1, 1, 2, 1],  # 8 гравців: раунд 4 має 2 голосування
    9: [0, 1, 2, 2, 1],  # 9 гравців: раунди 3-4 по 2 голосування
    10: [0, 2, 2, 2, 1],
    11: [0, 2, 2, 2, 2],
    12: [0, 2, 2, 3, 2],
    13: [0, 2, 3, 3, 2],
    14: [0, 3, 3, 3, 2],
    15: [0, 3, 3, 3, 3],
    16: [0, 3, 3, 4, 3],  # 16 гравців: раунд 4 має 4 голосування
}


def get_votings_for_round(player_count: int, round_num: int) -> int:
    """
    Отримати кількість голосувань для конкретного раунду

    Args:
        player_count: кількість гравців
        round_num: номер раунду (1-5)

    Returns:
        кількість голосувань у раунді
    """
    if player_count < 4 or player_count > 16:
        raise ValueError(
            f"Invalid player count: {player_count}. Must be between 4 and 16"
        )

    if round_num < 1 or round_num > 5:
        raise ValueError(f"Invalid round number: {round_num}. Must be between 1 and 5")

    return ROUNDS_TABLE[player_count][round_num]


def get_total_eliminations(player_count: int) -> int:
    """
    Отримати загальну кількість вигнаних гравців за всю гру

    Args:
        player_count: початкова кількість гравців

    Returns:
        кількість гравців, що будуть вигнані
    """
    if player_count < 4 or player_count > 16:
        raise ValueError(f"Invalid player count: {player_count}")

    return sum(ROUNDS_TABLE[player_count])


def get_bunker_capacity(player_count: int) -> int:
    """
    Отримати місткість бункера (половина від початкової кількості)

    Args:
        player_count: початкова кількість гравців

    Returns:
        кількість місць у бункері
    """
    return player_count - get_total_eliminations(player_count)


def should_round_have_voting(player_count: int, round_num: int) -> bool:
    """
    Перевірити, чи повинен бути раунд з голосуванням

    Args:
        player_count: кількість гравців
        round_num: номер раунду

    Returns:
        True якщо раунд має голосування
    """
    return get_votings_for_round(player_count, round_num) > 0


# Фази раунду
ROUND_PHASES = [
    "bunker_reveal",  # Відкривання картки бункера
    "card_reveal",  # Відкривання карток гравців (по черзі, 30 сек на гравця)
    "discussion",  # Обговорення (1 хв)
    "voting",  # Голосування
    "reveal",  # Підрахунок та вигнання
]


# Тривалість фаз (в секундах)
PHASE_DURATIONS = {
    "bunker_reveal": 10,  # 10 сек на показ картки бункера
    "card_reveal_per_player": 60,  # 60 сек (1 хвилина) на гравця для відкривання картки
    "discussion": 60,  # 1 хв обговорення
    "voting": 60,  # 1 хв на голосування
    "reveal": 10,  # 10 сек на показ результатів
    "survival_check": 30,  # 30 сек на перевірку виживання
}


def get_phase_duration(phase: str, player_count: int = 0) -> int:
    """
    Отримати тривалість фази

    Args:
        phase: назва фази
        player_count: кількість гравців (для card_reveal)

    Returns:
        тривалість в секундах
    """
    if phase == "card_reveal":
        return PHASE_DURATIONS["card_reveal_per_player"] * player_count

    return PHASE_DURATIONS.get(phase, 60)


# Обов'язкове відкривання професії у першому раунді
MANDATORY_FIRST_ROUND_CARD = "profession"


def get_mandatory_card_for_round(round_num: int) -> str:
    """
    Отримати обов'язкову картку для раунду

    Args:
        round_num: номер раунду (1-5)

    Returns:
        тип картки або None
    """
    if round_num == 1:
        return MANDATORY_FIRST_ROUND_CARD
    return None
