/**
 * OBSConnector — interacts with OBS Studio virtual camera
 *
 * On Linux, OBS creates a v4l2loopback device when virtual camera is started.
 * This module can:
 *   - List available video devices
 *   - Detect which one is the OBS virtual camera
 *   - Attempt to start/stop OBS virtual camera via obs-websocket (optional)
 */

import { spawn, exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

export class OBSConnector {
  constructor(options = {}) {
    this.obsHost = options.obsHost || 'localhost';
    this.obsPort = options.obsPort || 4455;
    this.obsPassword = options.obsPassword || '';
    this.ws = null;
  }

  async listDevices() {
    try {
      // Try v4l2-ctl first
      const { stdout } = await execAsync('v4l2-ctl --list-devices 2>/dev/null || true');
      return this._parseV4L2Devices(stdout);
    } catch {
      // Fallback: list /dev/video*
      const fs = await import('fs');
      const devices = [];
      try {
        const files = fs.default.readdirSync('/dev').filter((f) => f.startsWith('video'));
        for (const f of files) {
          devices.push({ path: `/dev/${f}`, name: `Video device ${f}` });
        }
      } catch {}
      return devices;
    }
  }

  _parseV4L2Devices(output) {
    const devices = [];
    const lines = output.split('\n');
    let currentName = '';
    for (const line of lines) {
      if (line.includes('/dev/video')) {
        devices.push({
          path: line.trim(),
          name: currentName.trim(),
          isOBS: currentName.toLowerCase().includes('obs') || currentName.toLowerCase().includes('virtual'),
        });
      } else if (line.trim() && !line.startsWith('\t')) {
        currentName = line.trim().replace(/:$/, '');
      }
    }
    return devices;
  }

  async detectOBSDevice() {
    const devices = await this.listDevices();
    return devices.find((d) => d.isOBS) || devices[0] || null;
  }

  async startVirtualCam() {
    // Try to use obs-websocket if available
    try {
      await this._obsWebSocketCall('StartVirtualCam');
      return { ok: true, method: 'obs-websocket' };
    } catch {
      // Fallback: check if a virtual cam device already exists
      const device = await this.detectOBSDevice();
      if (device) {
        return { ok: true, method: 'v4l2-device', device };
      }
      return {
        ok: false,
        error: 'OBS virtual camera not found. Start it manually in OBS Studio (Tools > Virtual Camera).',
      };
    }
  }

  async stopVirtualCam() {
    try {
      await this._obsWebSocketCall('StopVirtualCam');
      return { ok: true };
    } catch {
      return { ok: true, note: 'Could not reach OBS websocket — ensure you stop virtual cam manually.' };
    }
  }

  async _obsWebSocketCall(requestType, requestData = {}) {
    // Simple OBS WebSocket v5 request
    return new Promise((resolve, reject) => {
      const WebSocketClient = require('ws');
      const ws = new WebSocketClient(`ws://${this.obsHost}:${this.obsPort}`);

      ws.on('open', () => {
        if (this.obsPassword) {
          // Auth handshake omitted for brevity — OBS ws v5 requires hello/identify
          // In production, implement full auth flow
        }
        ws.send(
          JSON.stringify({
            op: 6,
            d: {
              requestType,
              requestId: `${requestType}_${Date.now()}`,
              requestData,
            },
          })
        );
      });

      ws.on('message', (data) => {
        try {
          const msg = JSON.parse(data);
          if (msg.op === 7 && msg.d?.requestType === requestType) {
            ws.close();
            if (msg.d.requestStatus?.result) resolve(msg.d.responseData);
            else reject(new Error(msg.d.requestStatus?.comment || 'OBS request failed'));
          }
        } catch {
          // ignore
        }
      });

      ws.on('error', reject);
      ws.on('close', () => reject(new Error('Connection closed')));

      // Timeout
      setTimeout(() => {
        ws.close();
        reject(new Error('OBS websocket timeout'));
      }, 5000);
    });
  }
}
