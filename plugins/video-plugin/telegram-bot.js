/**
 * Telegram Bot para controlar el Video Plugin
 * Comandos: /record, /stop, /status, /clips, /edit
 */

import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs';

const API_BASE = 'https://api.telegram.org/bot';

export class TelegramBot {
  constructor(config) {
    this.token = config.telegram?.botToken;
    this.chatId = config.telegram?.chatId;
    this.baseUrl = `${API_BASE}${this.token}`;
    this.offset = 0;
    this.running = false;
    this.handlers = {};
  }

  on(command, handler) {
    this.handlers[command] = handler;
  }

  async sendMessage(text, options = {}) {
    if (!this.token || !this.chatId) return;
    try {
      await axios.post(`${this.baseUrl}/sendMessage`, {
        chat_id: this.chatId,
        text,
        parse_mode: 'HTML',
        ...options,
      });
    } catch (e) {
      console.error('[TelegramBot] sendMessage error:', e.message);
    }
  }

  async sendVideo(videoPath, caption = '') {
    if (!this.token || !this.chatId) return;
    try {
      const form = new FormData();
      form.append('chat_id', this.chatId);
      form.append('video', fs.createReadStream(videoPath));
      form.append('caption', caption);
      form.append('supports_streaming', 'true');
      await axios.post(`${this.baseUrl}/sendVideo`, form, {
        headers: form.getHeaders(),
        maxBodyLength: 2000 * 1024 * 1024, // 2GB
        maxContentLength: 2000 * 1024 * 1024,
      });
      console.log(`[TelegramBot] Video enviado: ${videoPath}`);
    } catch (e) {
      console.error('[TelegramBot] sendVideo error:', e.message);
      await this.sendMessage(`❌ Error enviando video: ${e.message}`);
    }
  }

  async start() {
    if (!this.token) {
      console.log('[TelegramBot] Sin token, bot desactivado');
      return;
    }
    this.running = true;
    console.log('[TelegramBot] Bot iniciado');
    await this.sendMessage('🔴 <b>DaemonCraft Video Bot</b> conectado\n\nUsá <b>/record</b> para empezar a grabar');
    this._poll();
  }

  async _poll() {
    while (this.running) {
      try {
        const res = await axios.get(`${this.baseUrl}/getUpdates`, {
          params: { offset: this.offset, limit: 10, timeout: 30 },
          timeout: 40000,
        });
        const updates = res.data.result || [];
        for (const update of updates) {
          this.offset = update.update_id + 1;
          await this._handleUpdate(update);
        }
      } catch (e) {
        if (e.code !== 'ECONNABORTED') {
          console.error('[TelegramBot] poll error:', e.message);
        }
      }
      await this._sleep(1000);
    }
  }

  async _handleUpdate(update) {
    const msg = update.message;
    if (!msg || !msg.text) return;
    const text = msg.text.trim();
    const chatId = msg.chat.id;
    // Solo responder al chat configurado o al que inició
    if (this.chatId && chatId.toString() !== this.chatId.toString()) return;

    if (text.startsWith('/')) {
      const parts = text.split(' ');
      const cmd = parts[0].split('@')[0]; // Remove bot username
      const args = parts.slice(1);
      const handler = this.handlers[cmd];
      if (handler) {
        try {
          await handler({ cmd, args, msg, chatId });
        } catch (e) {
          console.error(`[TelegramBot] Error en ${cmd}:`, e);
          await this.sendMessage(`❌ Error: ${e.message}`);
        }
      } else {
        await this.sendMessage(`❓ Comando desconocido: ${cmd}\nUsá /record, /stop, /status o /clips`);
      }
    }
  }

  stop() {
    this.running = false;
  }

  _sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }
}
