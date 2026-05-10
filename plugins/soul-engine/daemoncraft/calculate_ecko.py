#!/usr/bin/env python3
"""
Calcular bodygraph de Ecko / Eko
Fecha: 26 octubre 1942, 11:11, Alta Gracia, Argentina
"""
import sys
sys.path.insert(0, '/home/saira/daemoncraft-soul-engine/human-design-mcp')

from hd.chart import calculate_chart
from hd.transits import get_transits
import json
from dataclasses import asdict

# Alta Gracia, Córdoba, Argentina
# En 1942, Argentina usaba UTC-4 (hora estándar) sin horario de verano

birth = {
    "year": 1942,
    "month": 10,
    "day": 26,
    "hour": 11,
    "minute": 11,
    "place": "Alta Gracia, Argentina",
    "utc_offset": -4.0,
}

print("=" * 70)
print("CALCULANDO BODYGRAPH NATAL")
print(f"Fecha: {birth['day']}/{birth['month']}/{birth['year']}")
print(f"Hora: {birth['hour']}:{birth['minute']:02d} (hora local)")
print(f"Lugar: {birth['place']}")
print(f"UTC offset: {birth['utc_offset']}")
print("=" * 70)

chart = calculate_chart(
    year=birth["year"],
    month=birth["month"],
    day=birth["day"],
    hour=birth["hour"],
    minute=birth["minute"],
    utc_offset=birth["utc_offset"],
)

print("\n--- RESULTADO NATAL ---\n")
chart_dict = asdict(chart)
print(json.dumps(chart_dict, indent=2, default=str, ensure_ascii=False))

# Guardar
with open("/home/saira/daemoncraft-soul-engine/ecko_natal.json", "w") as f:
    json.dump(chart_dict, f, indent=2, default=str, ensure_ascii=False)

print("\n" + "=" * 70)
print("CALCULANDO TRÁNSITOS DE HOY (2026-05-02)")
print("=" * 70)

# Extraer puertas natal para el overlay
natal_gates = set(chart.all_active_gates)

transits = get_transits(
    transit_year=2026,
    transit_month=5,
    transit_day=2,
    transit_hour=0,
    transit_minute=0,
    utc_offset=0.0,
    natal_gates=natal_gates,
)

print("\n--- TRÁNSITOS ---\n")
print(json.dumps(transits, indent=2, default=str, ensure_ascii=False))

with open("/home/saira/daemoncraft-soul-engine/ecko_transit_today.json", "w") as f:
    json.dump(transits, f, indent=2, default=str, ensure_ascii=False)

print("\n✅ Guardado en ecko_natal.json y ecko_transit_today.json")
