"""
Timezone and geocoding utilities.

Resolves birth location to coordinates and determines the historically
correct UTC offset (handles cases like Kirov being UTC+4 before 2014).
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from timezonefinder import TimezoneFinder

_tf = TimezoneFinder()

# Well-known cities for quick lookup (no geocoding API needed)
CITY_COORDS: dict[str, tuple[float, float]] = {
    # Russia
    "moscow": (55.7558, 37.6173),
    "москва": (55.7558, 37.6173),
    "saint petersburg": (59.9343, 30.3351),
    "санкт-петербург": (59.9343, 30.3351),
    "kirov": (58.6035, 49.6668),
    "киров": (58.6035, 49.6668),
    "kirovo-chepetsk": (58.5530, 50.0310),
    "кирово-чепецк": (58.5530, 50.0310),
    "prigorodnyy": (58.5530, 50.0310),  # Near Kirovo-Chepetsk
    "пригородный": (58.5530, 50.0310),
    "novosibirsk": (55.0084, 82.9357),
    "новосибирск": (55.0084, 82.9357),
    "yekaterinburg": (56.8389, 60.6057),
    "екатеринбург": (56.8389, 60.6057),
    "kazan": (55.7963, 49.1088),
    "казань": (55.7963, 49.1088),
    "nizhny novgorod": (56.2965, 43.9361),
    "нижний новгород": (56.2965, 43.9361),
    "samara": (53.1959, 50.1002),
    "самара": (53.1959, 50.1002),
    "omsk": (54.9885, 73.3242),
    "омск": (54.9885, 73.3242),
    "chelyabinsk": (55.1644, 61.4368),
    "челябинск": (55.1644, 61.4368),
    "rostov-on-don": (47.2357, 39.7015),
    "ростов-на-дону": (47.2357, 39.7015),
    "ufa": (54.7388, 55.9721),
    "уфа": (54.7388, 55.9721),
    "krasnoyarsk": (56.0153, 92.8932),
    "красноярск": (56.0153, 92.8932),
    "perm": (58.0105, 56.2502),
    "пермь": (58.0105, 56.2502),
    "voronezh": (51.6720, 39.1843),
    "воронеж": (51.6720, 39.1843),
    "volgograd": (48.7080, 44.5133),
    "волгоград": (48.7080, 44.5133),
    # International
    "new york": (40.7128, -74.0060),
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "berlin": (52.5200, 13.4050),
    "tokyo": (35.6762, 139.6503),
    "sydney": (-33.8688, 151.2093),
    "los angeles": (34.0522, -118.2437),
    "chicago": (41.8781, -87.6298),
}


def resolve_location(place: str) -> tuple[float, float] | None:
    """
    Resolve a place name to (latitude, longitude).
    Uses built-in city database. Returns None if not found.
    """
    key = place.lower().strip()
    return CITY_COORDS.get(key)


def get_utc_offset(
    lat: float,
    lng: float,
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    minute: int = 0,
) -> float:
    """
    Get the historically correct UTC offset for a given location and date.

    This handles cases like:
    - Kirov was UTC+4 before Oct 26, 2014, then became UTC+3
    - USSR decree time shifts
    - DST changes worldwide

    Returns offset in hours (e.g., 4.0 for UTC+4).
    """
    tz_name = _tf.timezone_at(lat=lat, lng=lng)
    if tz_name is None:
        return 0.0

    try:
        tz = ZoneInfo(tz_name)
        dt = datetime(year, month, day, hour, minute, tzinfo=tz)
        offset = dt.utcoffset()
        if offset is None:
            return 0.0
        return offset.total_seconds() / 3600.0
    except Exception:
        return 0.0


def get_timezone_name(lat: float, lng: float) -> str | None:
    """Get IANA timezone name for coordinates."""
    return _tf.timezone_at(lat=lat, lng=lng)
