/**
 * TelegramSender — sends videos via Telegram Bot API
 *
 * Supports:
 *   - sendVideo for files up to 50MB
 *   - Chunked upload via multipart/form-data
 *   - Caption with markdown
 */

import fs from 'fs';
import FormData from 'form-data';
import fetch from 'node-fetch';

export class TelegramSender {
  constructor(options = {}) {
    this.botToken = options.botToken;
    this.chatId = options.chatId;
    this.apiBase = `https://api.telegram.org/bot${this.botToken}`;
  }

  async sendVideo(videoPath, caption = '') {
    const stats = fs.statSync(videoPath);
    const sizeMB = stats.size / (1024 * 1024);

    if (sizeMB > 50) {
      // Telegram bot API limit is 50MB for videos
      throw new Error(
        `Video is ${sizeMB.toFixed(1)}MB — exceeds Telegram 50MB limit. ` +
        `Try reducing target duration or quality.`
      );
    }

    const url = `${this.apiBase}/sendVideo`;
    const form = new FormData();
    form.append('chat_id', this.chatId);
    form.append('video', fs.createReadStream(videoPath));
    form.append('caption', caption.slice(0, 1024));
    form.append('parse_mode', 'Markdown');
    form.append('supports_streaming', 'true');

    const response = await fetch(url, {
      method: 'POST',
      body: form,
    });

    const result = await response.json();
    if (!result.ok) {
      throw new Error(`Telegram API error: ${result.description}`);
    }

    return result.result;
  }

  async sendMessage(text) {
    const url = `${this.apiBase}/sendMessage`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: this.chatId,
        text: text.slice(0, 4096),
        parse_mode: 'Markdown',
      }),
    });

    const result = await response.json();
    if (!result.ok) {
      throw new Error(`Telegram API error: ${result.description}`);
    }
    return result.result;
  }
}
