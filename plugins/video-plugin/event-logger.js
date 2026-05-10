/**
 * EventLogger — captures game events with timestamps during recording
 *
 * Writes JSON Lines format for easy streaming analysis.
 */

import fs from 'fs';

export class EventLogger {
  constructor(eventFile) {
    this.eventFile = eventFile;
    this.stream = null;
    this.buffer = [];
    this.flushInterval = null;
    this.started = false;
  }

  start() {
    if (this.started) return;
    this.stream = fs.createWriteStream(this.eventFile, { flags: 'a' });
    this.flushInterval = setInterval(() => this._flush(), 1000);
    this.started = true;
  }

  stop() {
    if (!this.started) return;
    if (this.flushInterval) clearInterval(this.flushInterval);
    this._flush();
    if (this.stream) {
      this.stream.end();
      this.stream = null;
    }
    this.started = false;
  }

  logEvent(type, data) {
    if (!this.started) return;
    const entry = {
      ts: Date.now(),
      type,
      ...data,
    };
    this.buffer.push(JSON.stringify(entry));
    // Also flush immediately for critical events
    if (type === 'death' || type === 'combat' || type === 'quest') {
      this._flush();
    }
  }

  _flush() {
    if (this.buffer.length === 0 || !this.stream) return;
    const lines = this.buffer.join('\n') + '\n';
    this.stream.write(lines);
    this.buffer = [];
  }
}
