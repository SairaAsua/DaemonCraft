#!/bin/bash
#═══════════════════════════════════════════════════════════════════════════════
# start_daemoncraft.sh — Script maestro de inicio del Mundo Soul
#
# Un solo comando para levantar TODO:
#   ./start_daemoncraft.sh              # Iniciar todo
#   ./start_daemoncraft.sh --stop       # Detener todo
#   ./start_daemoncraft.sh --status     # Ver estado de procesos
#   ./start_daemoncraft.sh --build      # Solo construir datapack
#   ./start_daemoncraft.sh --bot-only   # Solo bot + heartbeat (sin agente)
#═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"
DATAPACK_DIR="$SCRIPT_DIR/datapacks/ra_soul_world"
DASHBOARD_URL="http://localhost:3001/dashboard"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$LOG_DIR" "$PID_DIR"

log() { echo -e "${CYAN}[$(date '+%H:%M:%S')]${NC} $1"; }
ok() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
err() { echo -e "${RED}✗${NC} $1"; }

save_pid() { echo $2 > "$PID_DIR/$1.pid"; }
get_pid() { cat "$PID_DIR/$1.pid" 2>/dev/null || echo ""; }
is_running() { local pid=$(get_pid "$1"); [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; }

stop_all() {
    log "${PURPLE}Deteniendo DaemonCraft...${NC}"
    for service in agent heartbeat bot-server; do
        local pid=$(get_pid "$service")
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$PID_DIR/$service.pid"
    done
    ok "Todos los servicios detenidos."
}

show_status() {
    echo -e "\n${PURPLE}═══ Estado de DaemonCraft ═══${NC}\n"
    printf "%-20s %-10s %-20s\n" "Servicio" "Estado" "PID"
    echo "---------------------------------------------"
    for service in heartbeat bot-server agent; do
        local pid=$(get_pid "$service")
        local status="${RED}OFF${NC}"
        if is_running "$service"; then status="${GREEN}ON${NC}"; fi
        printf "%-20b %-10b %-20s\n" "$service" "$status" "${pid:-—}"
    done
    echo ""
    if ss -tlnp 2>/dev/null | grep -q ":3001"; then ok "Puerto 3001 (Bot API) — escuchando"
    else warn "Puerto 3001 (Bot API) — no responde"; fi
    if ss -tlnp 2>/dev/null | grep -q ":25565"; then ok "Puerto 25565 (Minecraft) — escuchando"
    else warn "Puerto 25565 (Minecraft) — no responde"; fi
    if [[ -d "$DATAPACK_DIR" ]]; then
        local cmd_count=$(wc -l < "$DATAPACK_DIR/data/ra_soul_world/functions/build.mcfunction")
        ok "Datapack ra_soul_world — $cmd_count comandos listos"
    else warn "Datapack ra_soul_world — no encontrado"; fi
    local oracle_file="$SCRIPT_DIR/soul-engine/transits/eko_current.json"
    if [[ -f "$oracle_file" ]]; then ok "Oráculo Eko — $(python3 -c "import json; d=json.load(open('$oracle_file')); print('Día',d.get('hd_day','?'))")"
    else warn "Oráculo Eko — no encontrado"; fi
}

build_datapack() {
    log "${BLUE}Construyendo datapack del Mundo Soul...${NC}"
    cd "$SCRIPT_DIR/scripts"
    python3 build_world.py
    ok "Datapack generado: $DATAPACK_DIR"
    local cmd_count=$(wc -l < "$DATAPACK_DIR/data/ra_soul_world/functions/build.mcfunction")
    log "  Total comandos: $cmd_count"
}

start_heartbeat() {
    if is_running heartbeat; then ok "Heartbeat ya está corriendo (PID $(get_pid heartbeat))"; return; fi
    log "Iniciando Heartbeat Oráculo HD..."
    cd "$SCRIPT_DIR/soul-engine"
    nohup python3 heartbeat_minecraft.py >> "$LOG_DIR/heartbeat.log" 2>&1 &
    save_pid heartbeat $!
    sleep 2
    if is_running heartbeat; then ok "Heartbeat iniciado (PID $(get_pid heartbeat))"
    else err "Heartbeat falló al iniciar. Revisa $LOG_DIR/heartbeat.log"; return 1; fi
}

start_bot_server() {
    if is_running bot-server; then ok "Bot server ya está corriendo (PID $(get_pid bot-server))"; return; fi
    log "Iniciando Bot Mineflayer Bridge..."
    cd "$SCRIPT_DIR/agents/bot"
    if [[ ! -d "node_modules" ]]; then warn "node_modules no encontrado. Instalando..."; npm install >> "$LOG_DIR/npm.log" 2>&1; fi
    nohup node server.js >> "$LOG_DIR/bot-server.log" 2>&1 &
    save_pid bot-server $!
    sleep 3
    if is_running bot-server; then ok "Bot server iniciado (PID $(get_pid bot-server))"
        log "  Dashboard: http://localhost:3001/dashboard"
    else err "Bot server falló al iniciar. Revisa $LOG_DIR/bot-server.log"; return 1; fi
}

start_agent() {
    if is_running agent; then ok "Agente Eko ya está corriendo (PID $(get_pid agent))"; return; fi
    log "Iniciando Agente Eko (profile: eko)..."
    cd "$SCRIPT_DIR/agents"
    if [[ ! -d "$HOME/.hermes/profiles/eko" ]]; then
        warn "Perfil 'eko' no encontrado en ~/.hermes/profiles/"
        warn "El agente puede fallar al cargar SOUL.md"
    fi
    export MC_API_URL="http://localhost:3001"
    export MC_USERNAME="eko"
    export MC_KNOWN_BOTS="eko"
    nohup python3 agent_loop.py --profile eko >> "$LOG_DIR/agent.log" 2>&1 &
    save_pid agent $!
    sleep 2
    if is_running agent; then ok "Agente Eko iniciado (PID $(get_pid agent))"
    else err "Agente Eko falló al iniciar. Revisa $LOG_DIR/agent.log"; return 1; fi
}

start_all() {
    echo -e "\n${PURPLE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║${NC}  ${CYAN}DaemonCraft — Mundo Soul${NC}                       ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}  Diseño Humano + Minecraft AI                ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════════════════╝\n"
    build_datapack
    start_heartbeat
    start_bot_server
    if [[ "$1" != "--bot-only" ]]; then start_agent; fi
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  ✨ Todo listo, mi huracán ✨                      ${GREEN}║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════════════════╝\n"
    echo -e "${CYAN}Dashboard:${NC}     $DASHBOARD_URL"
    echo -e "${CYAN}API del bot:${NC}   http://localhost:3001"
    echo -e "${CYAN}Datapack:${NC}      $DATAPACK_DIR"
    echo -e "${CYAN}Perfil Eko:${NC}    ~/.hermes/profiles/eko/SOUL.md"
    echo ""
    echo -e "${YELLOW}Comandos útiles:${NC}"
    echo "  ./start_daemoncraft.sh --stop     # Detener todo"
    echo "  ./start_daemoncraft.sh --status   # Ver estado"
    echo "  tail -f $LOG_DIR/agent.log        # Ver logs del agente"
    echo "  tail -f $LOG_DIR/heartbeat.log    # Ver logs del oráculo"
    echo ""
}

case "${1:-}" in
    --stop|-s) stop_all ;;
    --status|-st) show_status ;;
    --build|-b) build_datapack ;;
    --bot-only) start_all --bot-only ;;
    --help|-h)
        echo "Uso: ./start_daemoncraft.sh [OPCIÓN]"
        echo ""
        echo "Opciones:"
        echo "  (sin args)     Iniciar todo (datapack + heartbeat + bot + agente)"
        echo "  --stop, -s     Detener todos los servicios"
        echo "  --status, -st  Mostrar estado de procesos"
        echo "  --build, -b    Solo construir datapack"
        echo "  --bot-only     Solo bot + heartbeat (sin agente AI)"
        echo "  --help, -h     Mostrar esta ayuda"
        echo ""
        echo "El datapack se instala copiando la carpeta:"
        echo "  $DATAPACK_DIR"
        echo "a la carpeta datapacks de tu mundo Minecraft."
        ;;
    *) start_all ;;
esac
