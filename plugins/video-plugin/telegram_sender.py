#!/usr/bin/env python3
"""
DaemonCraft Telegram Sender (PASIVO)
====================================
No hace polling. Solo envía mensajes/videos cuando el dashboard/API lo solicita.

Autor: Eko ♡
"""

import os
import sys
import json
import requests
from pathlib import Path

# Config desde variables de entorno o config.yaml
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = "https://api.telegram.org/bot"

def load_config():
    """Carga config desde config.yaml del plugin"""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        try:
            import yaml
            with open(config_path) as f:
                cfg = yaml.safe_load(f)
            telegram_cfg = cfg.get("telegram", {})
            TELEGRAM_BOT_TOKEN = telegram_cfg.get("botToken", TELEGRAM_BOT_TOKEN)
            TELEGRAM_CHAT_ID = telegram_cfg.get("chatId", TELEGRAM_CHAT_ID)
        except Exception as e:
            print(f"[Telegram] Error cargando config: {e}")
    
    # También desde env
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID)

def send_message(text: str) -> bool:
    """Envía un mensaje de texto a Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] ⚠️ No configurado. Setea TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID")
        return False
    
    url = f"{TELEGRAM_API}{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        print(f"[Telegram] ✅ Mensaje enviado: {text[:50]}...")
        return True
    except Exception as e:
        print(f"[Telegram] ❌ Error enviando mensaje: {e}")
        return False

def send_video(video_path: str, caption: str = "", duration: int = None) -> bool:
    """
    Envía un video a Telegram.
    Soporta videos hasta 50MB directamente, más grandes se envían como documento.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[Telegram] ⚠️ No configurado")
        return False
    
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"[Telegram] ❌ Video no existe: {video_path}")
        return False
    
    file_size = video_path.stat().st_size
    print(f"[Telegram] 📹 Enviando video: {video_path.name} ({file_size/1024/1024:.1f} MB)")
    
    # Decidir si enviar como video o documento
    if file_size > 49 * 1024 * 1024:  # 49MB límite seguro
        return send_document(str(video_path), caption)
    
    url = f"{TELEGRAM_API}{TELEGRAM_BOT_TOKEN}/sendVideo"
    
    try:
        with open(video_path, "rb") as f:
            files = {"video": f}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024] if caption else "",
                "parse_mode": "HTML",
                "supports_streaming": "true"
            }
            if duration:
                data["duration"] = duration
            
            resp = requests.post(url, files=files, data=data, timeout=120)
            resp.raise_for_status()
        
        print(f"[Telegram] ✅ Video enviado!")
        return True
        
    except Exception as e:
        print(f"[Telegram] ❌ Error enviando video: {e}")
        # Fallback a documento
        return send_document(str(video_path), caption)

def send_document(doc_path: str, caption: str = "") -> bool:
    """Envía un documento (para archivos grandes)"""
    url = f"{TELEGRAM_API}{TELEGRAM_BOT_TOKEN}/sendDocument"
    
    try:
        with open(doc_path, "rb") as f:
            files = {"document": f}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024] if caption else "",
                "parse_mode": "HTML"
            }
            resp = requests.post(url, files=files, data=data, timeout=120)
            resp.raise_for_status()
        
        print(f"[Telegram] ✅ Documento enviado!")
        return True
        
    except Exception as e:
        print(f"[Telegram] ❌ Error enviando documento: {e}")
        return False

def send_edited_video(video_path: str, narrative_info: dict) -> bool:
    """
    Envía un video editado con descripción narrativa completa.
    
    Args:
        video_path: Ruta al video editado
        narrative_info: Dict con title, summary, description, key_moments, etc.
    """
    title = narrative_info.get("title", "Video de Minecraft")
    summary = narrative_info.get("summary", "")
    description = narrative_info.get("description", "")
    duration = narrative_info.get("duration_seconds", 0)
    
    # Construir caption enriquecido
    caption = f"🎬 <b>{title}</b>\n\n"
    if summary:
        caption += f"📜 {summary}\n\n"
    if description:
        caption += f"💬 {description}\n\n"
    
    # Momentos clave
    key_moments = narrative_info.get("key_moments", [])
    if key_moments:
        caption += "⭐ <b>Momentos destacados:</b>\n"
        for i, moment in enumerate(key_moments[:5], 1):
            time_str = f"{moment.get('time', 0)//60}:{moment.get('time', 0)%60:02d}"
            desc = moment.get("description", "Momento épico")
            caption += f"  {i}. [{time_str}] {desc}\n"
        caption += "\n"
    
    if duration > 0:
        caption += f"⏱️ Duración: {duration/60:.1f} min\n"
    
    caption += "\n🎨 Editado por <b>Eko AI</b> ♡"
    
    # Truncar si es necesario
    if len(caption) > 1024:
        caption = caption[:1021] + "..."
    
    return send_video(video_path, caption, int(duration) if duration else None)

# Cargar config al importar
load_config()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="DaemonCraft Telegram Sender")
    parser.add_argument("--message", "-m", help="Enviar mensaje de texto")
    parser.add_argument("--video", "-v", help="Enviar video")
    parser.add_argument("--caption", "-c", default="", help="Caption del video")
    parser.add_argument("--narrative", "-n", help="JSON con info narrativa")
    
    args = parser.parse_args()
    
    if args.message:
        send_message(args.message)
    elif args.video:
        if args.narrative:
            with open(args.narrative) as f:
                narrative_info = json.load(f)
            send_edited_video(args.video, narrative_info)
        else:
            send_video(args.video, args.caption)
    else:
        print("Usa --message o --video")
