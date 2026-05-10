#!/usr/bin/env bash
# Control script para el DaemonCraft Video Plugin

cd "$(dirname "$0")"
PIDFILE="/tmp/video-plugin.pid"

status() {
  if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
    echo "Video plugin RUNNING (PID $(cat "$PIDFILE"))"
    return 0
  else
    echo "Video plugin STOPPED"
    return 1
  fi
}

start() {
  if status >/dev/null; then
    echo "Already running"
    return 0
  fi
  nohup node index.js >/tmp/video-plugin.log 2>&1 &
  echo $! > "$PIDFILE"
  echo "Started video plugin (PID $!)"
}

stop() {
  if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if kill -0 "$PID" 2>/dev/null; then
      kill "$PID"
      rm -f "$PIDFILE"
      echo "Stopped video plugin"
    else
      rm -f "$PIDFILE"
      echo "Was not running"
    fi
  else
    # Fallback: kill any node process in this dir
    pkill -f "node.*video-plugin/index.js" 2>/dev/null && echo "Stopped video plugin" || echo "Not running"
  fi
}

case "$1" in
  start) start ;;
  stop) stop ;;
  restart) stop; sleep 1; start ;;
  status) status ;;
  *) echo "Usage: $0 {start|stop|restart|status}" ;;
esac
