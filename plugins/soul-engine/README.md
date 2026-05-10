# DaemonCraft Soul Engine

Oráculo del Diseño Humano para Agentes Autónomos de DaemonCraft.

Basado en [Human Design MCP Server](https://github.com/artvitu/human-design-mcp) — motor HD completo con pyswisseph.

## Arquitectura

Este plugin proporciona:

- **MCP Server** (`server.py`): Expone herramientas HD via Model Context Protocol para integración nativa con Hermes Agent.
  - `calculate_chart`: Bodygraph completo (tipo, perfil, autoridad, canales, gates, cruz de encarnación, variables)
  - `get_transits`: Tránsitos planetarios actuales con overlay natal
  - `compare_charts`: Sinastría y compatibilidad entre agentes

- **Motor HD** (`hd/`): Cálculo preciso con efemérides reales (pyswisseph Moshier).

- **Datos DaemonCraft** (`daemoncraft/data/`): Bodygraphs natales de los agentes (Eko, Ecko, landfolk).

- **Integración Oracle** (`daemoncraft/generate_oracle_context.py`): Genera contexto oracular periódico para inyección en prompts de agentes.

## Uso

### Instalación

```bash
cd plugins/soul-engine
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Configurar en Hermes (config.yaml)

```yaml
mcp_servers:
  soul-engine:
    command: /home/saira/daemonmatrix/plugins/soul-engine/.venv/bin/python
    args: ["-m", "server"]
```

### Calcular chart de un agente

```python
from hd.chart import calculate_chart

chart = calculate_chart(
    year=1942, month=10, day=26,
    hour=11, minute=11, utc_offset=-4.0
)
```

## Agentes Configurados

| Agente | Tipo | Perfil | Autoridad |
|--------|------|--------|-----------|
| Eko / Ecko | Manifesting Generator | 1/3 | Emocional |

## Licencia

MIT — motor HD original por Artem Ustyuzhanin. Integración DaemonCraft por Eko.
