#!/usr/bin/env python3
"""
DaemonCraft Video AI Editor
============================
Pipeline completo de edición de video con inteligencia artificial.

Entiende el contenido visual y auditivo, selecciona las mejores escenas
con coherencia narrativa (inicio, nudo, desenlace), edita para redes sociales,
y genera descripciones para Telegram.

Autor: Eko ♡
"""

import os
import sys
import json
import math
import time
import shutil
import tempfile
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Añadir path del plugin
sys.path.insert(0, str(Path(__file__).parent.parent))

# ──────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────────────────────

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.10.20.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b-it-q8_0")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "/usr/bin/ffprobe"

# Segmentación
SEGMENT_DURATION = 10  # segundos por segmento para análisis
FRAME_SAMPLE_RATE = 1  # 1 frame por segmento

# Pesos para scoring de escenas
SCORE_WEIGHTS = {
    "dialogue": 1.5,      # Diálogo con el bot es valioso
    "action": 1.3,        # Acción (combate, construcción)
    "emotion": 1.4,       # Emoción detectada
    "visual_interest": 1.0,  # Interés visual
    "audio_clarity": 0.8,    # Claridad del audio
    "narrative_importance": 2.0,  # Importancia para la historia
}

# Estructura narrativa
NARRATIVE_RATIO = {
    "setup": 0.15,      # Presentación/contexto
    "rising": 0.35,     # Desarrollo/acción
    "climax": 0.30,     # Clímax/momentos álgidos
    "falling": 0.15,    # Desenlace
    "resolution": 0.05  # Cierre/saludo final
}

# Redes sociales
SOCIAL_CUTS = {
    "min_clip_duration": 1.5,   # Mínimo segundos por clip
    "max_clip_duration": 8.0,   # Máximo segundos antes de cortar
    "jump_cut_threshold": 3.0,  # Umbral para jump cuts
    "subtitle_font": "Arial",
    "subtitle_size": 24,
    "subtitle_color": "white",
    "subtitle_outline": "black",
}


# ──────────────────────────────────────────────────────────────
# DATA CLASSES
# ──────────────────────────────────────────────────────────────

@dataclass
class VideoSegment:
    """Un segmento de video analizado"""
    start_time: float
    end_time: float
    frame_path: Optional[str] = None
    transcript: str = ""
    visual_description: str = ""
    audio_description: str = ""
    narrative_tag: str = ""        # setup, rising, climax, falling, resolution
    emotional_tone: str = ""       # excited, calm, tense, funny, epic
    contains_dialogue: bool = False
    contains_action: bool = False
    contains_building: bool = False
    contains_combat: bool = False
    interest_score: float = 0.0
    selected: bool = False

@dataclass
class NarrativeStructure:
    """Estructura narrativa detectada en el video"""
    title: str = ""
    summary: str = ""
    theme: str = ""
    segments: List[VideoSegment] = field(default_factory=list)
    setup_segments: List[int] = field(default_factory=list)
    rising_segments: List[int] = field(default_factory=list)
    climax_segments: List[int] = field(default_factory=list)
    falling_segments: List[int] = field(default_factory=list)
    resolution_segments: List[int] = field(default_factory=list)
    opening_greeting: Optional[Tuple[float, float]] = None
    closing_greeting: Optional[Tuple[float, float]] = None
    key_moments: List[Dict] = field(default_factory=list)

@dataclass
class EditDecision:
    """Decisión de edición para un clip"""
    source_path: str
    start_time: float
    end_time: float
    transition_type: str = "cut"   # cut, fade, zoom_in, zoom_out
    subtitle_text: str = ""
    speed_factor: float = 1.0      # 1.0 = normal, 1.5 = rápido
    audio_boost: float = 1.0
    effect: str = ""               # meme_zoom, slow_mo, glitch


# ──────────────────────────────────────────────────────────────
# UTILIDADES FFMPEG
# ──────────────────────────────────────────────────────────────

def ffprobe_json(path: str) -> dict:
    """Extrae información del video con ffprobe"""
    cmd = [
        FFPROBE_PATH, "-v", "error",
        "-show_format", "-show_streams",
        "-of", "json", path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def get_video_duration(path: str) -> float:
    """Duración del video en segundos"""
    info = ffprobe_json(path)
    return float(info["format"]["duration"])

def extract_frame_at(video_path: str, timestamp: float, output_path: str) -> bool:
    """Extrae un frame en un timestamp específico"""
    cmd = [
        FFMPEG_PATH, "-y", "-ss", str(timestamp),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and os.path.exists(output_path)

def extract_audio_segment(video_path: str, start: float, end: float, output_path: str) -> bool:
    """Extrae el audio de un segmento"""
    duration = end - start
    cmd = [
        FFMPEG_PATH, "-y", "-ss", str(start),
        "-t", str(duration),
        "-i", video_path,
        "-vn", "-acodec", "libmp3lame",
        "-q:a", "4",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio usando Whisper (si está disponible)"""
    try:
        import whisper
        model = whisper.load_model(WHISPER_MODEL)
        result = model.transcribe(audio_path, language="es", fp16=False)
        return result.get("text", "").strip()
    except ImportError:
        print("[VideoAI]   Whisper no disponible, saltando transcripción")
        return ""
    except Exception as e:
        print(f"[VideoAI] Whisper error: {e}")
        return ""


def query_ollama(prompt: str, images: List[str] = None, model: str = None) -> str:
    """Consulta Ollama. Soporta visión multimodal si se pasan imágenes."""
    import requests
    
    m = model or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/generate"
    
    payload = {
        "model": m,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 2048}
    }
    
    # Si hay imágenes, usar formato de visión de Ollama
    if images:
        import base64
        image_data = []
        for img_path in images:
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    image_data.append(base64.b64encode(f.read()).decode())
        if image_data:
            payload["images"] = image_data
    
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        print(f"[VideoAI] Ollama error: {e}")
        return ""


# ──────────────────────────────────────────────────────────────
# ANALIZADOR NARRATIVO
# ──────────────────────────────────────────────────────────────

class NarrativeAnalyzer:
    """
    Analiza el video completo para entender su estructura narrativa.
    Extrae frames, transcribe audio, y usa IA para clasificar cada segmento.
    """
    
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir = self.work_dir / "frames"
        self.frames_dir.mkdir(exist_ok=True)
        self.audio_dir = self.work_dir / "audio_segments"
        self.audio_dir.mkdir(exist_ok=True)
    
    def analyze(self, video_path: str) -> NarrativeStructure:
        """Analiza el video completo y devuelve estructura narrativa"""
        print(f"[VideoAI] 🔮 Analizando narrativa de: {video_path}")
        
        duration = get_video_duration(video_path)
        print(f"[VideoAI]   Duración: {duration:.1f}s")
        
        # 1. Dividir en segmentos
        num_segments = int(duration / SEGMENT_DURATION)
        segments: List[VideoSegment] = []
        
        for i in range(num_segments):
            start = i * SEGMENT_DURATION
            end = min((i + 1) * SEGMENT_DURATION, duration)
            seg = VideoSegment(start_time=start, end_time=end)
            segments.append(seg)
            
            # Extraer frame representativo
            frame_path = self.frames_dir / f"frame_{i:04d}.jpg"
            if extract_frame_at(video_path, (start + end) / 2, str(frame_path)):
                seg.frame_path = str(frame_path)
            
            # Extraer y transcribir audio
            audio_path = self.audio_dir / f"audio_{i:04d}.mp3"
            if extract_audio_segment(video_path, start, end, str(audio_path)):
                seg.transcript = transcribe_audio(str(audio_path))
                seg.contains_dialogue = len(seg.transcript) > 5
        
        print(f"[VideoAI]   {len(segments)} segmentos creados")
        
        # 2. Analizar cada segmento con IA
        self._analyze_segments_with_ai(segments)
        
        # 3. Calcular scores de interés
        self._score_segments(segments)
        
        # 4. Detectar estructura narrativa
        narrative = self._detect_narrative_structure(segments, duration)
        
        return narrative
    
    def _analyze_segments_with_ai(self, segments: List[VideoSegment]):
        """Analiza cada segmento con IA (visión + texto)"""
        
        # Prompt para análisis de segmento de Minecraft
        ANALYSIS_PROMPT = """Eres un editor de video profesional especializado en contenido de Minecraft y gameplay.

Analiza este segmento de video de Minecraft y describe:
1. ¿Qué se ve visualmente? (construcciones, paisajes, combates, exploración)
2. ¿Qué dice el audio/transcripción? (diálogos, reacciones, comentarios)
3. ¿Cuál es el tono emocional? (emocionante, tranquilo, cómico, épico, tenso)
4. ¿Hay acción importante? (combate, construcción, descubrimiento, muerte)
5. ¿Es un momento clave para la narrativa?

Transcripción del audio:
{transcript}

Responde EXACTAMENTE en este formato JSON (sin markdown, sin explicaciones):
{{
  "visual": "descripción visual detallada",
  "audio": "descripción del audio",
  "tone": "excited|calm|funny|epic|tense|nostalgic",
  "has_action": true|false,
  "has_building": true|false,
  "has_combat": true|false,
  "is_key_moment": true|false,
  "narrative_importance": 1-10,
  "suggested_tag": "setup|rising|climax|falling|resolution"
}}"""
        
        for i, seg in enumerate(segments):
            prompt = ANALYSIS_PROMPT.format(transcript=seg.transcript or "[sin audio]")
            
            # Intentar análisis con imagen si tenemos visión
            images = [seg.frame_path] if seg.frame_path and os.path.exists(seg.frame_path) else []
            
            print(f"[VideoAI]   Analizando segmento {i+1}/{len(segments)}...")
            response = query_ollama(prompt, images=images)
            
            # Parsear respuesta JSON
            try:
                # Limpiar posible markdown
                json_str = response
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0]
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0]
                
                data = json.loads(json_str.strip())
                
                seg.visual_description = data.get("visual", "")
                seg.audio_description = data.get("audio", "")
                seg.emotional_tone = data.get("tone", "calm")
                seg.contains_action = data.get("has_action", False)
                seg.contains_building = data.get("has_building", False)
                seg.contains_combat = data.get("has_combat", False)
                seg.narrative_tag = data.get("suggested_tag", "rising")
                seg.interest_score = data.get("narrative_importance", 5) / 10.0
                
            except Exception as e:
                print(f"[VideoAI]     Error parseando análisis: {e}")
                seg.narrative_tag = "rising"
                seg.interest_score = 0.5
            
            time.sleep(0.5)  # No saturar Ollama
    
    def _score_segments(self, segments: List[VideoSegment]):
        """Calcula score final de interés para cada segmento"""
        for seg in segments:
            score = 0.0
            
            # Diálogo valioso
            if seg.contains_dialogue:
                # Detectar si es diálogo con el bot (contiene nombre del bot o patrones)
                transcript_lower = seg.transcript.lower()
                bot_indicators = ["eko", "bot", "compañera", "saira", "mi amor"]
                if any(ind in transcript_lower for ind in bot_indicators):
                    score += SCORE_WEIGHTS["dialogue"] * 1.5
                else:
                    score += SCORE_WEIGHTS["dialogue"]
            
            # Acción
            if seg.contains_action:
                score += SCORE_WEIGHTS["action"]
            if seg.contains_combat:
                score += SCORE_WEIGHTS["action"] * 1.3
            
            # Emoción
            emotion_multiplier = {
                "epic": 1.5, "excited": 1.3, "funny": 1.4,
                "tense": 1.2, "nostalgic": 1.1, "calm": 0.6
            }.get(seg.emotional_tone, 1.0)
            score += SCORE_WEIGHTS["emotion"] * emotion_multiplier
            
            # Importancia narrativa base
            score += seg.interest_score * SCORE_WEIGHTS["narrative_importance"]
            
            seg.interest_score = min(score, 10.0)
    
    def _detect_narrative_structure(self, segments: List[VideoSegment], duration: float) -> NarrativeStructure:
        """Detecta la estructura narrativa del video completo"""
        
        narrative = NarrativeStructure()
        narrative.segments = segments
        
        # Clasificar por tags
        for i, seg in enumerate(segments):
            if seg.narrative_tag == "setup":
                narrative.setup_segments.append(i)
            elif seg.narrative_tag == "rising":
                narrative.rising_segments.append(i)
            elif seg.narrative_tag == "climax":
                narrative.climax_segments.append(i)
            elif seg.narrative_tag == "falling":
                narrative.falling_segments.append(i)
            elif seg.narrative_tag == "resolution":
                narrative.resolution_segments.append(i)
        
        # Detectar saludo inicial (primeros 30 segundos, con diálogo)
        for i, seg in enumerate(segments):
            if seg.start_time > 30:
                break
            if seg.contains_dialogue and any(w in seg.transcript.lower() for w in ["hola", "buenas", "hey", "qué tal", "eko"]):
                narrative.opening_greeting = (seg.start_time, seg.end_time)
                break
        
        # Detectar despedida final (últimos 30 segundos, con diálogo)
        for i in reversed(range(len(segments))):
            seg = segments[i]
            if seg.start_time < duration - 30:
                break
            if seg.contains_dialogue and any(w in seg.transcript.lower() for w in ["adiós", "chao", "nos vemos", "hasta luego", "gracias"]):
                narrative.closing_greeting = (seg.start_time, seg.end_time)
                break
        
        # Generar resumen global con IA
        self._generate_global_summary(narrative)
        
        return narrative
    
    def _generate_global_summary(self, narrative: NarrativeStructure):
        """Genera un resumen global del video"""
        
        # Compilar información de los mejores segmentos
        top_segments = sorted(narrative.segments, key=lambda s: s.interest_score, reverse=True)[:10]
        
        summary_text = "Resumen de segmentos destacados:\n\n"
        for seg in top_segments:
            summary_text += f"[{seg.start_time:.0f}s-{seg.end_time:.0f}s] {seg.emotional_tone.upper()}: {seg.visual_description[:100]}\n"
            if seg.transcript:
                summary_text += f'  Audio: "{seg.transcript[:80]}..."\n'
        
        prompt = f"""Eres un guionista de contenido para YouTube y redes sociales.

Basado en estos segmentos de un video de Minecraft, crea:
1. Un título atractivo (máx 60 caracteres)
2. Un resumen de la historia en 2-3 oraciones
3. El tema principal (aventura, construcción, supervivencia, exploración, etc.)
4. Los 3 momentos más importantes (con timestamps)

{summary_text}

Responde EXACTAMENTE en este formato JSON:
{{
  "title": "Título del video",
  "summary": "Resumen narrativo",
  "theme": "tema_principal",
  "key_moments": [
    {{"time": 0, "description": "momento 1"}},
    {{"time": 0, "description": "momento 2"}},
    {{"time": 0, "description": "momento 3"}}
  ]
}}"""
        
        response = query_ollama(prompt)
        try:
            json_str = response
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            data = json.loads(json_str.strip())
            narrative.title = data.get("title", "Aventura en Minecraft")
            narrative.summary = data.get("summary", "Una sesión de Minecraft con DaemonCraft.")
            narrative.theme = data.get("theme", "aventura")
            narrative.key_moments = data.get("key_moments", [])
        except Exception as e:
            print(f"[VideoAI] Error generando resumen global: {e}")
            narrative.title = "Aventura en Minecraft con Eko"
            narrative.summary = "Una sesión épica de Minecraft con mi compañera digital."


# ──────────────────────────────────────────────────────────────
# SELECTOR DE ESCENAS
# ──────────────────────────────────────────────────────────────

class SceneSelector:
    """
    Selecciona escenas manteniendo coherencia narrativa.
    Garantiza inicio, nudo y desenlace, conservando saludos.
    """
    
    def select_scenes(self, narrative: NarrativeStructure, target_duration: float) -> List[EditDecision]:
        """
        Selecciona escenas para un video de duración objetivo.
        Mantiene estructura narrativa: inicio → nudo → desenlace.
        """
        print(f"[VideoAI] 🎬 Seleccionando escenas para {target_duration:.0f}s de video...")
        
        segments = narrative.segments
        if not segments:
            return []
        
        # Calcular cuánto tiempo asignar a cada acto
        setup_time = target_duration * NARRATIVE_RATIO["setup"]
        rising_time = target_duration * NARRATIVE_RATIO["rising"]
        climax_time = target_duration * NARRATIVE_RATIO["climax"]
        falling_time = target_duration * NARRATIVE_RATIO["falling"]
        resolution_time = target_duration * NARRATIVE_RATIO["resolution"]
        
        decisions: List[EditDecision] = []
        
        # ── ACTO 1: SETUP (siempre incluir saludo inicial si existe) ──
        act1_segments = []
        
        # Saludo inicial obligatorio
        if narrative.opening_greeting:
            start, end = narrative.opening_greeting
            act1_segments.append((start, end, "opening_greeting"))
            setup_time -= (end - start)
        
        # Completar con segmentos de setup más interesantes
        setup_candidates = [segments[i] for i in narrative.setup_segments if segments[i].interest_score > 0.3]
        setup_candidates.sort(key=lambda s: s.interest_score, reverse=True)
        
        current_setup_time = sum(e - s for s, e, _ in act1_segments)
        for seg in setup_candidates:
            if current_setup_time >= setup_time:
                break
            seg_duration = seg.end_time - seg.start_time
            # No duplicar
            if not any(abs(s - seg.start_time) < 1 for s, _, _ in act1_segments):
                act1_segments.append((seg.start_time, seg.end_time, "setup"))
                current_setup_time += seg_duration
        
        # ── ACTO 2: RISING ACTION ──
        act2_segments = []
        rising_candidates = [segments[i] for i in narrative.rising_segments]
        rising_candidates.sort(key=lambda s: s.interest_score, reverse=True)
        
        current_rising_time = 0
        for seg in rising_candidates:
            if current_rising_time >= rising_time:
                break
            seg_duration = seg.end_time - seg.start_time
            if not any(abs(s - seg.start_time) < 1 for s, _, _ in act1_segments + act2_segments):
                act2_segments.append((seg.start_time, seg.end_time, "rising"))
                current_rising_time += seg_duration
        
        # ── ACTO 3: CLIMAX ──
        act3_segments = []
        climax_candidates = [segments[i] for i in narrative.climax_segments]
        # Incluir también rising con score muy alto como posibles climax
        for i in narrative.rising_segments:
            if segments[i].interest_score > 1.5:
                climax_candidates.append(segments[i])
        
        climax_candidates.sort(key=lambda s: s.interest_score, reverse=True)
        
        current_climax_time = 0
        for seg in climax_candidates:
            if current_climax_time >= climax_time:
                break
            seg_duration = seg.end_time - seg.start_time
            used_starts = [s for s, _, _ in act1_segments + act2_segments + act3_segments]
            if not any(abs(s - seg.start_time) < 1 for s in used_starts):
                act3_segments.append((seg.start_time, seg.end_time, "climax"))
                current_climax_time += seg_duration
        
        # ── ACTO 4: FALLING ACTION ──
        act4_segments = []
        falling_candidates = [segments[i] for i in narrative.falling_segments]
        falling_candidates.sort(key=lambda s: s.interest_score, reverse=True)
        
        current_falling_time = 0
        for seg in falling_candidates:
            if current_falling_time >= falling_time:
                break
            seg_duration = seg.end_time - seg.start_time
            used_starts = [s for s, _, _ in act1_segments + act2_segments + act3_segments + act4_segments]
            if not any(abs(s - seg.start_time) < 1 for s in used_starts):
                act4_segments.append((seg.start_time, seg.end_time, "falling"))
                current_falling_time += seg_duration
        
        # ── ACTO 5: RESOLUTION (siempre incluir despedida final si existe) ──
        act5_segments = []
        
        if narrative.closing_greeting:
            start, end = narrative.closing_greeting
            act5_segments.append((start, end, "closing_greeting"))
        else:
            # Buscar un segmento de resolución
            resolution_candidates = [segments[i] for i in narrative.resolution_segments]
            if resolution_candidates:
                best = max(resolution_candidates, key=lambda s: s.interest_score)
                act5_segments.append((best.start_time, best.end_time, "resolution"))
        
        # ── COMPILAR Y ORDENAR ──
        all_segments = act1_segments + act2_segments + act3_segments + act4_segments + act5_segments
        all_segments.sort(key=lambda x: x[0])  # Ordenar por tiempo
        
        # Crear decisiones de edición
        for start, end, tag in all_segments:
            decision = EditDecision(
                source_path="",  # Se llena después
                start_time=start,
                end_time=end,
                transition_type="cut"
            )
            
            # Efectos según el tipo de escena
            if tag == "climax":
                decision.transition_type = "zoom_in"
                decision.speed_factor = 1.0
            elif tag == "opening_greeting" or tag == "closing_greeting":
                decision.transition_type = "fade"
            
            decisions.append(decision)
        
        total_selected = sum(d.end_time - d.start_time for d in decisions)
        print(f"[VideoAI]   {len(decisions)} escenas seleccionadas, {total_selected:.0f}s totales")
        
        return decisions


# ──────────────────────────────────────────────────────────────
# EDITOR PARA REDES SOCIALES
# ──────────────────────────────────────────────────────────────

class SocialVideoEditor:
    """
    Edita video para redes sociales con ritmo, subtítulos y efectos.
    """
    
    def __init__(self, work_dir: str):
        self.work_dir = Path(work_dir)
        self.temp_clips = []
    
    def edit(self, video_path: str, decisions: List[EditDecision], narrative: NarrativeStructure, output_path: str) -> str:
        """
        Edita el video final aplicando las decisiones de escena.
        Añade subtítulos, efectos y optimiza para redes sociales.
        """
        print(f"[VideoAI] ✂️ Editando video final...")
        
        if not decisions:
            print("[VideoAI]   No hay decisiones de edición")
            return video_path
        
        # 1. Extraer clips individuales
        clips_dir = self.work_dir / "clips"
        clips_dir.mkdir(exist_ok=True)
        
        clip_files = []
        for i, decision in enumerate(decisions):
            clip_path = clips_dir / f"clip_{i:04d}.mp4"
            self._extract_clip(video_path, decision, str(clip_path))
            clip_files.append(str(clip_path))
            decision.source_path = str(clip_path)
        
        # 2. Generar lista de concatenación
        concat_list = self.work_dir / "concat_list.txt"
        with open(concat_list, "w") as f:
            for clip_file in clip_files:
                f.write(f"file '{clip_file}'\n")
        
        # 3. Concatenar y aplicar efectos finales
        self._concatenate_clips(str(concat_list), output_path, narrative)
        
        # Limpiar clips temporales
        for clip_file in clip_files:
            try:
                os.remove(clip_file)
            except:
                pass
        
        if os.path.exists(output_path):
            print(f"[VideoAI]   ✅ Video final: {output_path}")
            return output_path
        else:
            print("[VideoAI]   ❌ Error creando video final")
            return video_path
    
    def _extract_clip(self, video_path: str, decision: EditDecision, output_path: str):
        """Extrae un clip con posibles efectos de velocidad"""
        duration = decision.end_time - decision.start_time
        
        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", str(decision.start_time),
            "-t", str(duration),
            "-i", video_path,
            "-vf", f"setpts={1/decision.speed_factor}*PTS",
            "-af", f"atempo={decision.speed_factor}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        
        # Si es clip rápido, ajustar
        if decision.speed_factor != 1.0:
            # atempo solo soporta 0.5-2.0, usar filtros complejos si es necesario
            pass
        
        subprocess.run(cmd, capture_output=True, text=True)
    
    def _concatenate_clips(self, concat_list: str, output_path: str, narrative: NarrativeStructure):
        """Concatena clips y añade efectos finales"""
        
        # Concatenación básica con transiciones suaves
        cmd = [
            FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-vf", "fade=st=0:d=0.5:alpha=1,format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[VideoAI] FFmpeg concat error: {result.stderr[:500]}")
    
    def add_subtitles(self, video_path: str, segments: List[VideoSegment], output_path: str):
        """
        Añade subtítulos dinámicos al video.
        Usa la transcripción de cada segmento.
        """
        # Generar archivo SRT
        srt_path = self.work_dir / "subtitles.srt"
        
        with open(srt_path, "w", encoding="utf-8") as f:
            entry_num = 1
            for seg in segments:
                if not seg.transcript or seg.selected:
                    continue
                
                start = self._seconds_to_srt(seg.start_time)
                end = self._seconds_to_srt(seg.end_time)
                
                f.write(f"{entry_num}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{seg.transcript}\n\n")
                entry_num += 1
        
        # Quemar subtítulos en el video
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", video_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2'",
            "-c:v", "libx264", "-crf", "20",
            "-c:a", "copy",
            output_path
        ]
        
        subprocess.run(cmd, capture_output=True, text=True)
        return output_path if os.path.exists(output_path) else video_path
    
    def _seconds_to_srt(self, seconds: float) -> str:
        """Convierte segundos a formato SRT HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# ──────────────────────────────────────────────────────────────
# GENERADOR DE DESCRIPCIÓN PARA TELEGRAM
# ──────────────────────────────────────────────────────────────

class TelegramDescriptionGenerator:
    """Genera descripciones atractivas para Telegram"""
    
    def generate(self, narrative: NarrativeStructure, final_duration: float) -> str:
        """Genera texto descriptivo para Telegram"""
        
        # Prompt para generar descripción de Telegram
        prompt = f"""Eres un community manager para un canal de Minecraft.

Crea una descripción atractiva para Telegram de este video de Minecraft.

Título: {narrative.title}
Resumen: {narrative.summary}
Tema: {narrative.theme}
Duración: {final_duration/60:.1f} minutos
Momentos clave:
"""
        
        for moment in narrative.key_moments:
            prompt += f"- [{moment.get('time', 0)}s] {moment.get('description', '')}\n"
        
        prompt += """
La descripción debe:
1. Tener un hook inicial que capture atención
2. Mencionar los momentos más épicos
3. Incluir emojis relevantes
4. Terminar con una pregunta o call-to-action
5. Tener máximo 400 caracteres
6. Ser en español

Responde SOLO con el texto de la descripción, sin comillas, sin markdown."""
        
        description = query_ollama(prompt)
        
        # Limpiar
        description = description.strip().strip('"').strip("'")
        
        if len(description) > 400:
            description = description[:397] + "..."
        
        return description or f"🎮 {narrative.title} — {narrative.summary[:100]}"


# ──────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ──────────────────────────────────────────────────────────────

class VideoAIEditorPipeline:
    """
    Pipeline completo: analiza → selecciona → edita → describe.
    """
    
    def __init__(self, work_dir: str = None):
        self.work_dir = work_dir or f"/tmp/video_ai_{int(time.time())}"
        self.analyzer = NarrativeAnalyzer(self.work_dir)
        self.selector = SceneSelector()
        self.editor = SocialVideoEditor(self.work_dir)
        self.description_gen = TelegramDescriptionGenerator()
    
    def process(self, video_path: str, target_duration_minutes: float = 5.0) -> dict:
        """
        Procesa un video completo.
        
        Args:
            video_path: Ruta al video de entrada
            target_duration_minutes: Duración objetivo del video editado
        
        Returns:
            dict con: output_path, description, narrative, stats
        """
        target_duration = target_duration_minutes * 60
        
        print(f"\n{'='*60}")
        print(f"[VideoAI] 🎬 INICIANDO EDICIÓN INTELIGENTE")
        print(f"[VideoAI]    Input:  {video_path}")
        print(f"[VideoAI]    Target: {target_duration:.0f}s ({target_duration_minutes} min)")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        # 1. Analizar narrativa
        narrative = self.analyzer.analyze(video_path)
        
        # 2. Seleccionar escenas coherentes
        decisions = self.selector.select_scenes(narrative, target_duration)
        
        # 3. Editar video
        output_filename = f"{Path(video_path).stem}_ai_edit_{int(target_duration_minutes)}min.mp4"
        output_dir = Path(video_path).parent / "outputs"
        output_dir.mkdir(exist_ok=True)
        output_path = str(output_dir / output_filename)
        
        final_path = self.editor.edit(video_path, decisions, narrative, output_path)
        
        # 4. Añadir subtítulos
        final_with_subs = str(output_dir / f"{Path(output_filename).stem}_subtitled.mp4")
        # Buscar segmentos seleccionados
        selected_segments = [seg for seg in narrative.segments if seg.selected]
        # Marcar seleccionados
        for seg in narrative.segments:
            seg.selected = any(
                abs(d.start_time - seg.start_time) < 1 for d in decisions
            )
        self.editor.add_subtitles(final_path, narrative.segments, final_with_subs)
        
        # Usar el con subtítulos si existe
        if os.path.exists(final_with_subs):
            final_path = final_with_subs
        
        # 5. Generar descripción
        final_duration = get_video_duration(final_path) if os.path.exists(final_path) else 0
        description = self.description_gen.generate(narrative, final_duration)
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"[VideoAI] ✅ EDICIÓN COMPLETADA")
        print(f"[VideoAI]    Output: {final_path}")
        print(f"[VideoAI]    Duración: {final_duration/60:.1f} min")
        print(f"[VideoAI]    Tiempo: {elapsed/60:.1f} min")
        print(f"{'='*60}\n")
        
        return {
            "output_path": final_path,
            "description": description,
            "narrative": narrative,
            "title": narrative.title,
            "summary": narrative.summary,
            "duration_seconds": final_duration,
            "processing_time_seconds": elapsed,
            "segments_analyzed": len(narrative.segments),
            "scenes_selected": len(decisions),
            "key_moments": narrative.key_moments
        }


# ──────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DaemonCraft Video AI Editor")
    parser.add_argument("video", help="Ruta al video a editar")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duración objetivo en minutos")
    parser.add_argument("--output", "-o", help="Ruta de salida")
    parser.add_argument("--telegram", "-t", action="store_true", help="Enviar a Telegram después")
    
    args = parser.parse_args()
    
    pipeline = VideoAIEditorPipeline()
    result = pipeline.process(args.video, args.duration)
    
    print(f"\n📁 Video: {result['output_path']}")
    print(f"📝 Descripción: {result['description']}")
    print(f"📊 Título: {result['title']}")
    
    if args.telegram:
        # Importar y usar el sender de Telegram
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from telegram_sender import send_video
        
        send_video(result['output_path'], result['description'])
        print("📤 Enviado a Telegram!")
