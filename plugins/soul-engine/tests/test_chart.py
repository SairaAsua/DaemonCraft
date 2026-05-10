"""
Smoke test — verifies chart calculation against a known reference.

Expected (reference calculator):
- Type: Projector (Mental)
- Profile: 1/3
- Authority: No inner authority (Mental)
- Defined Centers: Head, Ajna, Throat
- Channels: 64-47 (Abstraction), 43-23 (Structuring)
- Timezone: Europe/Kirov = UTC+4 in 1979

Birth data: fictional, based on a verified reference chart.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hd.chart import calculate_chart
from hd.geo import resolve_location, get_utc_offset


def test_chart_projector():
    """Test chart calculation for a Mental Projector — verified against reference."""

    # Auto-resolve timezone from city name
    coords = resolve_location("Кирово-Чепецк")
    assert coords is not None, "Should resolve Кирово-Чепецк"
    lat, lng = coords
    offset = get_utc_offset(lat, lng, 1979, 5, 10, 9, 29)
    print(f"  Timezone resolved: UTC+{offset:.1f} (Europe/Kirov)")
    assert offset == 4.0, f"Kirov in 1979 should be UTC+4, got UTC+{offset}"

    result = calculate_chart(
        year=1979,
        month=5,
        day=10,
        hour=9,
        minute=29,
        utc_offset=offset,
        include_variables=True,
    )

    print("=" * 60)
    print("  Human Design Chart — Projector Reference Test")
    print("=" * 60)
    print(f"  Type:       {result.type} / {result.type_ru}")
    print(f"  Profile:    {result.profile}")
    print(f"  Authority:  {result.authority} / {result.authority_ru}")
    print(f"  Strategy:   {result.strategy_ru}")
    print(f"  Signature:  {result.signature_ru}")
    print(f"  Not-Self:   {result.not_self_theme_ru}")
    print(f"  Definition: {result.definition_ru}")
    print()
    print(f"  Defined centers: {', '.join(result.defined_centers_ru)}")
    print(f"  Open centers:    {', '.join(result.open_centers_ru)}")
    print()
    print(f"  Channels ({len(result.active_channels)}):")
    for ch in result.active_channels:
        print(f"    {ch['gates'][0]}-{ch['gates'][1]}: {ch['name_ru']} ({ch['circuit']})")
    print()
    print(f"  Cross: {result.incarnation_cross['name']}")
    print(f"         {result.incarnation_cross['name_ru']}")
    print(f"         Gates: {result.incarnation_cross['gates']}")
    print()

    if result.variables:
        print(f"  Variables: {result.variables.get('arrows', '')}")
        for key in ['digestion', 'environment', 'perspective', 'motivation']:
            v = result.variables.get(key, {})
            print(f"    {key}: {v.get('arrow', '')} (Color {v.get('color', '')}, Tone {v.get('tone', '')})")
        print()

    print(f"  Personality date: {result.personality_date}")
    for p in result.personality:
        extras = ""
        if p.get("color"):
            extras = f" | C{p['color']}.T{p['tone']}.B{p['base']}"
        print(f"    {p['planet']:<12} Gate {p['gate']}.{p['line']}  ({p['degree']:.2f}°){extras}")

    print()
    print(f"  Design date: {result.design_date}")
    for p in result.design:
        extras = ""
        if p.get("color"):
            extras = f" | C{p['color']}.T{p['tone']}.B{p['base']}"
        print(f"    {p['planet']:<12} Gate {p['gate']}.{p['line']}  ({p['degree']:.2f}°){extras}")

    print("=" * 60)

    # === Assertions verified against reference calculator ===
    assert result.type == "Projector", f"Expected Projector, got {result.type}"
    assert result.profile == "1/3", f"Expected 1/3, got {result.profile}"

    # Mental Projector = no inner authority
    assert "Mental" in result.authority or "None" in result.authority, \
        f"Expected Mental/No authority, got {result.authority}"

    # Defined centers: ONLY Head, Ajna, Throat
    assert set(result.defined_centers) == {"Head", "Ajna", "Throat"}, \
        f"Expected Head/Ajna/Throat, got {result.defined_centers}"

    # Sacral must be open
    assert "Sacral" in result.open_centers, "Sacral should be open"

    # Channels: 43-23 and 47-64
    channel_keys = [frozenset(ch['gates']) for ch in result.active_channels]
    assert frozenset({23, 43}) in channel_keys, "Channel 23-43 missing"
    assert frozenset({47, 64}) in channel_keys, "Channel 47-64 missing"

    # Cross: Explanation (23/43 | 49/4)
    assert result.incarnation_cross['gates'] == [23, 43, 49, 4], \
        f"Cross gates should be [23, 43, 49, 4], got {result.incarnation_cross['gates']}"

    # Personality Sun = Gate 23
    p_sun = next(p for p in result.personality if p['planet'] == 'Sun')
    assert p_sun['gate'] == 23, f"P Sun should be gate 23, got {p_sun['gate']}"

    # Design Sun = Gate 49
    d_sun = next(p for p in result.design if p['planet'] == 'Sun')
    assert d_sun['gate'] == 49, f"D Sun should be gate 49, got {d_sun['gate']}"

    print("\n✅ All assertions passed! Chart matches reference exactly!")


if __name__ == "__main__":
    test_chart_projector()
