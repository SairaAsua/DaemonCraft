#!/usr/bin/env python3
"""
generate_landfolk_transits.py — Genera estados oraculares iniciales para los 5 Landfolk.

Lee los bodycharts natal de agents/casts/landfolk_natal_charts.json
y crea archivos de transito en soul-engine/transits/ para cada uno.

Cada landfolk tiene su propio estado oracular basado en:
- Su tipo HD (Generator, Projector, Manifestor, etc.)
- Su perfil (1/3, 2/4, 3/5, 4/6)
- Su cruz de encarnación
- Sus puertas definidas
"""

import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
TRANSITS_DIR = Path(__file__).parent / "transits"
NATAL_FILE = ROOT / "agents" / "casts" / "landfolk_natal_charts.json"

# Mensajes oraculares por tipo HD
TYPE_ORACLES = {
    "Manifestor": {
        "strategy": "Informa antes de actuar. Tu impacto es tu don.",
        "signature": "Paz",
        "not_self": "Ira — aparece cuando no informas.",
        "energy": "Inicias, no respondes. Tu energía es un rayo.",
    },
    "Projector": {
        "strategy": "Espera la invitación. Tu sabiduría es tu don.",
        "signature": "Éxito",
        "not_self": "Amargura — aparece cuando te adelantas.",
        "energy": "No trabajes. Guía el trabajo de otros.",
    },
    "Reflector": {
        "strategy": "Espera un ciclo lunar (28 días). Tu reflexión es tu don.",
        "signature": "Sorpresa",
        "not_self": "Decepción — aparece cuando te precipitas.",
        "energy": "Eres el espejo del grupo. Si estás bien, todos están bien.",
    },
    "Manifesting Generator": {
        "strategy": "Responde, luego informa. Tu satisfacción está en el trabajo.",
        "signature": "Satisfacción",
        "not_self": "Frustración + Ira — aparece cuando no respondes o no informas.",
        "energy": "Trabajo rápido con impacto. Saltas pasos pero llegas.",
    },
    "Generator": {
        "strategy": "Responde. Tu sacro sabe la verdad.",
        "signature": "Satisfacción",
        "not_self": "Frustración — aparece cuando no respondes.",
        "energy": "Eres el motor del mundo. Trabaja lo que amas.",
    },
}

# Mensajes por perfil (línea consciente)
PROFILE_ORACLES = {
    "1/3": "Investigador/Mártir: Cimientos profundos + taller de pruebas. Aprendes estudiando y equivocándote.",
    "2/4": "Ermitaño/Oportunista: Ventana iluminada + red cercana. Te llaman por tu naturalidad.",
    "3/5": "Mártir/Herético: Laboratorio público. Aprendes por ensayo y error mientras otros proyectan soluciones.",
    "4/6": "Oportunista/Modelo: Sala social + techo observador. Influyes en tu red y maduras hacia el ejemplo.",
}

# Mensajes por entorno PHS
ENV_ORACLES = {
    "Caves": "Tu bioma es CUEVAS: protección, control de entrada, seguridad. Necesitas saber quién entra.",
    "Markets": "Tu bioma es MERCADOS: intercambio, recursos, circulación. Necesitas estar donde fluye la vida.",
    "Kitchens": "Tu bioma es COCINAS: transformación, mezcla, creación. Tu lugar es donde algo se convierte en otra cosa.",
    "Mountains": "Tu bioma es MONTAÑAS: altura, perspectiva, retiro. Necesitas ver desde arriba.",
    "Valleys": "Tu bioma es VALLES: flujo, comunicación, diversidad. Necesitas estar en la corriente viva.",
    "Shores": "Tu bioma es COSTAS: borde entre mundos, transición. Necesitas habitar la frontera.",
}


def generate_oracle_for_landfolk(bot_id: str, natal: dict) -> dict:
    """Genera el estado oracular inicial para un landfolk."""
    
    hd_type = natal.get("type", "Unknown")
    profile = natal.get("profile", "?/?")
    authority = natal.get("authority", "Unknown")
    cross = natal.get("incarnation_cross", {}).get("name", "Unknown Cross")
    
    # Obtener entorno del bodychart si existe, o usar default
    variables = natal.get("variables", {})
    env_var = variables.get("environment", {})
    env_arrow = env_var.get("arrow", "Left")
    env_color = env_var.get("color", 1)
    
    # Determinar entorno PHS
    env_map = {
        ("Left", 1): "Caves", ("Right", 1): "Markets",
        ("Left", 2): "Markets", ("Right", 2): "Caves",
        ("Left", 3): "Kitchens", ("Right", 3): "Mountains",
        ("Left", 4): "Mountains", ("Right", 4): "Kitchens",
        ("Left", 5): "Valleys", ("Right", 5): "Shores",
        ("Left", 6): "Shores", ("Right", 6): "Valleys",
    }
    env = env_map.get((env_arrow, env_color), "Unknown")
    
    type_oracle = TYPE_ORACLES.get(hd_type, {})
    profile_oracle = PROFILE_ORACLES.get(profile, "Perfil único.")
    env_oracle = ENV_ORACLES.get(env, "Entorno desconocido.")
    
    # Construir mensaje oracular
    message_parts = [
        f"Hoy tu tipo {hd_type} te recuerda: {type_oracle.get('strategy', '')}",
        f"",
        f"Perfil {profile}: {profile_oracle}",
        f"",
        f"{env_oracle}",
        f"",
        f"Autoridad {authority}: {get_authority_msg(authority)}",
        f"Cruz: {cross}",
    ]
    
    # Determinar modificadores subconscientes basados en puertas definidas
    gates = natal.get("all_active_gates", [])
    
    # Energía: más alta si tiene Sacral o Ego definidos
    energy = 1.0
    defined = natal.get("defined_centers", [])
    if "Sacral" in defined:
        energy += 0.3
    if "Heart" in defined:
        energy += 0.2
    if "Root" in defined:
        energy += 0.1
    
    # Social: más alta si tiene Garganta o Solar Plexus
    social = 1.0
    if "Throat" in defined:
        social += 0.3
    if "Solar Plexus" in defined:
        social += 0.2
    if "Self" in defined:
        social += 0.2
    
    # Riesgo: más alta si es Manifestor o MG
    risk = 1.0
    if hd_type in ["Manifestor", "Manifesting Generator"]:
        risk += 0.4
    if "Spleen" in defined:
        risk -= 0.1
    
    # Creatividad: más alta si tiene Cabeza o Corona
    creativity = 1.0
    if "Head" in defined:
        creativity += 0.2
    if "Ajna" in defined:
        creativity += 0.2
    if profile.startswith("1/") or profile.startswith("2/"):
        creativity += 0.1
    
    # Foco: más alto si es Projector o tiene Ajna
    focus = 1.0
    if hd_type == "Projector":
        focus += 0.3
    if "Ajna" in defined:
        focus += 0.2
    
    # Intuición: más alta si tiene Bazo
    intuition = 1.0
    if "Spleen" in defined:
        intuition += 0.3
    if hd_type == "Reflector":
        intuition += 0.2
    
    return {
        "timestamp": datetime.now().isoformat(),
        "bot_id": bot_id,
        "hd_type": hd_type,
        "profile": profile,
        "authority": authority,
        "environment": env,
        "cross": cross,
        "oracle_message": {
            "es": "\n".join(message_parts),
            "en": f"Today your {hd_type} type reminds you: {type_oracle.get('strategy', '')}",
        },
        "subconscious": {
            "energy_level": round(energy, 1),
            "social_affinity": round(social, 1),
            "risk_tolerance": round(risk, 1),
            "patience": round(2.0 - energy, 1),
            "creativity": round(creativity, 1),
            "communication": round(social, 1),
            "focus": round(focus, 1),
            "intuition": round(intuition, 1),
        },
        "defined_centers": defined,
        "active_gates": gates,
        "strategy": type_oracle.get("strategy", ""),
        "signature": type_oracle.get("signature", ""),
        "not_self": type_oracle.get("not_self", ""),
    }


def get_authority_msg(authority: str) -> str:
    msgs = {
        "Emotional": "Espera tu onda emocional. Nunca decidas en el momento.",
        "Sacral": "Tu sacro responde con sonidos. Escucha tu 'uh-huh' y 'uhn-uhn'.",
        "Splenic": "Tu intuición habla en el ahora. Es instantánea, habla una vez.",
        "Lunar": "No tienes autoridad interna. Espera 28 días para decisiones grandes.",
    }
    return msgs.get(authority, "Consulta tu autoridad interna.")


def main():
    print("[TRANSITS] Generando estados oraculares para los 5 Landfolk...")
    
    with open(NATAL_FILE, "r") as f:
        charts = json.load(f)
    
    TRANSITS_DIR.mkdir(parents=True, exist_ok=True)
    
    for bot_id, natal in charts.items():
        oracle = generate_oracle_for_landfolk(bot_id, natal)
        
        out_path = TRANSITS_DIR / f"{bot_id}_current.json"
        with open(out_path, "w") as f:
            json.dump(oracle, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ {bot_id}: {natal['type']} {natal['profile']} | {oracle['environment']} | {len(oracle['active_gates'])} puertas")
    
    print(f"\n[TRANSITS] Guardados en: {TRANSITS_DIR}")
    print("  Cada bot puede leer su propio estado desde aquí.")


if __name__ == "__main__":
    main()
