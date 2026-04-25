# DaemonCraft Agent Bridge

Python Flask HTTP server that acts as a control plane for Mineflayer bots.

## Overview

The bridge receives triggers from external systems (Hermes CLI, webhooks, cron jobs) and forwards commands to the appropriate Mineflayer bot via its HTTP API.

## Setup

```bash
cd agent-bridge/
cp .env.example .env
# Edit .env with your configuration
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python bridge.py
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_HOST | 0.0.0.0 | Bind address |
| FLASK_PORT | 5000 | HTTP port |
| BOT_REGISTRY | DaemonBot=http://localhost:3000 | Comma-separated bot URLs |
| TRIGGER_TIMEOUT | 30 | Request timeout in seconds |

## API Endpoints

### Health
```
GET /health
```

### List Daemons
```
GET /daemons
```

### Send Trigger
```
POST /trigger
{
  "daemon": "DaemonBot",
  "action": "chat",
  "params": {"message": "Hello world"}
}
```

### Broadcast
```
POST /broadcast
{
  "message": "Hello all daemons"
}
```

## Architecture

```
Hermes CLI / Webhook
       |
       v
+-------------+      HTTP      +-------------+      HTTP      +-------------+
| Agent       | -------------> | Mineflayer  | -------------> | Minecraft   |
| Bridge      |   /trigger     | Bot API     |   /command     | Server      |
| (bridge.py) |                | (bots/)     |                | (Phi-Craft) |
+-------------+                +-------------+                +-------------+
```
