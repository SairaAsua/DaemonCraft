"""
Human Design MCP Server — the first full-featured HD calculator for AI assistants.

Provides 3 tools:
- calculate_chart: Full rave chart from birth data (auto timezone by city)
- get_transits: Current (or dated) transit positions with natal overlay
- compare_charts: Composite chart & compatibility for two people

License: MIT
Architecture: Python port of SharpAstrology.HumanDesign logic + pyswisseph
"""

from __future__ import annotations

import json
from dataclasses import asdict

from fastmcp import FastMCP

from hd.chart import calculate_chart as _calc_chart
from hd.transits import get_transits as _get_transits
from hd.composite import compare_charts as _compare_charts
from hd.geo import resolve_location, get_utc_offset

mcp = FastMCP(
    "Human Design",
    instructions=(
        "Calculate Human Design charts, transits, and compatibility. "
        "Full rave chart with type, profile, authority, strategy, channels, "
        "gates with lines, incarnation cross, variables (4 arrows), "
        "and definition splits. "
        "Supports automatic timezone detection by city name (handles "
        "historical timezone changes, e.g. Kirov was UTC+4 before 2014)."
    ),
)


def _resolve_offset(
    birth_place: str | None,
    utc_offset: float | None,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
) -> float:
    """Resolve UTC offset from place name or explicit value."""
    if utc_offset is not None:
        return utc_offset

    if birth_place:
        coords = resolve_location(birth_place)
        if coords:
            lat, lng = coords
            return get_utc_offset(lat, lng, year, month, day, hour, minute)

    return 0.0


@mcp.tool()
def calculate_chart(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    birth_place: str = "",
    utc_offset: float | None = None,
) -> str:
    """
    Calculate a complete Human Design rave chart (bodygraph).

    Provide EITHER birth_place (city name, auto-detects timezone including
    historical changes) OR utc_offset (explicit UTC offset in hours).
    If both are given, utc_offset takes priority.

    IMPORTANT: Historical timezone matters! For example, Kirov (Russia) was
    UTC+4 before 2014 and UTC+3 after. Using birth_place handles this
    automatically. If using utc_offset, verify the correct historical offset.

    Args:
        birth_year: Year of birth (e.g. 1979)
        birth_month: Month of birth (1-12)
        birth_day: Day of birth (1-31)
        birth_hour: Hour of birth in LOCAL time (0-23)
        birth_minute: Minute of birth (0-59)
        birth_place: City name for auto timezone detection (e.g. "Киров", "Moscow", "New York"). Supports Russian and English.
        utc_offset: Explicit UTC offset in hours (e.g. 4.0 for UTC+4). Overrides birth_place if both given.

    Returns:
        Complete chart data: type, profile, authority, strategy, signature,
        not-self theme, defined/open centers, active channels, all gates with lines,
        incarnation cross, variables (4 arrows with color/tone/base),
        definition type (single/split/triple/quad).
    """
    offset = _resolve_offset(
        birth_place, utc_offset, birth_year, birth_month, birth_day,
        birth_hour, birth_minute,
    )

    result = _calc_chart(
        year=birth_year,
        month=birth_month,
        day=birth_day,
        hour=birth_hour,
        minute=birth_minute,
        utc_offset=offset,
        include_variables=True,
    )

    output = asdict(result)
    output["_timezone"] = {
        "utc_offset": offset,
        "source": "explicit" if utc_offset is not None else (
            f"auto ({birth_place})" if birth_place else "default UTC"
        ),
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


@mcp.tool()
def get_transits(
    birth_year: int = 0,
    birth_month: int = 0,
    birth_day: int = 0,
    birth_hour: int = 0,
    birth_minute: int = 0,
    birth_place: str = "",
    birth_utc_offset: float | None = None,
    transit_year: int = 0,
    transit_month: int = 0,
    transit_day: int = 0,
    transit_hour: int = 0,
    transit_minute: int = 0,
    transit_utc_offset: float = 0.0,
) -> str:
    """
    Calculate Human Design transits (current planetary field).

    If birth data is provided, shows which channels are temporarily activated
    by the transit field overlaying the natal chart.

    If no transit date is given, uses the current moment (UTC).
    If no birth data is given, returns only transit positions.

    Args:
        birth_year: Year of birth (optional, 0 = skip natal overlay)
        birth_month: Month (optional)
        birth_day: Day (optional)
        birth_hour: Hour in LOCAL time (optional)
        birth_minute: Minute (optional)
        birth_place: City name for auto timezone (optional)
        birth_utc_offset: Explicit UTC offset (optional, overrides birth_place)
        transit_year: Year for transit calc (0 = now)
        transit_month: Month for transit calc (0 = now)
        transit_day: Day for transit calc (0 = now)
        transit_hour: Hour for transit calc (0 = now)
        transit_minute: Minute for transit calc (0 = now)
        transit_utc_offset: UTC offset for transit time (0 = UTC)

    Returns:
        Transit planetary positions (gate/line for each planet),
        and if birth data given: temporarily activated channels and centers.
    """
    natal_gates = None
    if birth_year > 0:
        offset = _resolve_offset(
            birth_place, birth_utc_offset, birth_year, birth_month, birth_day,
            birth_hour, birth_minute,
        )
        chart = _calc_chart(
            year=birth_year,
            month=birth_month,
            day=birth_day,
            hour=birth_hour,
            minute=birth_minute,
            utc_offset=offset,
            include_variables=False,
        )
        natal_gates = set(chart.all_active_gates)

    result = _get_transits(
        transit_year=transit_year,
        transit_month=transit_month,
        transit_day=transit_day,
        transit_hour=transit_hour,
        transit_minute=transit_minute,
        utc_offset=transit_utc_offset,
        natal_gates=natal_gates,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def compare_charts(
    person1_year: int, person1_month: int, person1_day: int,
    person1_hour: int, person1_minute: int,
    person2_year: int, person2_month: int, person2_day: int,
    person2_hour: int, person2_minute: int,
    person1_place: str = "",
    person2_place: str = "",
    person1_utc_offset: float | None = None,
    person2_utc_offset: float | None = None,
    person1_name: str = "Person 1",
    person2_name: str = "Person 2",
) -> str:
    """
    Build a composite chart and analyze Human Design compatibility between two people.

    Shows:
    - Each person's type, profile, authority
    - Electromagnetic channels (strongest attraction — each person contributes one gate)
    - Dominance channels (one person defines the full channel)
    - Compromise channels (both people define the same channel)
    - Composite bodygraph type
    - Chemistry score

    Args:
        person1_year..person1_minute: Birth date/time for person 1
        person2_year..person2_minute: Birth date/time for person 2
        person1_place: City name for person 1 timezone auto-detection
        person2_place: City name for person 2 timezone auto-detection
        person1_utc_offset: Explicit UTC offset for person 1 (overrides place)
        person2_utc_offset: Explicit UTC offset for person 2 (overrides place)
        person1_name: Display name for person 1
        person2_name: Display name for person 2

    Returns:
        Complete compatibility analysis with channel breakdown and composite type.
    """
    offset1 = _resolve_offset(
        person1_place, person1_utc_offset, person1_year, person1_month,
        person1_day, person1_hour, person1_minute,
    )
    offset2 = _resolve_offset(
        person2_place, person2_utc_offset, person2_year, person2_month,
        person2_day, person2_hour, person2_minute,
    )

    result = _compare_charts(
        person1_year, person1_month, person1_day,
        person1_hour, person1_minute, offset1,
        person2_year, person2_month, person2_day,
        person2_hour, person2_minute, offset2,
        person1_name, person2_name,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
