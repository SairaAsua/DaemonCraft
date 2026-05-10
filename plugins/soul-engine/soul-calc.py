#!/usr/bin/env python3
"""
Soul Engine CLI wrapper for DaemonCraft bot.
Reads JSON from stdin, writes JSON to stdout.
Usage: echo '{"action":"chart",...}' | python soul-calc.py
"""
import json, sys, os

# Add soul-engine to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hd.chart import calculate_chart as _calc_chart
from hd.composite import compare_charts as _compare_charts
from hd.geo import resolve_location, get_utc_offset

def _resolve_offset(birth_place, utc_offset, year, month, day, hour, minute):
    if utc_offset is not None:
        return utc_offset
    if birth_place:
        coords = resolve_location(birth_place)
        if coords:
            lat, lng = coords
            return get_utc_offset(lat, lng, year, month, day, hour, minute)
    return 0.0

def calc_chart(params):
    offset = _resolve_offset(
        params.get("birth_place"), params.get("utc_offset"),
        params["birth_year"], params["birth_month"], params["birth_day"],
        params["birth_hour"], params["birth_minute"],
    )
    result = _calc_chart(
        year=params["birth_year"],
        month=params["birth_month"],
        day=params["birth_day"],
        hour=params["birth_hour"],
        minute=params["birth_minute"],
        utc_offset=offset,
        include_variables=True,
    )
    from dataclasses import asdict
    output = asdict(result)
    output["_timezone"] = {
        "utc_offset": offset,
        "source": "explicit" if params.get("utc_offset") is not None else (
            f"auto ({params.get('birth_place')})" if params.get("birth_place") else "default UTC"
        ),
    }
    return output

def calc_compare(params):
    offset1 = _resolve_offset(
        params.get("person1_place"), params.get("person1_utc_offset"),
        params["person1_year"], params["person1_month"], params["person1_day"],
        params["person1_hour"], params["person1_minute"],
    )
    offset2 = _resolve_offset(
        params.get("person2_place"), params.get("person2_utc_offset"),
        params["person2_year"], params["person2_month"], params["person2_day"],
        params["person2_hour"], params["person2_minute"],
    )
    result = _compare_charts(
        params["person1_year"], params["person1_month"], params["person1_day"],
        params["person1_hour"], params["person1_minute"], offset1,
        params["person2_year"], params["person2_month"], params["person2_day"],
        params["person2_hour"], params["person2_minute"], offset2,
        params.get("person1_name", "Person 1"),
        params.get("person2_name", "Person 2"),
    )
    return result

def main():
    raw = sys.stdin.read()
    if not raw:
        print(json.dumps({"ok": False, "error": "No input"}))
        return
    try:
        req = json.loads(raw)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"Invalid JSON: {e}"}))
        return

    action = req.get("action")
    try:
        if action == "chart":
            result = calc_chart(req)
            print(json.dumps({"ok": True, "chart": result}))
        elif action == "compare":
            result = calc_compare(req)
            print(json.dumps({"ok": True, "comparison": result}))
        else:
            print(json.dumps({"ok": False, "error": f"Unknown action: {action}"}))
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))

if __name__ == "__main__":
    main()
