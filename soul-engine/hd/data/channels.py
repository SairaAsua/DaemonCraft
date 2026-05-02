"""
Channel definitions: 36 channels connecting pairs of gates.

Each channel connects two centers and has a name and circuit affiliation.
Source: SharpAstrology.HumanDesign + Jovian Archive.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Channel:
    gate1: int
    gate2: int
    name: str
    name_ru: str
    center1: str
    center2: str
    circuit: str  # Individual, Collective, Tribal, Integration


# All 36 channels
CHANNELS: list[Channel] = [
    # --- Integration Circuit (4 channels) ---
    Channel(10, 20, "Awakening", "Пробуждение", "Self", "Throat", "Integration"),
    Channel(20, 34, "Charisma", "Харизма", "Throat", "Sacral", "Integration"),
    Channel(20, 57, "The Brainwave", "Мозговая волна", "Throat", "Spleen", "Integration"),
    Channel(34, 57, "Power", "Сила", "Sacral", "Spleen", "Integration"),
    Channel(10, 57, "Perfected Form", "Совершенной формы", "Self", "Spleen", "Integration"),
    # --- Individual Circuit: Knowing ---
    Channel(1, 8, "Inspiration", "Вдохновение", "Self", "Throat", "Individual"),
    Channel(23, 43, "Structuring", "Структурирование", "Throat", "Ajna", "Individual"),
    Channel(24, 61, "Awareness", "Осознанность", "Ajna", "Head", "Individual"),
    Channel(25, 51, "Initiation", "Инициация", "Self", "Heart", "Individual"),
    Channel(2, 14, "The Beat", "Ритм", "Self", "Sacral", "Individual"),
    Channel(3, 60, "Mutation", "Мутация", "Sacral", "Root", "Individual"),
    Channel(28, 38, "Struggle", "Борьба", "Spleen", "Root", "Individual"),
    Channel(39, 55, "Emoting", "Эмоциональность", "Root", "Solar Plexus", "Individual"),
    Channel(12, 22, "Openness", "Открытость", "Throat", "Solar Plexus", "Individual"),
    # --- Individual Circuit: Centering ---
    Channel(10, 34, "Exploration", "Исследование", "Self", "Sacral", "Individual"),  # Note: 10-34 via Integration
    # --- Collective Circuit: Logic ---
    Channel(4, 63, "Logic", "Логика", "Ajna", "Head", "Collective"),
    Channel(7, 31, "The Alpha", "Альфа", "Self", "Throat", "Collective"),
    Channel(9, 52, "Concentration", "Концентрация", "Sacral", "Root", "Collective"),
    Channel(5, 15, "Rhythm", "Ритм", "Sacral", "Self", "Collective"),
    Channel(16, 48, "The Wavelength", "Волна", "Throat", "Spleen", "Collective"),
    Channel(17, 62, "Acceptance", "Принятие", "Ajna", "Throat", "Collective"),
    Channel(18, 58, "Judgment", "Суждение", "Spleen", "Root", "Collective"),
    Channel(47, 64, "Abstraction", "Абстракция", "Ajna", "Head", "Collective"),
    Channel(11, 56, "Curiosity", "Любопытство", "Ajna", "Throat", "Collective"),
    Channel(13, 33, "The Prodigal", "Блудный сын", "Self", "Throat", "Collective"),
    Channel(29, 46, "Discovery", "Открытие", "Sacral", "Self", "Collective"),
    Channel(30, 41, "Recognition", "Признание", "Solar Plexus", "Root", "Collective"),
    Channel(35, 36, "Transitoriness", "Бренность", "Throat", "Solar Plexus", "Collective"),
    Channel(42, 53, "Maturation", "Созревание", "Sacral", "Root", "Collective"),
    # --- Tribal Circuit ---
    Channel(6, 59, "Intimacy", "Близость", "Solar Plexus", "Sacral", "Tribal"),
    Channel(19, 49, "Synthesis", "Синтез", "Root", "Solar Plexus", "Tribal"),
    Channel(21, 45, "Money", "Деньги", "Heart", "Throat", "Tribal"),
    Channel(26, 44, "Surrender", "Сдача", "Heart", "Spleen", "Tribal"),
    Channel(27, 50, "Preservation", "Сохранение", "Sacral", "Spleen", "Tribal"),
    Channel(32, 54, "Transformation", "Трансформация", "Spleen", "Root", "Tribal"),
    Channel(37, 40, "Community", "Сообщество", "Solar Plexus", "Heart", "Tribal"),
]

# Quick lookup: frozenset({gate1, gate2}) -> Channel
CHANNEL_BY_GATES: dict[frozenset[int], Channel] = {
    frozenset({ch.gate1, ch.gate2}): ch for ch in CHANNELS
}


def find_active_channels(active_gates: set[int]) -> list[Channel]:
    """Return list of channels formed by the given active gates."""
    result = []
    for ch in CHANNELS:
        if ch.gate1 in active_gates and ch.gate2 in active_gates:
            result.append(ch)
    return result
