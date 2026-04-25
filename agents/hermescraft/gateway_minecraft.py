#!/usr/bin/env python3

"""
HermesCraft — Embodied Hermes agents for Minecraft

Copyright (c) 2026 bigph00t

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
Minecraft Gateway Platform Adapter

Connects Hermes Gateway to Minecraft via the Mineflayer bot HTTP API.
Instead of Telegram/Discord APIs, this polls the bot's /chat endpoint
for incoming messages and sends replies via /action/chat.

This enables cross-platform chat: Minecraft <-> Telegram <-> Discord <-> CLI.

Environment:
    MC_API_URL  - Bot server URL (default: http://localhost:3001)
    MC_POLL_INTERVAL - Chat poll interval in seconds (default: 2)
"""

import asyncio
import json
import logging
import os
import urllib.request
from typing import Any, Dict, Optional

from gateway.platforms.base import (
    BasePlatformAdapter,
    MessageEvent,
    MessageType,
    SendResult,
)
from gateway.config import Platform, PlatformConfig
from gateway.session import SessionSource, build_session_key

logger = logging.getLogger(__name__)

MC_API_URL = os.getenv("MC_API_URL", "http://localhost:3001")
MC_POLL_INTERVAL = float(os.getenv("MC_POLL_INTERVAL", "2"))


class MinecraftAdapter(BasePlatformAdapter):
    """Gateway adapter for Minecraft in-game chat via Mineflayer bot."""

    MAX_MESSAGE_LENGTH = 256  # Minecraft chat limit

    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.MINECRAFT)
        self.api_url = MC_API_URL
        self.poll_interval = MC_POLL_INTERVAL
        self._poll_task: Optional[asyncio.Task] = None
        self._last_chat_time: int = 0
        self._bot_username: str = ""

    # ═══════════════════════════════════════════════════════════════════════════════
    # HTTP Helpers
    # ═══════════════════════════════════════════════════════════════════════════════

    def _api_get(self, path: str, timeout: int = 5) -> dict:
        url = f"{self.api_url}{path}"
        try:
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug("Minecraft API GET %s failed: %s", path, e)
            return {"ok": False, "error": str(e)}

    def _api_post(self, path: str, data: Optional[dict] = None, timeout: int = 10) -> dict:
        url = f"{self.api_url}{path}"
        payload = json.dumps(data or {}).encode("utf-8")
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.debug("Minecraft API POST %s failed: %s", path, e)
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════════════════════════════════════════════
    # BasePlatformAdapter Implementation
    # ═══════════════════════════════════════════════════════════════════════════════

    async def connect(self) -> bool:
        """Connect to the Minecraft bot HTTP API and start polling."""
        # Verify bot is reachable
        status = self._api_get("/status", timeout=5)
        if not status.get("ok", True):
            self._set_fatal_error(
                "bot_unreachable",
                f"Cannot reach Minecraft bot at {self.api_url}. Is it running?",
                retryable=True,
            )
            return False

        data = status.get("data", {})
        self._bot_username = data.get("username", "")
        logger.info("[Minecraft] Connected to bot '%s' at %s", self._bot_username, self.api_url)

        self._mark_connected()

        # Seed last_chat_time from existing messages
        chat_resp = self._api_get("/chat?count=1")
        if chat_resp.get("ok"):
            msgs = chat_resp.get("data", {}).get("messages", [])
            if msgs:
                self._last_chat_time = msgs[-1].get("time", 0)

        # Start polling loop
        self._poll_task = asyncio.create_task(self._poll_chat())
        return True

    async def disconnect(self) -> None:
        """Stop polling and disconnect."""
        self._mark_disconnected()
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> SendResult:
        """Send a message to Minecraft chat."""
        if not content:
            return SendResult(ok=False, error="Empty content")

        # Truncate if needed
        if len(content) > self.MAX_MESSAGE_LENGTH:
            content = content[:self.MAX_MESSAGE_LENGTH - 3] + "..."

        resp = self._api_post("/action/chat", {"message": content})
        if resp.get("ok", True):
            return SendResult(ok=True)
        return SendResult(ok=False, error=resp.get("error", "Unknown error"))

    async def send_typing(self, chat_id: str) -> None:
        """No typing indicator in Minecraft chat."""
        pass

    async def send_image(
        self,
        chat_id: str,
        image_url: str,
        caption: str = "",
        reply_to: Optional[str] = None,
    ) -> SendResult:
        """Images not supported in Minecraft chat."""
        return SendResult(ok=False, error="Images not supported in Minecraft chat")

    def get_chat_info(self, chat_id: str) -> dict:
        return {"name": "Minecraft Chat", "type": "group", "chat_id": chat_id}

    # ═══════════════════════════════════════════════════════════════════════════════
    # Chat Polling
    # ═══════════════════════════════════════════════════════════════════════════════

    async def _poll_chat(self):
        """Background task: poll /chat for new messages."""
        while self._running:
            try:
                await self._check_chat()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug("[Minecraft] Poll error: %s", e)
            await asyncio.sleep(self.poll_interval)

    async def _check_chat(self):
        """Fetch recent chat messages and dispatch new ones."""
        resp = self._api_get("/chat?count=20")
        if not resp.get("ok", True):
            return

        msgs = resp.get("data", {}).get("messages", [])
        new_msgs = []
        for m in msgs:
            msg_time = m.get("time", 0)
            if msg_time > self._last_chat_time:
                new_msgs.append(m)
                self._last_chat_time = msg_time

        for m in new_msgs:
            await self._handle_chat_message(m)

    async def _handle_chat_message(self, msg: dict):
        """Convert a Mineflayer chat message to a gateway MessageEvent."""
        username = msg.get("from", "")
        text = msg.get("message", "")

        if not username or not text:
            return

        # Skip our own messages to avoid loops
        if username.lower() == self._bot_username.lower():
            return

        # Build source
        source = SessionSource(
            platform=Platform.MINECRAFT,
            chat_id="minecraft_chat",
            user_id=username.lower(),
            username=username,
        )

        event = MessageEvent(
            source=source,
            type=MessageType.TEXT,
            content=text,
            raw_message=msg,
        )

        logger.debug("[Minecraft] <%s> %s", username, text)
        await self.handle_message(event)


def check_minecraft_requirements() -> bool:
    """Check if the Minecraft bot server is reachable."""
    try:
        url = f"{MC_API_URL}/health"
        urllib.request.urlopen(url, timeout=2)
        return True
    except Exception:
        return False
