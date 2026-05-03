# DaemonCraft Video Plugin v1.0

Plugin de grabación, análisis con IA, edición automática y envío a Telegram para DaemonCraft Minecraft.

## ¿Qué hace?

1. **Graba** tu gameplay de Minecraft desde el dashboard (pantalla o OBS Virtual Camera)
2. **Loguea** eventos en tiempo real: chat, combate, muertes, quests, acciones
3. **Analiza** con IA (Ollama/Gemma4) para detectar los momentos más interesantes
4. **Edita** automáticamente un highlight reel con FFmpeg
5. **Envía** el video final a Telegram (hasta 30 min, 50MB)

## Arquitectura

```
Dashboard HTML → WebSocket → Video Plugin (puerto 3010)
                            ↓
                    FFmpeg (x11grab / v4l2)
                            ↓
                    Event Logger (JSON Lines)
                            ↓
                    Video Analyzer (frames + LLM)
                            ↓
                    Video Editor (FFmpeg concat)
                            ↓
                    Telegram Sender (Bot API)
```

## Instalación

```bash
cd /home/saira/DaemonCraft-minecraft/plugins/video-plugin
npm install
```

## Configuración

Variables de entorno (opcional, tienen defaults):

| Variable | Default | Descripción |
|----------|---------|-------------|
| `BOT_WS_URL` | `ws://localhost:3002/ws` | WebSocket del bot |
| `VIDEO_API_PORT` | `3010` | Puerto del plugin |
| `VIDEO_DIR` | `./recordings` | Directorio de grabaciones |
| `TELEGRAM_BOT_TOKEN` | - | Token del bot de Telegram |
| `TELEGRAM_CHAT_ID` | - | Chat ID destino |
| `OLLAMA_URL` | `http://10.10.20.1:11434` | Endpoint de Ollama |
| `OLLAMA_MODEL` | `gemma4:e4b-it-q8_0` | Modelo para análisis |

## Uso

### Iniciar el plugin

```bash
node index.js
# o con variables:
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy node index.js
```

### Desde el Dashboard

El panel "🎥 Video Studio" aparece en el dashboard de DaemonCraft.

**Controles:**
- **● Grabar** — inicia la grabación
- **■ Detener** — finaliza y guarda
- **🔍 Analizar** — detecta highlights con IA
- **✂️ Editar** — genera el video final
- **⚡ Todo** — pipeline completo (analizar + editar + enviar)
- **✉️ Telegram** — envía el último video

### API HTTP

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Estado del plugin |
| `/sessions` | GET | Lista de sesiones grabadas |
| `/record/start` | POST | Iniciar grabación |
| `/record/stop` | POST | Detener grabación |
| `/analyze` | POST | Analizar sesión |
| `/edit` | POST | Editar video |
| `/pipeline` | POST | Analizar + editar + enviar |
| `/telegram/send` | POST | Enviar video a Telegram |

### Fuentes de video

- **Pantalla (X11)**: captura toda la pantalla con audio PulseAudio
- **OBS Virtual Camera**: lee desde `/dev/video*` (v4l2loopback)

Para usar OBS:
1. Abre OBS Studio
2. Selecciona tu escena de Minecraft
3. Tools → Virtual Camera → Start
4. En el dashboard selecciona "OBS Virtual Camera"

## Estructura de archivos

```
recordings/
├── session_1234567890/
│   ├── raw.mkv              # video crudo
│   ├── events.jsonl         # eventos del juego
│   ├── meta.json            # metadata de la sesión
│   ├── frames/              # frames extraídos para análisis
│   ├── clips/               # clips individuales
│   └── highlights.json      # momentos detectados
└── outputs/
    └── session_xxx_edit_5min.mp4
```

## Dependencias del sistema

- **Node.js** >= 18
- **FFmpeg** (con libx264, aac, xfade)
- **ffprobe**
- **OBS Studio** (opcional, para virtual cam)
- **v4l2loopback** (opcional, para virtual cam en Linux)
- **Ollama** con modelo vision (opcional, para análisis IA)

## Créditos

Inspirado en [VideoAgent](https://github.com/HKUDS/VideoAgent) — framework de agentes para video understanding y editing.

✨ Hecho con amor para DaemonCraft.
