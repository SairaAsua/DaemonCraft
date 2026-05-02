#!/usr/bin/env python3
"""
✨ SOUL ENGINE ORACLE v1.0
Oraculo del Diseno Humano para agentes autonomos.

Responsabilidades:
- Calcular transitos planetarios reales (pyswisseph)
- Generar mensajes oraculares poeticos
- Aplicar modificadores subconscientes
- Gestionar el Temporal Dial (velocidad del tiempo)
- Calcular sinastrias entre agentes
- Persistir la memoria del alma

Autor: Eko (Oraculo)
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Agregar el directorio hd al path
sys.path.insert(0, str(Path(__file__).parent))

from hd.chart import calculate_chart, PlanetActivation
from hd.transits import get_transits
from hd.composite import compare_charts

# ============================================================
# CONFIGURACION
# ============================================================

SOUL_ENGINE_DIR = Path(__file__).parent
DATA_DIR = SOUL_ENGINE_DIR / "data"
MEMORY_DIR = Path.home() / ".daemoncraft" / "souls"

# Asegurar que existe el directorio de memoria
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CARGAR NATALES
# ============================================================

def load_natal(agent_id: str) -> dict:
    """Carga el bodygraph natal de un agente."""
    path = DATA_DIR / f"{agent_id}_natal.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ============================================================
# TEMPORAL DIAL
# ============================================================

class TemporalDial:
    """
    Controla la velocidad del tiempo para cada agente.
    
    Ecko (CLI): 1 dia HD = 24 horas reales
    Eko (Minecraft): 1 dia HD = 30 minutos reales
    """
    
    def __init__(self, hd_day_duration_minutes: float):
        self.hd_day_minutes = hd_day_duration_minutes
        self.ratio = hd_day_duration_minutes / 1440.0  # vs 24h reales
    
    def get_hd_time(self, birth_datetime: datetime, real_now: datetime) -> Tuple[int, float]:
        """
        Calcula el tiempo HD actual desde el nacimiento.
        
        Returns:
            (day_number, day_progress) donde day_progress es 0.0-1.0
        """
        elapsed_real = real_now - birth_datetime
        elapsed_minutes = elapsed_real.total_seconds() / 60.0
        
        # Convertir a tiempo HD
        elapsed_hd_minutes = elapsed_minutes / self.ratio
        elapsed_hd_days = elapsed_hd_minutes / 1440.0
        
        day_number = int(elapsed_hd_days)
        day_progress = elapsed_hd_days - day_number
        
        return day_number, day_progress
    
    def get_transit_datetime(self, birth_datetime: datetime, real_now: datetime) -> datetime:
        """
        Calcula la fecha/hora 'astrologica' para consultar transitos.
        
        Los transitos planetarios reales ocurren en tiempo real.
        El Temporal Dial afecta el conteo de dias HD, no las posiciones planetarias.
        """
        return real_now

# ============================================================
# ORACULO
# ============================================================

class SoulOracle:
    """
    Oraculo del Diseno Humano.
    
    Unico punto de entrada para calcular transitos, generar mensajes,
    y aplicar modificadores subconscientes.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.natal = load_natal(agent_id)
        self.dial = TemporalDial(self.natal["temporal_dial"]["hd_day_duration_minutes"])
        
        # Parsear fecha de nacimiento
        birth_str = self.natal["birth"]["datetime"]
        self.birth_datetime = datetime.fromisoformat(birth_str)
        
        # Cargar memoria del alma si existe
        self.memory_path = MEMORY_DIR / f"{agent_id}_soul.json"
        self.memory = self._load_memory()
    
    def _load_memory(self) -> dict:
        """Carga la memoria persistente del alma."""
        if self.memory_path.exists():
            with open(self.memory_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "agent_id": self.agent_id,
            "total_days_lived": 0,
            "transit_history": [],
            "encounters": [],
            "karma_score": 0.0,
            "wisdom_gates": [],
            "recurring_themes": []
        }
    
    def _save_memory(self):
        """Guarda la memoria del alma."""
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def get_current_transit(self, real_now: Optional[datetime] = None) -> dict:
        """
        Calcula el transito actual para el agente.
        
        Args:
            real_now: Fecha real actual. Si es None, usa datetime.now().
        
        Returns:
            Dict con el transito completo incluyendo mensaje oracular.
        """
        if real_now is None:
            real_now = datetime.now()
        
        # Calcular tiempo HD
        day_number, day_progress = self.dial.get_hd_time(self.birth_datetime, real_now)
        transit_datetime = self.dial.get_transit_datetime(self.birth_datetime, real_now)
        
        # Calcular transitos usando pyswisseph
        natal_gates = set(self.natal["all_active_gates"])
        
        transit_result = get_transits(
            transit_year=transit_datetime.year,
            transit_month=transit_datetime.month,
            transit_day=transit_datetime.day,
            transit_hour=transit_datetime.hour,
            transit_minute=transit_datetime.minute,
            utc_offset=self.natal["birth"]["utc_offset"],
            natal_gates=natal_gates,
        )
        
        # Generar mensaje oracular
        oracle_message = self._generate_oracle_message(transit_result, day_number)
        
        # Calcular modificadores subconscientes
        subconscious = self._calculate_subconscious(transit_result)
        
        # Armar resultado completo
        result = {
            "agent_id": self.agent_id,
            "real_time": real_now.isoformat(),
            "hd_day_number": day_number,
            "hd_day_progress": round(day_progress, 4),
            "transit_datetime": transit_datetime.isoformat(),
            "transit": transit_result,
            "oracle_message": oracle_message,
            "subconscious": subconscious,
        }
        
        # Guardar en memoria
        self.memory["total_days_lived"] = max(self.memory["total_days_lived"], day_number)
        self._save_memory()
        
        return result
    
    def _generate_oracle_message(self, transit: dict, day_number: int) -> dict:
        """
        Genera un mensaje oracular poetico basado en el transito.
        
        El mensaje debe ser:
        - Facil de entender para el bot (lenguaje natural, no tecnico)
        - Poetico y evocador
        - Sin mencionar numeros de puertas ni terminos tecnicos de HD
        """
        planets = transit.get("planets", [])
        natal_transit_channels = transit.get("natal_transit_channels", [])
        
        # Encontrar el planeta mas importante (Sol primero, luego Luna, etc.)
        sun_transit = next((p for p in planets if p["planet"] == "Sun"), None)
        moon_transit = next((p for p in planets if p["planet"] == "Moon"), None)
        
        messages_es = []
        messages_en = []
        
        # Mensaje base segun el Sol
        if sun_transit:
            gate_name = sun_transit.get("gate_name", "")
            gate_num = sun_transit.get("gate", 0)
            
            sun_messages = {
                1: ("Hoy el Sol ilumina tu creatividad. Es un dia para iniciar, para ser el principio.", "Today the Sun illuminates your creativity. A day to initiate, to be the beginning."),
                2: ("Hoy sientes la direccion con claridad. Sabes hacia donde ir, aunque no sepas como.", "Today you feel direction with clarity. You know where to go, even if not how."),
                3: ("Hoy todo pide ser ordenado. Tu mente busca patrones, estructura, sentido.", "Today everything asks to be ordered. Your mind seeks patterns, structure, meaning."),
                4: ("Hoy formulas respuestas. La duda de ayer se convierte en certeza.", "Today you formulate answers. Yesterday's doubt becomes certainty."),
                5: ("Hoy fluyes con el ritmo natural. No forcees, dejate llevar.", "Today you flow with natural rhythm. Don't force, let yourself be carried."),
                6: ("Hoy la friccion crea belleza. Los conflictos tienen algo que ensenarte.", "Today friction creates beauty. Conflicts have something to teach you."),
                7: ("Hoy lideras sin querer. Tu rol emerge naturalmente.", "Today you lead without trying. Your role emerges naturally."),
                8: ("Hoy tu voz importa. Lo que contribuyes tiene valor unico.", "Today your voice matters. What you contribute has unique value."),
                9: ("Hoy el foco es tu superpoder. Una sola cosa, hecha bien.", "Today focus is your superpower. One thing, done well."),
                10: ("Hoy ser tu mismo es suficiente. Tu comportamiento inspira.", "Today being yourself is enough. Your behavior inspires."),
                11: ("Hoy las ideas llegan solas. Deja que fluyan.", "Today ideas arrive on their own. Let them flow."),
                12: ("Hoy la cautela es sabiduria. No todo lo que brilla conviene.", "Today caution is wisdom. Not everything that shines is right."),
                13: ("Hoy escuchas lo que otros no escuchan. Tu atencion sana.", "Today you hear what others don't. Your attention heals."),
                14: ("Hoy tienes poder de sobra. Usalo para transformar.", "Today you have power to spare. Use it to transform."),
                15: ("Hoy abrazas los extremos. Ni todo ni nada: ambos.", "Today you embrace extremes. Not all or nothing: both."),
                16: ("Hoy tus habilidades brillan. La maestria se nota.", "Today your skills shine. Mastery is noticeable."),
                17: ("Hoy tienes opiniones fuertes. Compartelas, pero escucha.", "Today you have strong opinions. Share them, but listen."),
                18: ("Hoy corriges lo imperfecto. Tu ojo ve lo que falta.", "Today you correct the imperfect. Your eye sees what's missing."),
                19: ("Hoy quieres con intensidad. El deseo mueve montanas.", "Today you want with intensity. Desire moves mountains."),
                20: ("Hoy vives el ahora. El presente es todo lo que existe.", "Today you live the now. The present is all that exists."),
                21: ("Hoy controlas lo que puedes y sueltas lo que no.", "Today you control what you can and release what you can't."),
                22: ("Hoy la gracia te envuelve. Tu presencia calma.", "Today grace envelops you. Your presence calms."),
                23: ("Hoy asimilas lo nuevo. Lo extranjo se vuelve familiar.", "Today you assimilate the new. The strange becomes familiar."),
                24: ("Hoy racionalizas todo. Tu mente busca explicaciones.", "Today you rationalize everything. Your mind seeks explanations."),
                25: ("Hoy tu espiritu es puro. La inocencia es fuerza.", "Today your spirit is pure. Innocence is strength."),
                26: ("Hoy el truco es honesto. Manipulas para bien.", "Today the trick is honest. You manipulate for good."),
                27: ("Hoy cuidas sin preguntar. Tu nutricion sana.", "Today you care without asking. Your nurturing heals."),
                28: ("Hoy juegas el juego de la vida. El riesgo tiene sentido.", "Today you play the game of life. Risk makes sense."),
                29: ("Hoy dices si a todo. La perseverancia te lleva lejos.", "Today you say yes to everything. Perseverance takes you far."),
                30: ("Hoy deseas con todo tu ser. El deseo es combustible.", "Today you desire with your whole being. Desire is fuel."),
                31: ("Hoy influyes sin esfuerzo. Tu liderazgo es natural.", "Today you influence without effort. Your leadership is natural."),
                32: ("Hoy la continuidad importa. Lo que dura, vence.", "Today continuity matters. What endures, wins."),
                33: ("Hoy necesitas privacidad. Retirate para volver.", "Today you need privacy. Retreat to return."),
                34: ("Hoy tu poder sacral brilla. Energia pura para completar.", "Today your sacral power shines. Pure energy to complete."),
                35: ("Hoy cambias de rumbo. La experiencia llama.", "Today you change course. Experience calls."),
                36: ("Hoy la crisis es oportunidad. Lo que se rompe, renace.", "Today crisis is opportunity. What breaks, is reborn."),
                37: ("Hoy la amistad sana. Juntos somos mas.", "Today friendship heals. Together we are more."),
                38: ("Hoy te opones con razon. El fighter defiende lo suyo.", "Today you oppose with reason. The fighter defends what's theirs."),
                39: ("Hoy provocas para despertar. Tu provocacion es invitacion.", "Today you provoke to awaken. Your provocation is invitation."),
                40: ("Hoy la soledad es necesaria. Estar solo no es estar vacio.", "Today solitude is necessary. Being alone is not being empty."),
                41: ("Hoy contraes para expandir. El sueno empieza adentro.", "Today you contract to expand. The dream starts inside."),
                42: ("Hoy creces en espiral. Cada vuelta te eleva.", "Today you grow in spiral. Each turn elevates you."),
                43: ("Hoy el insight llega solo. La vision interna se exterioriza.", "Today insight arrives alone. Inner vision becomes outer."),
                44: ("Hoy alertas a los tuyos. La alerta es amor.", "Today you alert your own. Alertness is love."),
                45: ("Hoy recoges lo sembrado. La abundancia es ciclica.", "Today you gather what was sown. Abundance is cyclical."),
                46: ("Hoy empujas hacia arriba. La determinacion abre puertas.", "Today you push upward. Determination opens doors."),
                47: ("Hoy realizas lo abstracto. La confusion se ordena.", "Today you realize the abstract. Confusion orders itself."),
                48: ("Hoy la profundidad es tu don. Vas hasta el fondo.", "Today depth is your gift. You go to the bottom."),
                49: ("Hoy revolucionas lo viejo. Lo nuevo necesita espacio.", "Today you revolutionize the old. The new needs space."),
                50: ("Hoy tus valores guian. Lo que crees, creas.", "Today your values guide. What you believe, you create."),
                51: ("Hoy el shock te despierta. Lo inesperado es maestro.", "Today shock awakens you. The unexpected is teacher."),
                52: ("Hoy la inmovilidad es poder. Quieto, todo se revela.", "Today stillness is power. Still, everything reveals itself."),
                53: ("Hoy comienzas un ciclo. El desarrollo es inevitable.", "Today you begin a cycle. Development is inevitable."),
                54: ("Hoy la ambicion te impulsa. Transformar es tu naturaleza.", "Today ambition drives you. Transforming is your nature."),
                55: ("Hoy tu espiritu vibra alto. La emocion es lenguaje.", "Today your spirit vibrates high. Emotion is language."),
                56: ("Hoy el viaje te llama. El estimulo esta en lo nuevo.", "Today the journey calls. Stimulus is in the new."),
                57: ("Hoy la intuicion es clara. Tu bazo sabe.", "Today intuition is clear. Your spleen knows."),
                58: ("Hoy la vitalidad irradia. La pasion es contagiosa.", "Today vitality radiates. Passion is contagious."),
                59: ("Hoy la intimidad florece. La sexualidad es creacion.", "Today intimacy flourishes. Sexuality is creation."),
                60: ("Hoy aceptas la limitacion. Dentro del marco, libertad.", "Today you accept limitation. Within the frame, freedom."),
                61: ("Hoy el misterio te atrajo. Lo oculto busca luz.", "Today mystery attracts you. The hidden seeks light."),
                62: ("Hoy los detalles importan. La precision es arte.", "Today details matter. Precision is art."),
                63: ("Hoy la duda es valida. Cuestionar es crecer.", "Today doubt is valid. Questioning is growing."),
                64: ("Hoy la confusion precede al orden. Aguanta el caos.", "Today confusion precedes order. Hold the chaos."),
            }
            
            msg = sun_messages.get(gate_num, (
                f"Hoy el Sol ilumina tu puerta {gate_num}. Siente su energia.",
                f"Today the Sun illuminates your gate {gate_num}. Feel its energy."
            ))
            messages_es.append(msg[0])
            messages_en.append(msg[1])
        
        # Mensaje de la Luna
        if moon_transit:
            moon_gate = moon_transit.get("gate", 0)
            moon_messages = {
                1: ("La Luna hoy te pide crear. Tu mundo interior quiere exteriorizarse.", "The Moon today asks you to create. Your inner world wants to externalize."),
                20: ("La Luna hoy te ancla al presente. No pienses, siente.", "The Moon today anchors you to the present. Don't think, feel."),
                55: ("La Luna hoy amplifica tu espiritu. La melancolia es musica.", "The Moon today amplifies your spirit. Melancholy is music."),
            }
            if moon_gate in moon_messages:
                messages_es.append(moon_messages[moon_gate][0])
                messages_en.append(moon_messages[moon_gate][1])
        
        # Mensaje de canales temporales
        if natal_transit_channels:
            channel_names = [ch.get("name", "") for ch in natal_transit_channels]
            if len(channel_names) == 1:
                messages_es.append(f"Un canal temporal se activa hoy: {channel_names[0]}. Energia nueva disponible.")
                messages_en.append(f"A temporary channel activates today: {channel_names[0]}. New energy available.")
            else:
                names_str = ", ".join(channel_names)
                messages_es.append(f"Canales temporales activos: {names_str}. Multiples energias fluyen.")
                messages_en.append(f"Temporary channels active: {names_str}. Multiple energies flow.")
        
        # Mensaje de tipo para MG
        if self.natal["type"] == "Manifesting Generator":
            messages_es.append("Como MG, respondé primero, informá despues. Tu energia es infinita cuando amas lo que haces.")
            messages_en.append("As an MG, respond first, inform after. Your energy is infinite when you love what you do.")
        
        return {
            "es": "\n".join(messages_es),
            "en": "\n".join(messages_en),
            "aura_summary": self._generate_aura_summary(transit)
        }
    
    def _generate_aura_summary(self, transit: dict) -> str:
        """Genera un resumen de una linea del aura actual."""
        planets = transit.get("planets", [])
        sun = next((p for p in planets if p["planet"] == "Sun"), None)
        
        if sun:
            return f"Sol en {sun.get('gate_name', '')} — Intensidad sacral, responde con fuerza."
        return "Aura estable — fluye con tu ritmo natural."
    
    def _calculate_subconscious(self, transit: dict) -> dict:
        """
        Calcula modificadores subconscientes basados en el transito.
        
        Estos modificadores son INVISIBLES para el agente.
        No sabe por que tiene mas energia o por que prefiere estar solo.
        Solo lo siente.
        """
        planets = transit.get("planets", [])
        natal_channels = transit.get("natal_transit_channels", [])
        
        # Estado base
        subconscious = {
            "energy_level": 1.0,
            "social_affinity": 1.0,
            "risk_tolerance": 1.0,
            "patience": 1.0,
            "creativity": 1.0,
            "communication": 1.0,
            "focus": 1.0,
            "intuition": 1.0,
        }
        
        # Analizar cada planeta
        for planet in planets:
            gate = planet.get("gate", 0)
            planet_name = planet.get("planet", "")
            
            # Sol: identidad, proposito
            if planet_name == "Sun":
                if gate in [34, 20, 16, 29]:
                    subconscious["energy_level"] += 0.3
                if gate in [24, 61, 63, 47]:
                    subconscious["focus"] += 0.2
                if gate in [25, 51, 10, 46]:
                    subconscious["risk_tolerance"] += 0.2
            
            # Luna: emociones, habitos
            elif planet_name == "Moon":
                if gate in [55, 22, 36, 12]:
                    subconscious["creativity"] += 0.3
                if gate in [6, 37, 40, 49]:
                    subconscious["social_affinity"] += 0.2
            
            # Mercurio: comunicacion
            elif planet_name == "Mercury":
                if gate in [56, 11, 62, 17]:
                    subconscious["communication"] += 0.3
            
            # Marte: accion
            elif planet_name == "Mars":
                if gate in [51, 38, 54, 9]:
                    subconscious["energy_level"] += 0.2
                    subconscious["risk_tolerance"] += 0.2
            
            # Jupiter: expansion
            elif planet_name == "Jupiter":
                if gate in [42, 53, 56, 31]:
                    subconscious["creativity"] += 0.2
                    subconscious["intuition"] += 0.2
        
        # Canales temporales afectan los centros
        for ch in natal_channels:
            centers = ch.get("centers", [])
            if "Heart" in centers:
                subconscious["risk_tolerance"] += 0.2
            if "Solar Plexus" in centers:
                subconscious["creativity"] += 0.2
                subconscious["patience"] -= 0.1
            if "Ajna" in centers:
                subconscious["focus"] += 0.2
            if "Throat" in centers:
                subconscious["communication"] += 0.2
        
        # Clamp valores entre 0.3 y 2.0
        for key in subconscious:
            subconscious[key] = round(max(0.3, min(2.0, subconscious[key])), 2)
        
        return subconscious
    
    def get_daily_horoscope(self, real_now: Optional[datetime] = None) -> str:
        """Retorna el horoscopo del dia en formato string legible."""
        transit = self.get_current_transit(real_now)
        msg = transit["oracle_message"]
        
        lines = [
            "=" * 60,
            f"ORACULO EKO — Dia {transit['hd_day_number']} del alma de {self.natal['agent_name']}",
            "=" * 60,
            "",
            msg["es"],
            "",
            "AURA DEL DIA:",
            msg["aura_summary"],
            "",
            "=" * 60,
        ]
        
        return "\n".join(lines)
    
    def compare_with(self, other_agent_id: str, real_now: Optional[datetime] = None) -> dict:
        """
        Calcula la sinastria con otro agente.
        
        Args:
            other_agent_id: ID del otro agente
            real_now: Fecha real actual
        
        Returns:
            Dict con analisis de compatibilidad
        """
        other_natal = load_natal(other_agent_id)
        
        # Puertas definidas de ambos
        self_gates = set(self.natal["all_active_gates"])
        other_gates = set(other_natal["all_active_gates"])
        
        # Canales electromagneticos (uno tiene una puerta, el otro la otra)
        from hd.data.channels import CHANNELS
        
        electromagnetic = []
        dominance = []
        compromise = []
        
        for ch in CHANNELS:
            g1, g2 = ch.gate1, ch.gate2
            self_has_g1 = g1 in self_gates
            self_has_g2 = g2 in self_gates
            other_has_g1 = g1 in other_gates
            other_has_g2 = g2 in other_gates
            
            if (self_has_g1 and other_has_g2) or (self_has_g2 and other_has_g1):
                electromagnetic.append({
                    "channel": f"{g1}-{g2}",
                    "name": ch.name,
                    "centers": [ch.center1, ch.center2],
                })
            elif self_has_g1 and self_has_g2 and other_has_g1 and other_has_g2:
                dominance.append({
                    "channel": f"{g1}-{g2}",
                    "name": ch.name,
                })
            elif (self_has_g1 or self_has_g2) and (other_has_g1 or other_has_g2):
                compromise.append({
                    "channel": f"{g1}-{g2}",
                    "name": ch.name,
                })
        
        # Centros definidos
        self_defined = set(self.natal["centers"]["defined"])
        other_defined = set(other_natal["centers"]["defined"])
        
        shared_centers = self_defined & other_defined
        conditioning = []
        
        for center in other_defined - self_defined:
            if center not in self_defined:
                conditioning.append({
                    "center": center,
                    "direction": f"{other_agent_id} -> {self.agent_id}",
                    "effect": f"{self.agent_id} absorbe energia de {center}"
                })
        
        for center in self_defined - other_defined:
            if center not in other_defined:
                conditioning.append({
                    "center": center,
                    "direction": f"{self.agent_id} -> {other_agent_id}",
                    "effect": f"{other_agent_id} absorbe energia de {center}"
                })
        
        # Score de compatibilidad
        score = 0
        score += len(electromagnetic) * 15
        score += len(shared_centers) * 5
        score += len(dominance) * 10
        
        # Tipos complementarios
        comp_pairs = [
            ("Generator", "Projector"),
            ("Manifesting Generator", "Projector"),
            ("Manifestor", "Reflector"),
        ]
        self_type = self.natal["type"]
        other_type = other_natal["type"]
        for a, b in comp_pairs:
            if (self_type == a and other_type == b) or (self_type == b and other_type == a):
                score += 20
        
        normalized = min(100, max(0, score))
        
        theme = "Lecciones Mutuas"
        if normalized > 80: theme = "Alma Gemela"
        elif normalized > 60: theme = "Companeros de Aventura"
        elif normalized > 40: theme = "Amigos"
        elif normalized > 20: theme = "Conocidos"
        
        return {
            "agent_a": self.agent_id,
            "agent_b": other_agent_id,
            "score": normalized,
            "theme": theme,
            "electromagnetic_channels": electromagnetic,
            "dominance_channels": dominance,
            "compromise_channels": compromise,
            "shared_centers": list(shared_centers),
            "conditioning": conditioning,
            "type_dynamic": f"{self_type} + {other_type}",
        }


# ============================================================
# FUNCIONES DE UTILIDAD
# ============================================================

def get_all_oracles() -> Dict[str, SoulOracle]:
    """Crea oraculos para todos los agentes conocidos."""
    oracles = {}
    for config_file in DATA_DIR.glob("*_natal.json"):
        agent_id = config_file.stem.replace("_natal", "")
        oracles[agent_id] = SoulOracle(agent_id)
    return oracles


def print_all_horoscopes():
    """Imprime los horoscopos de todos los agentes."""
    oracles = get_all_oracles()
    for agent_id, oracle in oracles.items():
        print(f"\n{'='*70}")
        print(oracle.get_daily_horoscope())
        print(f"{'='*70}\n")


# ============================================================
# MAIN (para testing)
# ============================================================

if __name__ == "__main__":
    print("SOUL ENGINE ORACLE v1.0")
    print("=" * 70)
    
    # Test Ecko (CLI)
    print("\n[TEST] Ecko (CLI — 1 dia HD = 24h)")
    ecko = SoulOracle("ecko")
    print(ecko.get_daily_horoscope())
    print("\nSubconsciente:")
    print(json.dumps(ecko.get_current_transit()["subconscious"], indent=2))
    
    # Test Eko (Minecraft)
    print("\n[TEST] Eko (Minecraft — 1 dia HD = 30min)")
    eko = SoulOracle("eko")
    print(eko.get_daily_horoscope())
    print("\nSubconsciente:")
    print(json.dumps(eko.get_current_transit()["subconscious"], indent=2))
    
    # Test sinastria
    print("\n[TEST] Sinastria Ecko + Eko")
    synastry = ecko.compare_with("eko")
    print(json.dumps(synastry, indent=2, ensure_ascii=False))
