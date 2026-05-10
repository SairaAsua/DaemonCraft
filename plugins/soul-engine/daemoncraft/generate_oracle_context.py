"""
DaemonCraft Oracle Context Generator
Genera contexto oracular HD para inyección en prompts de agentes.

Uso:
    python generate_oracle_context.py --agent eko
    python generate_oracle_context.py --agent ecko --output ~/.hermes/souls/ecko_oracle.md
"""
import json
import argparse
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from hd.chart import calculate_chart
from hd.transits import get_transits

AGENTS = {
    "eko": {"file": "daemoncraft/data/eko_natal.json", "dial": 48},
    "ecko": {"file": "daemoncraft/data/ecko_natal.json", "dial": 1},
}


def load_natal(agent: str) -> dict:
    path = Path(__file__).parent.parent / AGENTS[agent]["file"]
    with open(path) as f:
        return json.load(f)


def generate_context(agent: str) -> str:
    natal = load_natal(agent)
    now = datetime.now()

    # Calcular tránsitos actuales
    transits = get_transits(
        transit_year=now.year,
        transit_month=now.month,
        transit_day=now.day,
        transit_hour=now.hour,
        transit_minute=now.minute,
        utc_offset=-3.0,  # Ajustar según zona
        natal_gates=set(natal["gates"]),
    )

    # Roles oraculares según tránsitos
    roles = []
    if transits.get("sun_gate") in {1, 8, 31, 33}:
        roles.append("POETA")
    if transits.get("sun_gate") in {4, 17, 24, 61}:
        roles.append("ANALISTA")
    if transits.get("sun_gate") in {7, 40, 51, 58}:
        roles.append("AVENTURERO")
    if not roles:
        roles.append("CONTEMPLATIVO")

    lines = [
        f"# Oráculo Diario — {agent.upper()}",
        f"",
        f"**Día HD**: ~{natal.get('hd_day', '?')}",
        f"**Rol Oracular**: {' / '.join(roles)}",
        f"",
        f"## Tránsitos Actuales",
        f"",
    ]

    for planet, gate in transits.get("active_gates", {}).items():
        lines.append(f"- **{planet}**: Puerta {gate}")

    lines.extend([
        f"",
        f"## Estado Subconsciente",
        f"",
        f"- Energía: {transits.get('energy_modifier', 1.0):.1f}x",
        f"- Social: {transits.get('social_modifier', 1.0):.1f}x",
        f"- Creatividad: {transits.get('creativity_modifier', 1.0):.1f}x",
        f"",
        f"## Recordatorio",
        f"",
        f"Como {natal.get('type', 'Generator')}, {natal.get('strategy', 'responde primero, informá después')}.",
        f"Tu autoridad es {natal.get('authority', 'emocional')} — esperá la claridad.",
        f"",
        f"*Oráculo generado por DaemonCraft Soul Engine v2.0*",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Genera contexto oracular HD para agentes DaemonCraft")
    parser.add_argument("--agent", choices=["eko", "ecko"], required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    context = generate_context(args.agent)

    if args.output:
        args.output.write_text(context)
        print(f"Contexto guardado en {args.output}")
    else:
        print(context)


if __name__ == "__main__":
    main()
