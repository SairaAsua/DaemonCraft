/**
 * VideoRecorder — FFmpeg-based screen/camera recorder
 *
 * Supports:
 *   - x11grab (screen capture on Linux)
 *   - v4l2 (OBS virtual camera, webcams)
 *   - segment recording (auto-split every N minutes to prevent data loss)
 */

import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

export class VideoRecorder {
  constructor(options = {}) {
    this.outputFile = options.outputFile || './recording.mkv';
    this.fps = options.fps || 30;
    this.resolution = options.resolution || '1920x1080';
    this.videoBitrate = options.videoBitrate || '8000k';
    this.audioBitrate = options.audioBitrate || '192k';
    this.source = options.source || 'screen'; // 'screen' | 'obs' | 'camera'
    this.device = options.device; // e.g. /dev/video0
    this.duration = options.duration || 3600; // max seconds
    this.segmentDuration = options.segmentDuration || 600; // 10 min segments
    this.onSegment = options.onSegment || (() => {});
    this.onError = options.onError || (() => {});

    this.ffmpeg = null;
    this.startTime = null;
    this.segmentFiles = [];
    this.isRunning = false;
  }

  buildArgs() {
    const args = ['-y'];

    // Input source
    if (this.source === 'screen') {
      // Linux X11 screen capture
      const display = process.env.DISPLAY || ':0.0';
      args.push('-f', 'x11grab');
      args.push('-framerate', String(this.fps));
      args.push('-video_size', this.resolution);
      args.push('-i', display);

      // Audio from PulseAudio
      args.push('-f', 'pulse');
      args.push('-i', 'default');
    } else if (this.source === 'obs' || this.source === 'camera') {
      // V4L2 device (OBS virtual camera or webcam)
      const device = this.device || '/dev/video0';
      args.push('-f', 'v4l2');
      args.push('-framerate', String(this.fps));
      args.push('-video_size', this.resolution);
      args.push('-i', device);

      // Audio from PulseAudio (game audio)
      args.push('-f', 'pulse');
      args.push('-i', 'default');
    } else {
      throw new Error(`Unknown source: ${this.source}`);
    }

    // Encoding settings — use mkv for robustness during crashes
    args.push('-c:v', 'libx264');
    args.push('-preset', 'veryfast');
    args.push('-b:v', this.videoBitrate);
    args.push('-maxrate', this.videoBitrate);
    args.push('-bufsize', '2M');
    args.push('-pix_fmt', 'yuv420p');
    args.push('-g', String(this.fps * 2)); // keyframe every 2 sec

    args.push('-c:a', 'aac');
    args.push('-b:a', this.audioBitrate);
    args.push('-ar', '48000');

    // Segment mode: split every N seconds to prevent total loss on crash
    if (this.segmentDuration > 0) {
      const segmentDir = path.dirname(this.outputFile);
      const segmentPattern = path.join(segmentDir, 'segment_%03d.mkv');
      args.push('-f', 'segment');
      args.push('-segment_time', String(this.segmentDuration));
      args.push('-reset_timestamps', '1');
      args.push('-segment_format', 'mkv');
      args.push(segmentPattern);
      this.segmentPattern = segmentPattern;
    } else {
      // Single file
      args.push('-t', String(this.duration));
      args.push(this.outputFile);
    }

    return args;
  }

  async start() {
    if (this.isRunning) throw new Error('Already running');

    const args = this.buildArgs();
    const ffmpegPath = process.env.FFMPEG_PATH || 'ffmpeg';

    return new Promise((resolve, reject) => {
      this.ffmpeg = spawn(ffmpegPath, args, {
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe'],
      });

      let stderrBuffer = '';
      this.ffmpeg.stderr.on('data', (data) => {
        stderrBuffer += data.toString();
        // Keep last 2KB
        if (stderrBuffer.length > 2048) stderrBuffer = stderrBuffer.slice(-2048);
      });

      this.ffmpeg.stdout.on('data', () => {}); // ignore

      this.ffmpeg.on('error', (err) => {
        this.isRunning = false;
        this.onError(err);
        reject(err);
      });

      this.ffmpeg.on('exit', (code) => {
        this.isRunning = false;
        if (code !== 0 && code !== 255) {
          const err = new Error(`FFmpeg exited with code ${code}: ${stderrBuffer.slice(-500)}`);
          this.onError(err);
        }
      });

      // Wait a bit to confirm it started
      setTimeout(() => {
        if (this.ffmpeg && this.ffmpeg.pid) {
          this.isRunning = true;
          this.startTime = Date.now();
          resolve();
        } else {
          reject(new Error('FFmpeg failed to start'));
        }
      }, 1500);
    });
  }

  async stop() {
    if (!this.ffmpeg || !this.isRunning) return;

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        // Force kill if graceful doesn't work
        try {
          this.ffmpeg.kill('SIGKILL');
        } catch {}
        resolve();
      }, 8000);

      this.ffmpeg.on('exit', () => {
        clearTimeout(timeout);
        this.isRunning = false;
        this.ffmpeg = null;
        this._mergeSegments().then(resolve).catch(reject);
      });

      // Graceful stop with 'q'
      try {
        this.ffmpeg.stdin.write('q');
      } catch {
        try {
          this.ffmpeg.kill('SIGTERM');
        } catch {}
      }
    });
  }

  async _mergeSegments() {
    if (!this.segmentPattern) return;

    const segmentDir = path.dirname(this.outputFile);
    const segments = fs
      .readdirSync(segmentDir)
      .filter((f) => f.startsWith('segment_') && f.endsWith('.mkv'))
      .sort();

    if (segments.length === 0) return;
    if (segments.length === 1) {
      // Just rename
      const oldPath = path.join(segmentDir, segments[0]);
      fs.renameSync(oldPath, this.outputFile);
      return;
    }

    // Create concat list
    const listFile = path.join(segmentDir, 'concat.txt');
    const listContent = segments.map((s) => `file '${path.join(segmentDir, s)}'`).join('\n');
    fs.writeFileSync(listFile, listContent);

    // Merge with ffmpeg
    const { spawn } = await import('child_process');
    return new Promise((resolve, reject) => {
      const merge = spawn('ffmpeg', [
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', listFile,
        '-c', 'copy',
        this.outputFile,
      ]);

      merge.on('exit', (code) => {
        // Cleanup
        try {
          fs.unlinkSync(listFile);
          segments.forEach((s) => fs.unlinkSync(path.join(segmentDir, s)));
        } catch {}

        if (code === 0) resolve();
        else reject(new Error(`Merge failed with code ${code}`));
      });

      merge.on('error', reject);
    });
  }

  getStatus() {
    if (!this.isRunning) return { running: false };
    return {
      running: true,
      elapsedSec: Math.round((Date.now() - this.startTime) / 1000),
      outputFile: this.outputFile,
    };
  }
}
