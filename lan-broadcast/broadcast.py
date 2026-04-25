#!/usr/bin/env python3
"""
Minecraft Java LAN Discovery Broadcaster
Sends UDP multicast packets to 224.0.2.60:4445 every 1.5 seconds
so the dedicated server appears in the client's LAN server list.
"""
import socket
import struct
import time
import os
import sys

MULTICAST_GROUP = "224.0.2.60"
MULTICAST_PORT = 4445
INTERVAL = 1.5

motd = os.environ.get("BROADCAST_MOTD", "Minecraft Server")
port = os.environ.get("BROADCAST_PORT", "25565")

message = f"[MOTD]{motd}[/MOTD][AD]{port}[/AD]".encode("utf-8")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Set multicast TTL (try integer first, fallback to packed byte)
try:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
except (TypeError, OSError):
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack("b", 2))

# Enable multicast loopback so local clients on same machine can see it
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

print(f"LAN broadcaster started: {motd} on port {port}", flush=True)
print(f"Sending multicast to {MULTICAST_GROUP}:{MULTICAST_PORT} every {INTERVAL}s", flush=True)

try:
    while True:
        sent = sock.sendto(message, (MULTICAST_GROUP, MULTICAST_PORT))
        print(f"Sent {sent} bytes: {message!r}", flush=True)
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("Shutting down broadcaster.", flush=True)
finally:
    sock.close()
