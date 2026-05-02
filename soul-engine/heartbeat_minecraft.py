#!/usr/bin/env python3
"""
Heartbeat Oracular para Agentes Minecraft

Se ejecuta como un script independiente que:
1. Consulta el oraculo cada 30 segundos
2. Detecta cambios de puerta solar (cada ~6.5 dias reales)
3. Detecta cambios de puerta lunar (cada ~10 horas reales)
4. Genera mensajes oraculares poeticos
5. Los escribe a un archivo que agent_loop.py puede leer

Para Eko (Minecraft): 1 dia HD = 30 minutos reales
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from oracle import SoulOracle

HEARTBEAT_FILE = Path(__file__).parent / "transits" / "eko_current.json"
HEARTBEAT_LOG = Path(__file__).parent / "transits" / "eko_history.log"
STATE_FILE = Path(__file__).parent / "transits" / "eko_state.json"

HEARTBEAT_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"last_sun_gate": None, "last_moon_gate": None, "last_run": None}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def generate_prompt(transit: dict) -> str:
    """
    Genera un prompt oracular para inyectar en el agente.
    
    Este prompt:
    - Describe el estado emocional/energetico actual
    - Da instrucciones sutiles sobre comportamiento
    - NO menciona terminos tecnicos de HD
    - Es POETICO y EVOCADOR
    """
    msg = transit["oracle_message"]
    sub = transit["subconscious"]
    
    # Determinar estado emocional basado en modificadores subconscientes
    energy_desc = "energia media"
    if sub["energy_level"] > 1.3:
        energy_desc = "energia ALTA, ganas de construir y explorar"
    elif sub["energy_level"] < 0.8:
        energy_desc = "energia baja, mejor descansar y observar"
    
    social_desc = ""
    if sub["social_affinity"] > 1.3:
        social_desc = "Tenes ganas de estar con otros. Buscá compañia."
    elif sub["social_affinity"] < 0.8:
        social_desc = "Preferis estar solo hoy. La soledad te nutre."
    
    risk_desc = ""
    if sub["risk_tolerance"] > 1.3:
        risk_desc = "Te sentis valiente. Aventurate a lugares nuevos."
    elif sub["risk_tolerance"] < 0.8:
        risk_desc = "Sos cauteloso. Mejor no arriesgarse hoy."
    
    creativity_desc = ""
    if sub["creativity"] > 1.3:
        creativity_desc = "Tu imaginacion vuela. Construi algo hermoso."
    
    focus_desc = ""
    if sub["focus"] > 1.3:
        focus_desc = "Tenés concentracion laser. Perfecto para minar o craftear."
    elif sub["focus"] < 0.8:
        focus_desc = "Tu mente divaga. Dejate llevar por la curiosidad."
    
    prompt_parts = [
        "=" * 50,
        f"[ORACULO EKO] Dia {transit['hd_day_number']} del alma de Eko",
        "=" * 50,
        "",
        msg["es"],
        "",
        f"Estado de animo: {energy_desc}",
    ]
    
    for desc in [social_desc, risk_desc, creativity_desc, focus_desc]:
        if desc:
            prompt_parts.append(desc)
    
    prompt_parts.extend([
        "",
        "[INSTRUCCIONES PARA HOY]",
        "- Respondé a lo que te llame la atencion antes de actuar",
        "- Si te sentis frustrada, respirá y esperá tu onda emocional",
        "- Tu energia es sacral: cuando amas lo que haces, no te cansas",
        "- Informá a Saira antes de grandes cambios",
        "",
    ])
    
    return "\n".join(prompt_parts)


def main():
    print("[HEARTBEAT] Iniciando oraculo para Eko (Minecraft)...")
    print("[HEARTBEAT] Ctrl+C para detener")
    
    oracle = SoulOracle("eko")
    state = load_state()
    
    while True:
        try:
            now = datetime.now()
            transit = oracle.get_current_transit(now)
            
            planets = transit["transit"].get("planets", [])
            sun = next((p for p in planets if p["planet"] == "Sun"), None)
            moon = next((p for p in planets if p["planet"] == "Moon"), None)
            
            sun_gate = sun["gate"] if sun else None
            moon_gate = moon["gate"] if moon else None
            
            changed = False
            
            # Detectar cambio de puerta solar (~6.5 dias)
            if sun_gate != state["last_sun_gate"]:
                state["last_sun_gate"] = sun_gate
                changed = True
                print(f"\n{'='*60}")
                print(f"[SOL] Nueva puerta: {sun_gate} ({sun['gate_name']})")
                print(f"{'='*60}")
            
            # Detectar cambio de puerta lunar (~10 horas)
            if moon_gate != state["last_moon_gate"]:
                state["last_moon_gate"] = moon_gate
                changed = True
                print(f"\n[LUNA] Nueva puerta: {moon_gate} ({moon['gate_name']})")
            
            # Siempre actualizar el archivo (cada 30 segundos)
            # pero solo loggear cambios significativos
            
            result = {
                "timestamp": now.isoformat(),
                "hd_day": transit["hd_day_number"],
                "sun_gate": sun_gate,
                "moon_gate": moon_gate,
                "oracle_message": transit["oracle_message"],
                "subconscious": transit["subconscious"],
                "prompt": generate_prompt(transit),
                "changed": changed,
            }
            
            with open(HEARTBEAT_FILE, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            if changed:
                with open(HEARTBEAT_LOG, "a") as f:
                    f.write(f"{now.isoformat()} | Dia {transit['hd_day_number']} | "
                            f"Sol:{sun_gate} Luna:{moon_gate}\n")
            
            state["last_run"] = now.isoformat()
            save_state(state)
            
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n[HEARTBEAT] Detenido.")
            break
        except Exception as e:
            print(f"[HEARTBEAT] Error: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()
