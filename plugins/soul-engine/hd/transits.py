"""
Transit calculation: current planetary positions and their impact on a natal chart.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass

import swisseph as swe

from hd.data.gates import degree_to_gate_line, GATE_NAMES, GATE_NAMES_RU
from hd.data.channels import find_active_channels, CHANNELS
from hd.data.centers import CENTERS
from hd.chart import get_planet_positions, HD_PLANETS_RU


def get_transits(
    transit_year: int = 0,
    transit_month: int = 0,
    transit_day: int = 0,
    transit_hour: int = 0,
    transit_minute: int = 0,
    utc_offset: float = 0.0,
    natal_gates: set[int] | None = None,
) -> dict:
    """
    Calculate current (or specified) transit positions.

    If natal_gates are provided, shows which channels get temporarily activated.
    """
    # Default to current time
    if transit_year == 0:
        now = datetime.now(timezone.utc)
        transit_year = now.year
        transit_month = now.month
        transit_day = now.day
        transit_hour = now.hour
        transit_minute = now.minute
        utc_offset = 0.0

    utc_hour = transit_hour - utc_offset + transit_minute / 60.0
    jd = swe.julday(transit_year, transit_month, transit_day, utc_hour)

    positions = get_planet_positions(jd, include_variables=False)

    transit_gates: set[int] = {p.gate for p in positions}

    planets_data = []
    for p in positions:
        planets_data.append({
            "planet": p.planet,
            "planet_ru": HD_PLANETS_RU.get(p.planet, p.planet),
            "gate": p.gate,
            "gate_name": GATE_NAMES.get(p.gate, ""),
            "gate_name_ru": GATE_NAMES_RU.get(p.gate, ""),
            "line": p.line,
            "degree": round(p.degree, 4),
        })

    result = {
        "transit_date": f"{transit_year}-{transit_month:02d}-{transit_day:02d} {transit_hour:02d}:{transit_minute:02d} UTC{utc_offset:+.1f}",
        "transit_gates": sorted(transit_gates),
        "planets": planets_data,
    }

    # If we have natal chart data, find temporarily activated channels
    if natal_gates is not None:
        combined_gates = natal_gates | transit_gates
        all_channels = find_active_channels(combined_gates)
        natal_channels = find_active_channels(natal_gates)
        natal_channel_keys = {frozenset({ch.gate1, ch.gate2}) for ch in natal_channels}

        new_channels = []
        for ch in all_channels:
            key = frozenset({ch.gate1, ch.gate2})
            if key not in natal_channel_keys:
                new_channels.append({
                    "gates": [ch.gate1, ch.gate2],
                    "name": ch.name,
                    "name_ru": ch.name_ru,
                    "centers": [ch.center1, ch.center2],
                    "activated_by": "transit",
                })

        result["natal_transit_channels"] = new_channels
        result["natal_transit_defined_centers"] = sorted(
            {ch["centers"][0] for ch in new_channels} | {ch["centers"][1] for ch in new_channels}
        )

    return result
