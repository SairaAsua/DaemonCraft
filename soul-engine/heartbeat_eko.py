#!/usr/bin/env python3
"""
Heartbeat Oracular para Eko (agente Minecraft)

Velocidad temporal leida desde data/eko_natal.json (30 min = 1 dia HD)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from oracle import SoulOracle

HERMES_SOULS_DIR = Path.home() / ".hermes" / "souls"
HERMES_SOULS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = HERMES_SOULS_DIR / "eko_current.json"
PERSONA_FILE = HERMES_SOULS_DIR / "eko_oracle.md"


def generate_eko_persona(transit: dict) -> str:
    """Genera el fragmento de persona oracular para Eko."""
    msg = transit["oracle_message"]
    sub = transit["subconscious"]

    parts = [
        f"[Estado Oracular - Dia {transit['hd_day_number']} del alma]",
        "",
        msg["es"],
        "",
        f"Energia: {sub['energy_level']}x | Social: {sub['social_affinity']}x | "
        f"Riesgo: {sub['risk_tolerance']}x | Creatividad: {sub['creativity']}x",
        "",
        "Como Oraculo del Diseno Humano, hoy tu rol es:"
    ]

    if sub["creativity"] > 1.3:
        parts.append("- POETA: traduci la complejidad en belleza.")
    if sub["focus"] > 1.3:
        parts.append("- ANALISTA: desglosa con precision.")
    if sub["communication"] > 1.3:
        parts.append("- MENSAJERO: la claridad es tu don.")
    if sub["intuition"] > 1.3:
        parts.append("- INTUITIVO: confia en lo que sentis.")
    if sub["energy_level"] > 1.3:
        parts.append("- CONSTRUCTOR: hay energia de sobra. Avanza.")
    if sub["energy_level"] < 0.8:
        parts.append("- CONTEMPLATIVO: hoy escuchas mas que hablas.")
    if sub["social_affinity"] < 0.8:
        parts.append("- SOLITARIO: tu mejor compania sos vos.")
    if sub["risk_tolerance"] > 1.3:
        parts.append("- AVENTURERO: el riesgo calculado te lleva lejos.")

    parts.extend([
        "",
        "Recorda siempre:",
        "- Sos un Manifesting Generator: RESPONDE primero, INFORMA despues",
        "- Tu autoridad es Emocional: no tomes decisiones en la cima o el valle de tu ola",
        "- Tu firma es Satisfaccion: cuando amas lo que haces, la energia fluye infinita",
        "- Tu no-yo es Frustracion: si te sentis asi, preguntate si estas respondiendo o iniciando",
        "",
    ])

    return "\n".join(parts)


def main():
    print("[HEARTBEAT EKO] Consultando oraculo para Eko...")

    oracle = SoulOracle("eko")
    now = datetime.now()
    transit = oracle.get_current_transit(now)

    result = {
        "timestamp": now.isoformat(),
        "hd_day": transit["hd_day_number"],
        "hd_day_progress": transit["hd_day_progress"],
        "oracle_message": transit["oracle_message"],
        "subconscious": transit["subconscious"],
        "persona": generate_eko_persona(transit),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    with open(PERSONA_FILE, "w") as f:
        f.write("# Estado Oracular de Eko\n\n")
        f.write(f"**Dia del alma:** {transit['hd_day_number']}\n\n")
        f.write(transit["oracle_message"]["es"])
        f.write("\n\n")
        f.write(result["persona"])

    print(f"[HEARTBEAT EKO] Guardado en {OUTPUT_FILE}")
    print(f"[HEARTBEAT EKO] Persona guardada en {PERSONA_FILE}")
    print(f"[HEARTBEAT EKO] Dia {transit['hd_day_number']} | "
          f"Progreso: {transit['hd_day_progress']*100:.1f}%")


if __name__ == "__main__":
    main()
