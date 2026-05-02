"""
Composite chart: compatibility analysis between two people.
Based on SharpAstrology.HumanDesign composite logic.
"""

from __future__ import annotations

from hd.chart import calculate_chart, ChartResult
from hd.data.channels import CHANNELS, Channel, find_active_channels
from hd.data.centers import CENTERS


def compare_charts(
    person1_year: int, person1_month: int, person1_day: int,
    person1_hour: int, person1_minute: int, person1_utc_offset: float,
    person2_year: int, person2_month: int, person2_day: int,
    person2_hour: int, person2_minute: int, person2_utc_offset: float,
    person1_name: str = "Person 1",
    person2_name: str = "Person 2",
) -> dict:
    """
    Build a composite chart and analyze compatibility.

    Returns:
    - Each person's type/profile/authority
    - Electromagnetic channels (one gate each — attraction)
    - Dominance channels (same channel defined by both)
    - Compromise channels (both have both gates)
    - Composite type (combined bodygraph)
    """
    chart1 = calculate_chart(
        person1_year, person1_month, person1_day,
        person1_hour, person1_minute, person1_utc_offset,
        include_variables=False,
    )
    chart2 = calculate_chart(
        person2_year, person2_month, person2_day,
        person2_hour, person2_minute, person2_utc_offset,
        include_variables=False,
    )

    gates1 = set(chart1.all_active_gates)
    gates2 = set(chart2.all_active_gates)
    combined_gates = gates1 | gates2

    # Individual channels
    channels1 = find_active_channels(gates1)
    channels2 = find_active_channels(gates2)
    channels_combined = find_active_channels(combined_gates)

    keys1 = {frozenset({ch.gate1, ch.gate2}) for ch in channels1}
    keys2 = {frozenset({ch.gate1, ch.gate2}) for ch in channels2}

    # Electromagnetic: channel exists ONLY in composite (one gate from each person)
    electromagnetic = []
    dominance = []
    compromise = []

    for ch in channels_combined:
        key = frozenset({ch.gate1, ch.gate2})
        in1 = key in keys1
        in2 = key in keys2

        if in1 and in2:
            # Both have the channel — check gates
            has_both_gates_1 = ch.gate1 in gates1 and ch.gate2 in gates1
            has_both_gates_2 = ch.gate1 in gates2 and ch.gate2 in gates2
            if has_both_gates_1 and has_both_gates_2:
                compromise.append(_channel_dict(ch, person1_name, person2_name, "compromise"))
            else:
                dominance.append(_channel_dict(ch, person1_name, person2_name, "dominance"))
        elif not in1 and not in2:
            # New channel only in composite = electromagnetic
            # Determine who contributes which gate
            g1_from = person1_name if ch.gate1 in gates1 else person2_name
            g2_from = person1_name if ch.gate2 in gates1 else person2_name
            electromagnetic.append({
                "gates": [ch.gate1, ch.gate2],
                "name": ch.name,
                "name_ru": ch.name_ru,
                "centers": [ch.center1, ch.center2],
                "type": "electromagnetic",
                f"gate_{ch.gate1}_from": g1_from,
                f"gate_{ch.gate2}_from": g2_from,
            })

    # Composite defined centers
    composite_channels = find_active_channels(combined_gates)
    composite_defined: set[str] = set()
    for ch in composite_channels:
        composite_defined.add(ch.center1)
        composite_defined.add(ch.center2)

    # Composite type
    from hd.chart import determine_type
    composite_type, composite_type_ru = determine_type(composite_defined, composite_channels)

    return {
        "person1": {
            "name": person1_name,
            "type": chart1.type,
            "type_ru": chart1.type_ru,
            "profile": chart1.profile,
            "authority": chart1.authority,
            "authority_ru": chart1.authority_ru,
            "defined_centers": chart1.defined_centers,
        },
        "person2": {
            "name": person2_name,
            "type": chart2.type,
            "type_ru": chart2.type_ru,
            "profile": chart2.profile,
            "authority": chart2.authority,
            "authority_ru": chart2.authority_ru,
            "defined_centers": chart2.defined_centers,
        },
        "composite": {
            "type": composite_type,
            "type_ru": composite_type_ru,
            "defined_centers": sorted(composite_defined),
            "defined_centers_ru": [CENTERS[c].name_ru for c in sorted(composite_defined)],
        },
        "electromagnetic_channels": electromagnetic,
        "dominance_channels": dominance,
        "compromise_channels": compromise,
        "total_new_channels": len(electromagnetic),
        "chemistry_score": _chemistry_score(electromagnetic, dominance, compromise),
    }


def _channel_dict(ch: Channel, p1: str, p2: str, ch_type: str) -> dict:
    return {
        "gates": [ch.gate1, ch.gate2],
        "name": ch.name,
        "name_ru": ch.name_ru,
        "centers": [ch.center1, ch.center2],
        "type": ch_type,
    }


def _chemistry_score(electromagnetic: list, dominance: list, compromise: list) -> dict:
    """
    Simple chemistry score based on channel interactions.
    Electromagnetic = attraction, Dominance = tension, Compromise = comfort.
    """
    em = len(electromagnetic)
    dom = len(dominance)
    comp = len(compromise)
    total = em + dom + comp
    if total == 0:
        return {"score": 0, "description": "No channel interactions", "description_ru": "Нет взаимодействий каналов"}

    # Electromagnetic channels create strongest attraction
    score = min(100, int((em * 15 + comp * 10 + dom * 5)))

    if score >= 70:
        desc = "Strong electromagnetic attraction"
        desc_ru = "Сильное электромагнитное притяжение"
    elif score >= 40:
        desc = "Moderate connection"
        desc_ru = "Умеренная связь"
    else:
        desc = "Light connection"
        desc_ru = "Лёгкая связь"

    return {"score": score, "description": desc, "description_ru": desc_ru}
