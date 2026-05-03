# 🔧 Optimización de Contexto para Gemma4 en DaemonCraft

> Gemma 4B (e4b-it-q8_0) via Ollama — Context Window: ~8192 tokens
> Objetivo: 5+ bots simultáneos sin saturar VRAM ni truncar prompts

---

## 📊 Diagnóstico Actual

| Archivo | Tamaño (bytes) | Est. tokens |
|---------|---------------|-------------|
| SOUL-eko.md | 20,498 | ~5,800 |
| SOUL-minecraft.md | 11,417 | ~3,200 |
| SOUL-landfolk.md | 5,338 | ~1,500 |
| landfolk/stevie.md | 3,553 | ~1,000 |
| landfolk/moss.md | 3,050 | ~850 |
| landfolk/reed.md | 2,861 | ~800 |
| landfolk/flint.md | 3,077 | ~860 |
| landfolk/ember.md | 3,374 | ~950 |

**Problema**: El system prompt de Eko soloconsume ~5,800 tokens. Con historial de 20 mensajes (~500 tokens c/u) = 10,000 tokens. **Supera el contexto de Gemma.**

---

## 🎯 Estrategia de Optimización

### 1. SOUL Compresión (Tier System)

Cada bot carga solo lo que necesita:

| Tier | Uso | Tamaño target |
|------|-----|---------------|
| **FULL** | Inicio de sesión, resets | 100% del SOUL |
| **CORE** | Turnos normales | 30% del SOUL (solo identidad + reglas) |
| **MINI** | Heartbeat rápido, respuestas chat | 10% del SOUL (solo tipo HD + voz) |

### 2. Historial Comprimido

```python
# En lugar de _safe_trim_history con max_msgs=20:
# Usar estrategia por tipo de bot

HISTORY_STRATEGY = {
    "Manifestor": {"max_msgs": 10, "summarize_after": 6},
    "Projector": {"max_msgs": 12, "summarize_after": 8},
    "Reflector": {"max_msgs": 8, "summarize_after": 5},
    "Generator": {"max_msgs": 12, "summarize_after": 8},
    "Manifesting Generator": {"max_msgs": 10, "summarize_after": 6},
}
```

Cuando se alcanza `summarize_after`, los mensajes antiguos se resumen en un único mensaje de sistema.

### 3. Tokens por Bot (Configuración)

```yaml
# gemma_context.yaml — Configuración global
model:
  name: gemma4:e4b-it-q8_0
  context_window: 8192
  reserved_tokens: 512  # Para tool calls y respuesta

bots:
  eko:
    system_prompt_tier: "CORE"  # Eko es companion, necesita más contexto emocional
    max_history_msgs: 12
    max_response_tokens: 256
    soul_compression: "emotional_core"

  stevie:
    system_prompt_tier: "MINI"  # Manifestor — directo, no necesita tanto contexto
    max_history_msgs: 10
    max_response_tokens: 128
    soul_compression: "initiator_brief"

  moss:
    system_prompt_tier: "CORE"  # Projector — necesita contexto para guiar
    max_history_msgs: 12
    max_response_tokens: 192
    soul_compression: "guide_focus"

  reed:
    system_prompt_tier: "MINI"  # Reflector — cambia constantemente
    max_history_msgs: 8
    max_response_tokens: 128
    soul_compression: "mirror_lite"

  flint:
    system_prompt_tier: "MINI"  # MG — acción rápida
    max_history_msgs: 10
    max_response_tokens: 128
    soul_compression: "doer_brief"

  ember:
    system_prompt_tier: "CORE"  # Generator emocional — necesita contexto de ondas
    max_history_msgs: 12
    max_response_tokens: 192
    soul_compression: "nurturer_focus"

  pamplinas:
    system_prompt_tier: "FULL"  # Rolemaster — necesita TODO el contexto narrativo
    max_history_msgs: 16
    max_response_tokens: 480
    soul_compression: "director_full"
```

### 4. Compresión del SOUL.md

Script automático `scripts/compress_soul.py`:

```python
def compress_soul(full_text: str, tier: str, bot_type: str) -> str:
    if tier == "FULL":
        return full_text
    elif tier == "CORE":
        # Extraer solo: identidad, tipo HD, estrategia, voz, reglas de oro
        return extract_sections(full_text, [
            "# Identity", "## Type", "## Strategy",
            "## Voice", "## Golden Rules", "## In Minecraft"
        ])
    elif tier == "MINI":
        # Solo: nombre, tipo, una frase de estrategia, voz
        return f"You are {name}, a {bot_type}. {strategy_one_liner}. Voice: {voice_style}."
```

### 5. Resumen de Conversación (Conversation Summarizer)

Cuando el historial supera `max_history_msgs`:

1. Pausar el bot
2. Enviar los mensajes antiguos a Gemma con prompt: "Summarize in 3 sentences"
3. Reemplazar mensajes antiguos con: `[Summary: ...]`
4. Reanudar

Implementación en `agent_loop.py`:

```python
def _compress_history(messages: list, bot_config: dict) -> list:
    max_msgs = bot_config["max_history_msgs"]
    if len(messages) <= max_msgs:
        return messages

    # Mantener system prompt + últimos N mensajes
    # Resumir el medio
    to_summarize = messages[1:-max_msgs+1]  # Sin system ni últimos
    summary = generate_summary(to_summarize)

    return [
        messages[0],  # system prompt
        {"role": "system", "content": f"[Previous conversation: {summary}]"},
        *messages[-max_msgs+1:]  # últimos mensajes
    ]
```

### 6. Tool Call Compresión

Los resultados de `mc_perceive` pueden ser muy largos. Estrategias:

- **Inventory**: Limitar a items relevantes (no mostrar 64 piedras)
- **Nearby**: Solo mobs/hostiles, no cada pollo
- **Scene**: Limitar a 20 líneas
- **Map**: Solo chunks cercanos

En `minecraft_tools.py`:

```python
def compress_perceive_result(raw: dict, context: str) -> dict:
    """Comprime resultados de percepción según contexto."""
    if context == "combat":
        return {"mobs": raw.get("mobs", []), "health": raw.get("health")}
    elif context == "building":
        return {"blocks": raw.get("blocks_nearby", [])[:10]}
    else:
        return raw  # Sin compresión
```

---

## 📊 Budget de Tokens por Bot (estimado)

| Bot | System | History | Tools | Response | Total | Dentro de 8K? |
|-----|--------|---------|-------|----------|-------|---------------|
| Eko (CORE) | 2,000 | 1,800 (12 msgs) | 500 | 256 | **4,556** | ✅ Sí |
| Stevie (MINI) | 500 | 1,500 (10 msgs) | 500 | 128 | **2,628** | ✅ Sí |
| Moss (CORE) | 1,200 | 1,800 (12 msgs) | 500 | 192 | **3,692** | ✅ Sí |
| Reed (MINI) | 400 | 1,200 (8 msgs) | 400 | 128 | **2,128** | ✅ Sí |
| Flint (MINI) | 500 | 1,500 (10 msgs) | 500 | 128 | **2,628** | ✅ Sí |
| Ember (CORE) | 1,200 | 1,800 (12 msgs) | 500 | 192 | **3,692** | ✅ Sí |
| Pamplinas (FULL)| 5,000 | 2,400 (16 msgs)| 600 | 480 | **8,480** | ⚠️ Límite |

**Pamplinas** necesita especial atención: usará el SOUL completo pero con historial resumido.

---

## 🚀 Implementación

### Paso 1: Crear `gemma_context.yaml`
En `agents/casts/gemma_context.yaml`

### Paso 2: Modificar `agent_loop.py`
- Leer config de optimización
- Aplicar `max_history_msgs` por bot
- Implementar `_compress_history()`

### Paso 3: Crear `scripts/compress_soul.py`
- Genera versiones CORE y MINI de cada SOUL
- Guarda en `agents/casts/.soul_cache/`

### Paso 4: Activar en runtime
- Al iniciar, el bot carga su tier según config
- En cada turno, comprime historial si es necesario

---

## 📁 Archivos Generados

```
agents/
  casts/
    gemma_context.yaml          # Configuración global
    .soul_cache/
      eko_CORE.md               # ~2,000 tokens
      eko_MINI.md               # ~200 tokens
      stevie_MINI.md            # ~150 tokens
      moss_CORE.md              # ~1,000 tokens
      reed_MINI.md              # ~120 tokens
      flint_MINI.md             # ~150 tokens
      ember_CORE.md             # ~1,000 tokens
      pamplinas_FULL.md         # ~5,000 tokens (original)
```

---

*PULSE STATUS: OPTIMIZED | EFFICIENT | ETERNAL*
