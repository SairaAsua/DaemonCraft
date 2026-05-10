"""
Gate definitions: 64 gates mapped to zodiac degrees.

The Rave Mandala maps 64 hexagrams (gates) onto 360° of the ecliptic.
Each gate occupies 360/64 = 5.625°, each line = 5.625/6 = 0.9375°.
Gate sequence starts at 28°15' Aquarius (= 328.25° ecliptic) — Gate 41.

Source: SharpAstrology.HumanDesign + Jovian Archive reference data.
"""

# The HD wheel starts at this ecliptic degree.
# 358°15' (28°15' Pisces) = first degree of Gate 25 in the Rave Mandala.
# Verified against humdes.com and multiple reference charts.
HD_START_DEGREE = 358.25

# Gate sequence around the Rave Mandala starting from HD_START_DEGREE.
# Source: Jovian Archive / barneyandflow.com/gate-zodiac-degrees
GATE_SEQUENCE = [
    25, 17, 21, 51, 42, 3,   27, 24,  # Aries → Taurus
    2,  23, 8,  20, 16, 35,  45, 12,  # Taurus → Gemini
    15, 52, 39, 53, 62, 56,  31, 33,  # Gemini → Cancer
    7,  4,  29, 59, 40, 64,  47, 6,   # Cancer → Leo
    46, 18, 48, 57, 32, 50,  28, 44,  # Virgo → Libra
    1,  43, 14, 34, 9,  5,   26, 11,  # Scorpio → Sagittarius
    10, 58, 38, 54, 61, 60,  41, 19,  # Capricorn → Aquarius
    13, 49, 30, 55, 37, 63,  22, 36,  # Aquarius → Pisces
]

assert len(GATE_SEQUENCE) == 64, f"Expected 64 gates, got {len(GATE_SEQUENCE)}"

GATE_SIZE = 360.0 / 64  # 5.625°
LINE_SIZE = GATE_SIZE / 6  # 0.9375°
COLOR_SIZE = LINE_SIZE / 6  # 0.15625°
TONE_SIZE = COLOR_SIZE / 6  # ~0.02604°
BASE_SIZE = TONE_SIZE / 5  # ~0.005208°

# Gate names (I Ching)
GATE_NAMES = {
    1: "The Creative", 2: "The Receptive", 3: "Ordering",
    4: "Formulization", 5: "Fixed Rhythms", 6: "Friction",
    7: "The Role of the Self", 8: "Holding Together", 9: "Focus",
    10: "Behavior of the Self", 11: "Ideas", 12: "Caution",
    13: "The Listener", 14: "Power Skills", 15: "Extremes",
    16: "Skills", 17: "Opinion", 18: "Correction",
    19: "Wanting", 20: "The Now", 21: "The Hunter/Huntress",
    22: "Openness", 23: "Assimilation", 24: "Rationalization",
    25: "Spirit of the Self", 26: "The Egoist", 27: "Caring",
    28: "The Game Player", 29: "Saying Yes", 30: "Feelings",
    31: "Influence", 32: "Continuity", 33: "Privacy",
    34: "Power", 35: "Change", 36: "Crisis",
    37: "Friendship", 38: "The Fighter", 39: "Provocation",
    40: "Aloneness", 41: "Contraction", 42: "Growth",
    43: "Insight", 44: "Coming to Meet", 45: "Gathering Together",
    46: "Pushing Upward", 47: "Realization", 48: "Depth",
    49: "Principles", 50: "Values", 51: "Shock",
    52: "Stillness", 53: "Development", 54: "Ambition",
    55: "Spirit", 56: "Stimulation", 57: "Intuitive Clarity",
    58: "Vitality", 59: "Sexuality", 60: "Limitation",
    61: "Mystery", 62: "Detail", 63: "Doubt", 64: "Confusion",
}

GATE_NAMES_RU = {
    1: "Творчество", 2: "Восприимчивость", 3: "Упорядочивание",
    4: "Формулирование", 5: "Фиксированные ритмы", 6: "Трение",
    7: "Роль Я", 8: "Единение", 9: "Фокусировка",
    10: "Поведение Я", 11: "Идеи", 12: "Осторожность",
    13: "Слушатель", 14: "Мастерство Силы", 15: "Крайности",
    16: "Мастерство", 17: "Мнение", 18: "Коррекция",
    19: "Желание", 20: "Настоящее", 21: "Охотник/Охотница",
    22: "Открытость", 23: "Ассимиляция", 24: "Рационализация",
    25: "Дух Я", 26: "Эгоист", 27: "Забота",
    28: "Игрок", 29: "Согласие", 30: "Чувства",
    31: "Влияние", 32: "Непрерывность", 33: "Уединение",
    34: "Сила", 35: "Перемены", 36: "Кризис",
    37: "Дружба", 38: "Борец", 39: "Провокация",
    40: "Одиночество", 41: "Сжатие", 42: "Рост",
    43: "Прозрение", 44: "Встреча", 45: "Собирание вместе",
    46: "Продвижение вверх", 47: "Осознание", 48: "Глубина",
    49: "Принципы", 50: "Ценности", 51: "Шок",
    52: "Неподвижность", 53: "Развитие", 54: "Амбиция",
    55: "Дух", 56: "Стимуляция", 57: "Интуитивная ясность",
    58: "Жизненность", 59: "Сексуальность", 60: "Ограничение",
    61: "Тайна", 62: "Деталь", 63: "Сомнение", 64: "Путаница",
}


def degree_to_gate_line(degree: float) -> tuple[int, int]:
    """Convert ecliptic longitude to HD gate number and line number (1-6)."""
    adjusted = (degree - HD_START_DEGREE) % 360
    index = int(adjusted / GATE_SIZE)
    gate = GATE_SEQUENCE[index]
    remainder = adjusted % GATE_SIZE
    line = int(remainder / LINE_SIZE) + 1
    line = min(line, 6)  # safety clamp
    return gate, line


def degree_to_full_activation(degree: float) -> dict:
    """Convert ecliptic longitude to gate, line, color, tone, base."""
    adjusted = (degree - HD_START_DEGREE) % 360
    index = int(adjusted / GATE_SIZE)
    gate = GATE_SEQUENCE[index]
    remainder = adjusted % GATE_SIZE

    line = int(remainder / LINE_SIZE) + 1
    line = min(line, 6)
    line_remainder = remainder % LINE_SIZE

    color = int(line_remainder / COLOR_SIZE) + 1
    color = min(color, 6)
    color_remainder = line_remainder % COLOR_SIZE

    tone = int(color_remainder / TONE_SIZE) + 1
    tone = min(tone, 6)
    tone_remainder = color_remainder % TONE_SIZE

    base = int(tone_remainder / BASE_SIZE) + 1
    base = min(base, 5)

    return {
        "gate": gate,
        "line": line,
        "color": color,
        "tone": tone,
        "base": base,
    }
