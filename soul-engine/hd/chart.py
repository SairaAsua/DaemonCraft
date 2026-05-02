"""
Human Design chart calculation engine.

Ported from SharpAstrology.HumanDesign (MIT) + human-design-py (MIT).
Calculates: type, profile, authority, strategy, centers, channels, gates,
incarnation cross, variables, definition splits.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

import swisseph as swe

from hd.data.gates import (
    degree_to_gate_line,
    degree_to_full_activation,
    GATE_NAMES,
    GATE_NAMES_RU,
    HD_START_DEGREE,
    GATE_SIZE,
)
from hd.data.channels import Channel, CHANNELS, find_active_channels, CHANNEL_BY_GATES
from hd.data.centers import CENTERS, gate_to_center

# Use built-in Moshier ephemeris (no external files needed, ±1 arcsec accuracy)
swe.set_ephe_path("")

# Planets used in Human Design
HD_PLANETS = {
    "Sun": swe.SUN,
    "Earth": None,        # Sun + 180°
    "Moon": swe.MOON,
    "North Node": swe.TRUE_NODE,
    "South Node": None,   # North Node + 180°
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
}

HD_PLANETS_RU = {
    "Sun": "Солнце", "Earth": "Земля", "Moon": "Луна",
    "North Node": "Сев. Узел", "South Node": "Юж. Узел",
    "Mercury": "Меркурий", "Venus": "Венера", "Mars": "Марс",
    "Jupiter": "Юпитер", "Saturn": "Сатурн",
    "Uranus": "Уран", "Neptune": "Нептун", "Pluto": "Плутон",
}


# ───────────── Data structures ─────────────

@dataclass
class PlanetActivation:
    """Single planet position with gate/line/color/tone/base."""
    planet: str
    degree: float
    gate: int
    line: int
    color: int = 0
    tone: int = 0
    base: int = 0


@dataclass
class ChartResult:
    """Complete Human Design chart calculation result."""
    # Core
    type: str
    type_ru: str
    profile: str
    authority: str
    authority_ru: str
    strategy: str
    strategy_ru: str
    signature: str
    signature_ru: str
    not_self_theme: str
    not_self_theme_ru: str

    # Centers
    defined_centers: list[str]
    open_centers: list[str]
    defined_centers_ru: list[str]
    open_centers_ru: list[str]

    # Channels
    active_channels: list[dict]

    # Gates
    all_active_gates: list[int]

    # Planets
    personality: list[dict]   # Conscious (black)
    design: list[dict]        # Unconscious (red)

    # Incarnation Cross
    incarnation_cross: dict

    # Variables (arrows)
    variables: dict | None = None

    # Definition
    definition: str = ""
    definition_ru: str = ""

    # Split details
    split_centers: list[list[str]] | None = None

    # Metadata
    personality_date: str = ""
    design_date: str = ""


# ───────────── Planet positions ─────────────

def _get_planet_degree(jd: float, planet_id: int) -> float:
    """Get ecliptic longitude for a planet at Julian day."""
    try:
        result = swe.calc_ut(jd, planet_id, swe.FLG_MOSEPH)
    except AttributeError:
        result = swe.calc_ut(jd, planet_id)
    return result[0][0]


def get_planet_positions(jd: float, include_variables: bool = False) -> list[PlanetActivation]:
    """Calculate gate/line positions for all HD planets at a given Julian Day."""
    positions = []

    # Sun
    sun_deg = _get_planet_degree(jd, swe.SUN)
    if include_variables:
        act = degree_to_full_activation(sun_deg)
        positions.append(PlanetActivation("Sun", sun_deg, **act))
    else:
        gate, line = degree_to_gate_line(sun_deg)
        positions.append(PlanetActivation("Sun", sun_deg, gate, line))

    # Earth = Sun + 180°
    earth_deg = (sun_deg + 180.0) % 360
    if include_variables:
        act = degree_to_full_activation(earth_deg)
        positions.append(PlanetActivation("Earth", earth_deg, **act))
    else:
        gate, line = degree_to_gate_line(earth_deg)
        positions.append(PlanetActivation("Earth", earth_deg, gate, line))

    # Moon and planets
    for name, planet_id in HD_PLANETS.items():
        if name in ("Sun", "Earth", "South Node"):
            continue
        if planet_id is None:
            continue
        deg = _get_planet_degree(jd, planet_id)
        if include_variables:
            act = degree_to_full_activation(deg)
            positions.append(PlanetActivation(name, deg, **act))
        else:
            gate, line = degree_to_gate_line(deg)
            positions.append(PlanetActivation(name, deg, gate, line))

    # South Node = North Node + 180°
    nn = next(p for p in positions if p.planet == "North Node")
    sn_deg = (nn.degree + 180.0) % 360
    if include_variables:
        act = degree_to_full_activation(sn_deg)
        positions.append(PlanetActivation("South Node", sn_deg, **act))
    else:
        gate, line = degree_to_gate_line(sn_deg)
        positions.append(PlanetActivation("South Node", sn_deg, gate, line))

    return positions


# ───────────── Design date (88° solar arc) ─────────────

def find_design_date(jd_personality: float) -> float:
    """
    Find the Julian Day when the Sun was exactly 88° behind
    its personality position (binary search, SharpAstrology approach).
    """
    sun_deg = _get_planet_degree(jd_personality, swe.SUN)
    target_deg = (sun_deg - 88.0) % 360

    # Binary search: Sun was at target_deg roughly 88 days before birth
    jd_low = jd_personality - 100
    jd_high = jd_personality - 75
    jd_design = (jd_low + jd_high) / 2

    for _ in range(60):  # 60 iterations → precision < 0.0001°
        jd_mid = (jd_low + jd_high) / 2
        cur_deg = _get_planet_degree(jd_mid, swe.SUN)
        diff = (cur_deg - target_deg + 180) % 360 - 180
        if abs(diff) < 0.0001:
            jd_design = jd_mid
            break
        if diff > 0:
            jd_high = jd_mid
        else:
            jd_low = jd_mid
        jd_design = jd_mid

    return jd_design


# ───────────── Type determination ─────────────

def _build_center_graph(defined_centers: set[str], active_channels: list[Channel]) -> dict[str, set[str]]:
    """Build adjacency graph of defined centers connected by channels."""
    graph: dict[str, set[str]] = defaultdict(set)
    for ch in active_channels:
        if ch.center1 in defined_centers and ch.center2 in defined_centers:
            graph[ch.center1].add(ch.center2)
            graph[ch.center2].add(ch.center1)
    return graph


def _motor_reaches_throat(defined_centers: set[str], active_channels: list[Channel]) -> bool:
    """
    Check if ANY motor center reaches the Throat through defined channels.
    Uses BFS graph traversal (SharpAstrology approach — NOT just direct connection).
    """
    if "Throat" not in defined_centers:
        return False

    graph = _build_center_graph(defined_centers, active_channels)
    motor_centers = {"Sacral", "Heart", "Solar Plexus", "Root"}
    motors_defined = motor_centers & defined_centers

    for motor in motors_defined:
        # BFS from motor to Throat
        visited = set()
        queue = [motor]
        while queue:
            current = queue.pop(0)
            if current == "Throat":
                return True
            if current in visited:
                continue
            visited.add(current)
            for neighbor in graph.get(current, set()):
                if neighbor not in visited:
                    queue.append(neighbor)
    return False


def determine_type(defined_centers: set[str], active_channels: list[Channel]) -> tuple[str, str]:
    """Determine HD type. Returns (english, russian)."""
    if not defined_centers:
        return "Reflector", "Рефлектор"

    has_sacral = "Sacral" in defined_centers
    motor_to_throat = _motor_reaches_throat(defined_centers, active_channels)

    if has_sacral and motor_to_throat:
        return "Manifesting Generator", "Манифестирующий Генератор"
    elif has_sacral:
        return "Generator", "Генератор"
    elif motor_to_throat:
        return "Manifestor", "Манифестор"
    else:
        return "Projector", "Проектор"


# ───────────── Authority ─────────────

def determine_authority(defined_centers: set[str], hd_type: str) -> tuple[str, str]:
    """Determine inner authority. Returns (english, russian)."""
    # Reflector has Lunar authority
    if hd_type == "Reflector":
        return "Lunar", "Лунный"

    priority = [
        ("Solar Plexus", "Emotional", "Эмоциональный"),
        ("Sacral", "Sacral", "Сакральный"),
        ("Spleen", "Splenic", "Селезёночный"),
        ("Heart", "Ego", "Эго"),
        ("Self", "Self-Projected", "Самопроецируемый"),
    ]
    for center, auth_en, auth_ru in priority:
        if center in defined_centers:
            return auth_en, auth_ru

    # Mental Projector (only Head/Ajna/Throat defined, no motors/self)
    if "Ajna" in defined_centers:
        return "Mental (Outer Authority)", "Ментальный (Внешний Авторитет)"
    return "None (Outer Authority)", "Нет (Внешний Авторитет)"


# ───────────── Strategy, Signature, Not-Self ─────────────

TYPE_META = {
    "Generator": {
        "strategy": "To Respond",
        "strategy_ru": "Откликаться",
        "signature": "Satisfaction",
        "signature_ru": "Удовлетворение",
        "not_self": "Frustration",
        "not_self_ru": "Фрустрация",
    },
    "Manifesting Generator": {
        "strategy": "To Respond, then Inform",
        "strategy_ru": "Откликаться, затем информировать",
        "signature": "Satisfaction",
        "signature_ru": "Удовлетворение",
        "not_self": "Frustration & Anger",
        "not_self_ru": "Фрустрация и гнев",
    },
    "Projector": {
        "strategy": "Wait for the Invitation",
        "strategy_ru": "Ждать приглашения",
        "signature": "Success",
        "signature_ru": "Успех",
        "not_self": "Bitterness",
        "not_self_ru": "Горечь",
    },
    "Manifestor": {
        "strategy": "To Inform",
        "strategy_ru": "Информировать",
        "signature": "Peace",
        "signature_ru": "Мир",
        "not_self": "Anger",
        "not_self_ru": "Гнев",
    },
    "Reflector": {
        "strategy": "Wait a Lunar Cycle (28 days)",
        "strategy_ru": "Ждать лунный цикл (28 дней)",
        "signature": "Surprise",
        "signature_ru": "Удивление",
        "not_self": "Disappointment",
        "not_self_ru": "Разочарование",
    },
}


# ───────────── Definition (splits) ─────────────

def determine_definition(defined_centers: set[str], active_channels: list[Channel]) -> tuple[str, str, list[list[str]]]:
    """
    Determine definition type using graph connectivity (BFS).
    Returns (english, russian, list_of_groups).
    """
    if not defined_centers:
        return "No Definition", "Нет определения", []

    graph = _build_center_graph(defined_centers, active_channels)

    visited = set()
    groups = []

    for center in defined_centers:
        if center in visited:
            continue
        # BFS to find connected component
        group = []
        queue = [center]
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            group.append(current)
            for neighbor in graph.get(current, set()):
                if neighbor not in visited and neighbor in defined_centers:
                    queue.append(neighbor)
        groups.append(sorted(group))

    n = len(groups)
    labels = {
        1: ("Single Definition", "Единое определение"),
        2: ("Split Definition", "Расщеплённое определение"),
        3: ("Triple Split", "Тройной сплит"),
        4: ("Quadruple Split", "Четверной сплит"),
    }
    en, ru = labels.get(n, (f"{n}-Split", f"{n}-сплит"))
    return en, ru, groups


# ───────────── Incarnation Cross ─────────────

CROSS_ANGLE = {
    "1/3": "Right Angle", "1/4": "Right Angle",
    "2/4": "Right Angle", "2/5": "Right Angle",
    "3/5": "Right Angle", "3/6": "Right Angle",
    "4/6": "Right Angle", "4/1": "Juxtaposition",
    "5/1": "Left Angle", "5/2": "Left Angle",
    "6/2": "Left Angle", "6/3": "Left Angle",
}

CROSS_ANGLE_RU = {
    "Right Angle": "Правый угол",
    "Left Angle": "Левый угол",
    "Juxtaposition": "Сопоставление",
}

# Cross names by personality Sun gate (simplified — covers main 64 crosses)
# Full list: https://www.jovianarchive.com/Human_Design/Incarnation_Crosses
CROSS_NAMES = {
    1: "The Sphinx", 2: "The Sphinx", 7: "The Sphinx", 13: "The Sphinx",
    3: "Laws", 60: "Laws", 50: "Laws", 56: "Laws",
    4: "Explanation", 49: "Explanation", 43: "Explanation", 23: "Explanation",
    5: "Consciousness", 35: "Consciousness", 63: "Consciousness", 64: "Consciousness",
    6: "Eden", 36: "Eden", 12: "Eden", 11: "Eden",
    8: "Contribution", 14: "Contribution", 55: "Contribution", 59: "Contribution",
    9: "Planning", 16: "Planning", 40: "Planning", 37: "Planning",
    10: "the Vessel of Love", 15: "the Vessel of Love", 46: "the Vessel of Love", 25: "the Vessel of Love",
    17: "Service", 18: "Service", 58: "Service", 52: "Service",
    19: "the Four Ways", 33: "the Four Ways", 44: "the Four Ways", 24: "the Four Ways",
    20: "the Sleeping Phoenix", 34: "the Sleeping Phoenix", 57: "the Sleeping Phoenix", 51: "the Sleeping Phoenix",
    21: "Endeavor", 48: "Endeavor", 45: "Endeavor", 26: "Endeavor",
    22: "Fates", 47: "Fates", 12: "Fates", 11: "Fates",
    27: "the Unexpected", 28: "the Unexpected", 41: "the Unexpected", 31: "the Unexpected",
    29: "Contagion", 30: "Contagion", 20: "Contagion", 34: "Contagion",
    32: "Maya", 42: "Maya", 61: "Maya", 62: "Maya",
    38: "Tension", 39: "Tension", 54: "Tension", 53: "Tension",
}


def determine_incarnation_cross(
    personality: list[PlanetActivation],
    design: list[PlanetActivation],
    profile: str,
) -> dict:
    """Determine incarnation cross from Sun/Earth gates of personality and design."""
    p_sun = next(p for p in personality if p.planet == "Sun")
    p_earth = next(p for p in personality if p.planet == "Earth")
    d_sun = next(p for p in design if p.planet == "Sun")
    d_earth = next(p for p in design if p.planet == "Earth")

    gates = [p_sun.gate, p_earth.gate, d_sun.gate, d_earth.gate]
    angle = CROSS_ANGLE.get(profile, "Right Angle")
    angle_ru = CROSS_ANGLE_RU.get(angle, angle)

    cross_name = CROSS_NAMES.get(p_sun.gate, f"Cross of Gate {p_sun.gate}")

    return {
        "name": f"{angle} Cross of {cross_name}",
        "name_ru": f"Крест {angle_ru}: {cross_name}",
        "angle": angle,
        "angle_ru": angle_ru,
        "gates": gates,
        "personality_sun": p_sun.gate,
        "personality_earth": p_earth.gate,
        "design_sun": d_sun.gate,
        "design_earth": d_earth.gate,
    }


# ───────────── Variables (4 arrows) ─────────────

def determine_variables(
    personality: list[PlanetActivation],
    design: list[PlanetActivation],
) -> dict:
    """
    Determine the 4 Variables (arrows) from Color/Tone of
    Personality Sun/Node and Design Sun/Node.

    Arrow direction: Color 1-3 = Left (◄), Color 4-6 = Right (►)
    """
    def get_planet(planets: list[PlanetActivation], name: str) -> PlanetActivation:
        return next(p for p in planets if p.planet == name)

    def arrow(color: int) -> str:
        return "Left" if color <= 3 else "Right"

    p_sun = get_planet(personality, "Sun")
    p_node = get_planet(personality, "North Node")
    d_sun = get_planet(design, "Sun")
    d_node = get_planet(design, "North Node")

    if not all(p.color > 0 for p in [p_sun, p_node, d_sun, d_node]):
        return {}

    return {
        "digestion": {
            "arrow": arrow(d_sun.color),
            "color": d_sun.color,
            "tone": d_sun.tone,
            "label": "Active" if d_sun.color <= 3 else "Passive",
        },
        "environment": {
            "arrow": arrow(d_node.color),
            "color": d_node.color,
            "tone": d_node.tone,
            "label": "Observed" if d_node.color <= 3 else "Observer",
        },
        "perspective": {
            "arrow": arrow(p_sun.color),
            "color": p_sun.color,
            "tone": p_sun.tone,
            "label": "Focused" if p_sun.color <= 3 else "Peripheral",
        },
        "motivation": {
            "arrow": arrow(p_node.color),
            "color": p_node.color,
            "tone": p_node.tone,
            "label": "Specific" if p_node.color <= 3 else "Non-Specific",
        },
        "arrows": (
            f"{'◄' if d_sun.color <= 3 else '►'} "
            f"{'◄' if d_node.color <= 3 else '►'} "
            f"{'◄' if p_sun.color <= 3 else '►'} "
            f"{'◄' if p_node.color <= 3 else '►'}"
        ),
    }


# ───────────── Main calculation ─────────────

def calculate_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    utc_offset: float = 0.0,
    include_variables: bool = True,
) -> ChartResult:
    """
    Calculate a complete Human Design chart.

    Args:
        year, month, day, hour, minute: Birth date/time
        utc_offset: UTC offset in hours (e.g., 3.0 for MSK)
        include_variables: Whether to calculate Color/Tone/Base for Variables

    Returns:
        ChartResult with all chart data
    """
    # Convert to UTC
    utc_hour = hour - utc_offset + minute / 60.0
    jd_personality = swe.julday(year, month, day, utc_hour)

    # Find Design date (88° solar arc before birth)
    jd_design = find_design_date(jd_personality)

    # Calculate planet positions
    personality = get_planet_positions(jd_personality, include_variables)
    design = get_planet_positions(jd_design, include_variables)

    # Collect all active gates
    all_gates: set[int] = set()
    for p in personality:
        all_gates.add(p.gate)
    for p in design:
        all_gates.add(p.gate)

    # Active channels
    active_channels = find_active_channels(all_gates)

    # Defined centers (via active channels)
    defined_centers: set[str] = set()
    for ch in active_channels:
        defined_centers.add(ch.center1)
        defined_centers.add(ch.center2)

    all_center_names = list(CENTERS.keys())
    open_centers = sorted(set(all_center_names) - defined_centers)

    # Profile
    p_sun_line = next(p for p in personality if p.planet == "Sun").line
    d_sun_line = next(p for p in design if p.planet == "Sun").line
    profile = f"{p_sun_line}/{d_sun_line}"

    # Type
    hd_type, hd_type_ru = determine_type(defined_centers, active_channels)

    # Authority
    authority, authority_ru = determine_authority(defined_centers, hd_type)

    # Strategy, Signature, Not-Self
    meta = TYPE_META.get(hd_type, TYPE_META["Projector"])

    # Definition (splits)
    definition, definition_ru, split_groups = determine_definition(
        defined_centers, active_channels
    )

    # Incarnation Cross
    cross = determine_incarnation_cross(personality, design, profile)

    # Variables
    variables = None
    if include_variables:
        variables = determine_variables(personality, design)

    # Convert planet data to dicts for output
    def planets_to_dicts(planets: list[PlanetActivation]) -> list[dict]:
        result = []
        for p in planets:
            d = {
                "planet": p.planet,
                "planet_ru": HD_PLANETS_RU.get(p.planet, p.planet),
                "gate": p.gate,
                "gate_name": GATE_NAMES.get(p.gate, ""),
                "gate_name_ru": GATE_NAMES_RU.get(p.gate, ""),
                "line": p.line,
                "degree": round(p.degree, 4),
            }
            if include_variables:
                d["color"] = p.color
                d["tone"] = p.tone
                d["base"] = p.base
            result.append(d)
        return result

    # Format channel data
    channel_dicts = []
    for ch in active_channels:
        channel_dicts.append({
            "gates": [ch.gate1, ch.gate2],
            "name": ch.name,
            "name_ru": ch.name_ru,
            "centers": [ch.center1, ch.center2],
            "circuit": ch.circuit,
        })

    # Design date for metadata
    design_dt = swe.revjul(jd_design)
    design_date_str = f"{int(design_dt[0])}-{int(design_dt[1]):02d}-{int(design_dt[2]):02d}"

    # Center names in Russian
    defined_centers_ru = [CENTERS[c].name_ru for c in sorted(defined_centers)]
    open_centers_ru = [CENTERS[c].name_ru for c in open_centers]

    return ChartResult(
        type=hd_type,
        type_ru=hd_type_ru,
        profile=profile,
        authority=authority,
        authority_ru=authority_ru,
        strategy=meta["strategy"],
        strategy_ru=meta["strategy_ru"],
        signature=meta["signature"],
        signature_ru=meta["signature_ru"],
        not_self_theme=meta["not_self"],
        not_self_theme_ru=meta["not_self_ru"],
        defined_centers=sorted(defined_centers),
        open_centers=open_centers,
        defined_centers_ru=defined_centers_ru,
        open_centers_ru=open_centers_ru,
        active_channels=channel_dicts,
        all_active_gates=sorted(all_gates),
        personality=planets_to_dicts(personality),
        design=planets_to_dicts(design),
        incarnation_cross=cross,
        variables=variables,
        definition=definition,
        definition_ru=definition_ru,
        split_centers=split_groups,
        personality_date=f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC{utc_offset:+.1f}",
        design_date=design_date_str,
    )
