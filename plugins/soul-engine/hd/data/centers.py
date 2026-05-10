"""
Center definitions: 9 bodygraph centers and their gates.

Source: SharpAstrology.HumanDesign / Jovian Archive.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Center:
    name: str
    name_ru: str
    gates: frozenset[int]
    is_motor: bool
    is_awareness: bool
    is_pressure: bool


CENTERS: dict[str, Center] = {
    "Head": Center(
        name="Head", name_ru="Голова",
        gates=frozenset({61, 63, 64}),
        is_motor=False, is_awareness=False, is_pressure=True,
    ),
    "Ajna": Center(
        name="Ajna", name_ru="Аджна",
        gates=frozenset({4, 11, 17, 24, 43, 47}),
        is_motor=False, is_awareness=True, is_pressure=False,
    ),
    "Throat": Center(
        name="Throat", name_ru="Горло",
        gates=frozenset({8, 12, 16, 20, 23, 31, 33, 35, 45, 56, 62}),
        is_motor=False, is_awareness=False, is_pressure=False,
    ),
    "Self": Center(
        name="Self", name_ru="G-центр",
        gates=frozenset({1, 2, 7, 10, 13, 15, 25, 46}),
        is_motor=False, is_awareness=False, is_pressure=False,
    ),
    "Heart": Center(
        name="Heart", name_ru="Сердце (Эго)",
        gates=frozenset({21, 26, 40, 51}),
        is_motor=True, is_awareness=False, is_pressure=False,
    ),
    "Sacral": Center(
        name="Sacral", name_ru="Сакрал",
        gates=frozenset({3, 5, 9, 14, 27, 29, 34, 42, 59}),
        is_motor=True, is_awareness=False, is_pressure=False,
    ),
    "Spleen": Center(
        name="Spleen", name_ru="Селезёнка",
        gates=frozenset({18, 28, 32, 44, 48, 50, 57}),
        is_motor=False, is_awareness=True, is_pressure=False,
    ),
    "Solar Plexus": Center(
        name="Solar Plexus", name_ru="Солнечное сплетение",
        gates=frozenset({6, 22, 30, 36, 37, 49, 55}),
        is_motor=True, is_awareness=True, is_pressure=False,
    ),
    "Root": Center(
        name="Root", name_ru="Корень",
        gates=frozenset({19, 28, 38, 39, 41, 52, 53, 54, 58, 60}),
        is_motor=True, is_awareness=False, is_pressure=True,
    ),
}


def gate_to_center(gate: int) -> str | None:
    """Return center name for a given gate, or None if not found."""
    for name, center in CENTERS.items():
        if gate in center.gates:
            return name
    return None
