#!/usr/bin/env python3
"""
AI Edit Wrapper
===============
Script invocable desde Node.js para ejecutar el pipeline de edición narrativa.

Uso:
  python3 ai_edit_wrapper.py --video /path/to/video.mp4 --duration 5 \
    --output /path/to/output.mp4 [--narrative-json /path/to/narrative.json]

Escribe resultado JSON a stdout para que Node.js lo parseé.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Asegurar que podemos importar el módulo
sys.path.insert(0, str(Path(__file__).parent))

def main():
    parser = argparse.ArgumentParser(description="DaemonCraft AI Video Editor Wrapper")
    parser.add_argument("--video", required=True, help="Ruta al video de entrada")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duración objetivo en minutos")
    parser.add_argument("--output", "-o", help="Ruta de salida (opcional)")
    parser.add_argument("--work-dir", "-w", help="Directorio de trabajo temporal")
    parser.add_argument("--narrative-json", "-n", help="Path para guardar JSON con info narrativa")
    parser.add_argument("--skip-whisper", action="store_true", help="Saltar transcripción (más rápido)")
    
    args = parser.parse_args()
    
    video_path = Path(args.video)
    if not video_path.exists():
        print(json.dumps({"ok": False, "error": f"Video not found: {video_path}"}), flush=True)
        sys.exit(1)
    
    try:
        from video_ai_editor import VideoAIEditorPipeline
        
        pipeline = VideoAIEditorPipeline(work_dir=args.work_dir)
        result = pipeline.process(str(video_path), args.duration)
        
        # Guardar narrativa JSON si se pidió
        if args.narrative_json:
            narrative_data = {
                "title": result["title"],
                "summary": result["summary"],
                "description": result["description"],
                "duration_seconds": result["duration_seconds"],
                "key_moments": result["key_moments"],
                "segments_analyzed": result["segments_analyzed"],
                "scenes_selected": result["scenes_selected"],
                "processing_time_seconds": result["processing_time_seconds"],
            }
            with open(args.narrative_json, "w") as f:
                json.dump(narrative_data, f, indent=2, ensure_ascii=False)
        
        # Output JSON para Node.js
        output = {
            "ok": True,
            "outputFile": result["output_path"],
            "title": result["title"],
            "summary": result["summary"],
            "description": result["description"],
            "durationSeconds": result["duration_seconds"],
            "processingTimeSeconds": result["processing_time_seconds"],
            "segmentsAnalyzed": result["segments_analyzed"],
            "scenesSelected": result["scenes_selected"],
            "keyMoments": result["key_moments"],
        }
        print(json.dumps(output), flush=True)
        
    except Exception as e:
        import traceback
        print(json.dumps({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
