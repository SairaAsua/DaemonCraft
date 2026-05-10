#!/usr/bin/env node
/**
 * DaemonCraft Video Plugin
 *
 * Integrates screen recording, OBS virtual camera, event logging,
 * AI-powered highlight detection, auto-editing, and Telegram delivery
 * into the DaemonCraft Minecraft ecosystem.
 *
 * Environment:
 *   BOT_WS_URL      WebSocket URL of the bot dashboard (default: ws://localhost:3002/ws)
 *   VIDEO_API_PORT  HTTP port for this plugin (default: 3010)
 *   VIDEO_DIR       Where recordings are stored (default: ./recordings)
 *   TELEGRAM_BOT_TOKEN   Telegram bot token for sending videos
 *   TELEGRAM_CHAT_ID     Target chat ID for video delivery
 *   OLLAMA_URL      Ollama API URL for AI analysis (default: http://10.10.20.1:11434)
 *   OLLAMA_MODEL    Model for video analysis (default: gemma4:e4b-it-q8_0)
 */

import fs from 'fs';
import path from 'path';
import http from 'http';
import { URL } from 'url';
import { spawn } from 'child_process';
import { WebSocket } from 'ws';
import { VideoRecorder } from './video-recorder.js';
import { EventLogger } from './event-logger.js';
import { VideoAnalyzer } from './video-analyzer.js';
import { VideoEditor } from './video-editor.js';
import { TelegramSender } from './telegram-sender.js';
import { OBSConnector } from './obs-connector.js';

// ═══════════════════════════════════════════════════════════════════
// Configuration (env overrides config.yaml)
// ═══════════════════════════════════════════════════════════════════

function loadConfig() {
  const configPath = path.join(process.cwd(), 'config.yaml');
  let fileConfig = {};
  if (fs.existsSync(configPath)) {
    try {
      const yaml = fs.readFileSync(configPath, 'utf8');
      // Simple YAML parser for flat keys
      yaml.split('\n').forEach((line) => {
        const m = line.match(/^(\w+):\s*(.*)$/);
        if (m) {
          const key = m[1];
          const val = m[2].replace(/^"|"$/g, '').replace(/^'|'$/g, '');
          fileConfig[key] = val;
        }
      });
    } catch (e) {
      console.error('Config load error:', e.message);
    }
  }
  return fileConfig;
}

const FILE_CONFIG = loadConfig();

const CONFIG = {
  botWsUrl: process.env.BOT_WS_URL || 'ws://localhost:3002/ws',
  apiPort: parseInt(process.env.VIDEO_API_PORT || FILE_CONFIG.botApiPort || '3010'),
  videoDir: process.env.VIDEO_DIR || path.join(process.cwd(), 'recordings'),
  telegramBotToken: process.env.TELEGRAM_BOT_TOKEN || FILE_CONFIG.telegramBotToken || '',
  telegramChatId: process.env.TELEGRAM_CHAT_ID || FILE_CONFIG.telegramChatId || '',
  ollamaUrl: process.env.OLLAMA_URL || FILE_CONFIG.ollamaUrl || 'http://10.10.20.1:11434',
  ollamaModel: process.env.OLLAMA_MODEL || FILE_CONFIG.ollamaModel || 'gemma4:e4b-it-q8_0',
  defaultDuration: 3600,
  fps: parseInt(FILE_CONFIG.defaultFPS || '24'),
  resolution: FILE_CONFIG.defaultResolution || '1366x768',
  videoBitrate: '8000k',
  audioBitrate: '192k',
  framesPerMinute: 6,
  maxHighlights: 20,
  defaultOutputMinutes: parseInt(FILE_CONFIG.defaultOutputMinutes || '5'),
  autoReconnect: FILE_CONFIG.autoReconnect === 'true' || FILE_CONFIG.autoReconnect === true,
};

// Ensure directories exist
fs.mkdirSync(CONFIG.videoDir, { recursive: true });
const CLIPS_DIR = path.join(CONFIG.videoDir, 'clips');
const OUTPUTS_DIR = path.join(CONFIG.videoDir, 'outputs');
fs.mkdirSync(CLIPS_DIR, { recursive: true });
fs.mkdirSync(OUTPUTS_DIR, { recursive: true });

// ═══════════════════════════════════════════════════════════════════
// Plugin State
// ═══════════════════════════════════════════════════════════════════

let recorder = null;
let logger = null;
let analyzer = null;
let editor = null;
let telegram = null;
let obs = null;

let botWs = null;
let botReconnectTimer = null;
let isRecording = false;
let currentSession = null; // { id, startedAt, videoFile, eventFile, sessionDir }
let pluginClients = new Set(); // WebSocket clients for plugin dashboard

function log(msg) {
  const ts = new Date().toLocaleTimeString();
  console.log(`[VideoPlugin ${ts}] ${msg}`);
}

// ═══════════════════════════════════════════════════════════════════
// Bot WebSocket Connection
// ═══════════════════════════════════════════════════════════════════

function connectBot() {
  if (botWs) {
    try { botWs.close(); } catch {}
  }

  log(`Connecting to bot at ${CONFIG.botWsUrl}...`);
  botWs = new WebSocket(CONFIG.botWsUrl);

  botWs.on('open', () => {
    log('Connected to DaemonCraft bot dashboard');
    broadcastPlugin({ type: 'bot_status', connected: true });
  });

  botWs.on('message', (data) => {
    try {
      const msg = JSON.parse(data);
      handleBotMessage(msg);
    } catch (e) {
      // ignore malformed
    }
  });

  botWs.on('close', () => {
    log('Bot WebSocket disconnected');
    broadcastPlugin({ type: 'bot_status', connected: false });
    if (CONFIG.autoReconnect) {
      log('Reconnecting in 5s...');
      botReconnectTimer = setTimeout(connectBot, 5000);
    } else {
      log('Auto-reconnect disabled — staying offline until recording starts');
    }
  });

  botWs.on('error', (err) => {
    log(`Bot WebSocket error: ${err.message}`);
  });
}

function handleBotMessage(msg) {
  // Log relevant events for highlight detection
  if (!logger || !isRecording) return;

  const ts = Date.now();

  switch (msg.type) {
    case 'chat': {
      const msgs = msg.data || [];
      msgs.forEach((m) => {
        logger.logEvent('chat', {
          time: m.time || ts,
          from: m.from,
          message: m.message,
          whisper: m.whisper,
          private: m.private,
        });
      });
      break;
    }
    case 'status': {
      const data = msg.data || {};
      if (data.health !== undefined && data.health < 8) {
        logger.logEvent('danger', {
          time: ts,
          health: data.health,
          position: data.position,
          note: 'Low health detected',
        });
      }
      if (data.nearby_entities) {
        const hostiles = data.nearby_entities.filter(
          (e) => e.type && /zombie|skeleton|creeper|spider|enderman|witch|drowned|phantom|blaze|ghast/.test(e.type)
        );
        if (hostiles.length > 2) {
          logger.logEvent('combat', {
            time: ts,
            hostiles: hostiles.map((h) => h.type),
            count: hostiles.length,
            note: 'Multiple hostiles nearby',
          });
        }
      }
      break;
    }
    case 'actions': {
      const actions = msg.data || [];
      actions.slice(-3).forEach((a) => {
        const interesting = ['attack', 'eat', 'flee', 'deathpoint', 'collect', 'craft', 'place', 'build'];
        if (interesting.some((k) => a.action?.includes(k))) {
          logger.logEvent('action', {
            time: a.time || ts,
            action: a.action,
            status: a.status,
          });
        }
      });
      break;
    }
    case 'quest_event': {
      logger.logEvent('quest', {
        time: ts,
        event_type: msg.data?.event_type,
        message: msg.data?.message,
        from_phase: msg.data?.from_phase,
        to_phase: msg.data?.to_phase,
      });
      break;
    }
    default:
      break;
  }
}

// ═══════════════════════════════════════════════════════════════════
// Recording Lifecycle
// ═══════════════════════════════════════════════════════════════════

async function startRecording(options = {}) {
  if (isRecording) {
    return { ok: false, error: 'Already recording' };
  }

  // Connect to bot if not already connected (needed for event logging)
  if (!botWs || botWs.readyState !== WebSocket.OPEN) {
    log('Connecting to bot for recording session...');
    connectBot();
  }

  const sessionId = `session_${Date.now()}`;
  const sessionDir = path.join(CONFIG.videoDir, sessionId);
  fs.mkdirSync(sessionDir, { recursive: true });

  const videoFile = path.join(sessionDir, 'raw.mkv');
  const eventFile = path.join(sessionDir, 'events.jsonl');

  currentSession = {
    id: sessionId,
    startedAt: Date.now(),
    videoFile,
    eventFile,
    sessionDir,
    options,
  };

  // Initialize event logger
  logger = new EventLogger(eventFile);
  logger.start();

  // Initialize recorder
  recorder = new VideoRecorder({
    outputFile: videoFile,
    fps: options.fps || CONFIG.fps,
    resolution: options.resolution || CONFIG.resolution,
    videoBitrate: options.videoBitrate || CONFIG.videoBitrate,
    audioBitrate: options.audioBitrate || CONFIG.audioBitrate,
    source: options.source || 'screen', // 'screen' | 'obs' | 'camera'
    device: options.device, // e.g. /dev/video0 for OBS virtual cam
    duration: options.duration || CONFIG.defaultDuration,
    onSegment: (segmentFile) => {
      log(`Segment saved: ${path.basename(segmentFile)}`);
    },
    onError: (err) => {
      log(`Recorder error: ${err.message}`);
      broadcastPlugin({ type: 'recording_error', error: err.message });
    },
  });

  try {
    await recorder.start();
    isRecording = true;
    log(`Recording started: ${sessionId}`);
    broadcastPlugin({ type: 'recording_status', status: 'recording', sessionId, startedAt: currentSession.startedAt });
    return { ok: true, sessionId };
  } catch (err) {
    isRecording = false;
    logger.stop();
    log(`Failed to start recording: ${err.message}`);
    return { ok: false, error: err.message };
  }
}

async function stopRecording() {
  if (!isRecording || !recorder) {
    return { ok: false, error: 'Not recording' };
  }

  log('Stopping recording...');
  broadcastPlugin({ type: 'recording_status', status: 'finalizing' });

  try {
    await recorder.stop();
    if (logger) logger.stop();
    isRecording = false;

    currentSession.endedAt = Date.now();
    currentSession.durationSec = Math.round((currentSession.endedAt - currentSession.startedAt) / 1000);

    // Save session metadata
    const metaFile = path.join(currentSession.sessionDir, 'meta.json');
    fs.writeFileSync(metaFile, JSON.stringify({
      id: currentSession.id,
      startedAt: currentSession.startedAt,
      endedAt: currentSession.endedAt,
      durationSec: currentSession.durationSec,
      options: currentSession.options,
      videoFile: path.basename(currentSession.videoFile),
      eventFile: path.basename(currentSession.eventFile),
    }, null, 2));

    log(`Recording saved. Duration: ${currentSession.durationSec}s`);
    broadcastPlugin({
      type: 'recording_status',
      status: 'finished',
      sessionId: currentSession.id,
      durationSec: currentSession.durationSec,
      sessionDir: currentSession.sessionDir,
    });

    return { ok: true, session: currentSession };
  } catch (err) {
    log(`Error stopping recording: ${err.message}`);
    isRecording = false;
    return { ok: false, error: err.message };
  }
}

// ═══════════════════════════════════════════════════════════════════
// Analysis & Editing Pipeline
// ═══════════════════════════════════════════════════════════════════

async function analyzeSession(sessionId, targetMinutes = CONFIG.defaultOutputMinutes) {
  const sessionDir = path.join(CONFIG.videoDir, sessionId);
  if (!fs.existsSync(sessionDir)) {
    return { ok: false, error: 'Session not found' };
  }

  const metaPath = path.join(sessionDir, 'meta.json');
  if (!fs.existsSync(metaPath)) {
    return { ok: false, error: 'Session metadata missing' };
  }
  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));

  const videoFile = path.join(sessionDir, meta.videoFile);
  const eventFile = path.join(sessionDir, meta.eventFile);

  if (!fs.existsSync(videoFile)) {
    return { ok: false, error: 'Video file missing' };
  }

  log(`Analyzing session ${sessionId} for ${targetMinutes}min output...`);
  broadcastPlugin({ type: 'analysis_status', status: 'analyzing', sessionId });

  try {
    // Initialize analyzer
    analyzer = new VideoAnalyzer({
      ollamaUrl: CONFIG.ollamaUrl,
      ollamaModel: CONFIG.ollamaModel,
      framesPerMinute: CONFIG.framesPerMinute,
      maxHighlights: CONFIG.maxHighlights,
      videoFile,
      eventFile,
      sessionDir,
    });

    const highlights = await analyzer.analyze(targetMinutes);

    // Save highlights
    const highlightsFile = path.join(sessionDir, 'highlights.json');
    fs.writeFileSync(highlightsFile, JSON.stringify(highlights, null, 2));

    log(`Analysis complete. Found ${highlights.length} highlights`);
    broadcastPlugin({ type: 'analysis_status', status: 'done', sessionId, highlightsCount: highlights.length });

    return { ok: true, highlights };
  } catch (err) {
    log(`Analysis failed: ${err.message}`);
    broadcastPlugin({ type: 'analysis_status', status: 'error', error: err.message });
    return { ok: false, error: err.message };
  }
}

async function editSession(sessionId, targetMinutes = CONFIG.defaultOutputMinutes, options = {}) {
  const sessionDir = path.join(CONFIG.videoDir, sessionId);
  const highlightsFile = path.join(sessionDir, 'highlights.json');
  const metaPath = path.join(sessionDir, 'meta.json');

  if (!fs.existsSync(highlightsFile)) {
    return { ok: false, error: 'Highlights not found — run analyze first' };
  }

  const highlights = JSON.parse(fs.readFileSync(highlightsFile, 'utf8'));
  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  const videoFile = path.join(sessionDir, meta.videoFile);

  log(`Editing session ${sessionId} to ~${targetMinutes}min...`);
  broadcastPlugin({ type: 'edit_status', status: 'editing', sessionId });

  try {
    editor = new VideoEditor({
      ffmpegPath: 'ffmpeg',
      ffprobePath: 'ffprobe',
      sessionDir,
      outputDir: OUTPUTS_DIR,
    });

    const outputFile = path.join(OUTPUTS_DIR, `${sessionId}_edit_${targetMinutes}min.mp4`);

    await editor.createHighlightReel({
      sourceVideo: videoFile,
      highlights,
      targetDurationMinutes: targetMinutes,
      outputFile,
      addTransitions: options.addTransitions !== false,
      addMusic: options.addMusic || false,
      musicFile: options.musicFile,
      titleCard: options.titleCard,
    });

    log(`Edit complete: ${outputFile}`);
    broadcastPlugin({ type: 'edit_status', status: 'done', sessionId, outputFile });

    return { ok: true, outputFile };
  } catch (err) {
    log(`Edit failed: ${err.message}`);
    broadcastPlugin({ type: 'edit_status', status: 'error', error: err.message });
    return { ok: false, error: err.message };
  }
}

// ── AI Narrative Editor ───────────────────────────────────────────

function runAIEdit(videoPath, targetMinutes, outputPath, narrativeJsonPath) {
  return new Promise((resolve, reject) => {
    const wrapperPath = path.join(process.cwd(), 'ai_editor', 'ai_edit_wrapper.py');
    const args = [
      wrapperPath,
      '--video', videoPath,
      '--duration', String(targetMinutes),
      '--output', outputPath,
      '--narrative-json', narrativeJsonPath,
    ];

    log(`Running AI editor: python3 ${args.join(' ')}`);
    const proc = spawn('python3', args, {
      cwd: process.cwd(),
      env: {
        ...process.env,
        OLLAMA_HOST: CONFIG.ollamaUrl,
        OLLAMA_MODEL: CONFIG.ollamaModel,
        TELEGRAM_BOT_TOKEN: CONFIG.telegramBotToken,
        TELEGRAM_CHAT_ID: CONFIG.telegramChatId,
      },
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
      const lines = data.toString().split('\n').filter((l) => l.trim());
      lines.forEach((line) => {
        if (line.includes('[VideoAI]')) log(`[AI] ${line.trim()}`);
      });
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        return reject(new Error(`AI editor exited with code ${code}. stderr: ${stderr.slice(0, 500)}`));
      }
      try {
        const result = JSON.parse(stdout.trim().split('\n').pop());
        resolve(result);
      } catch (e) {
        reject(new Error(`Failed to parse AI editor output: ${e.message}. stdout: ${stdout.slice(0, 500)}`));
      }
    });

    proc.on('error', (err) => reject(err));
  });
}

async function aiEditSession(sessionId, targetMinutes = CONFIG.defaultOutputMinutes, options = {}) {
  const sessionDir = path.join(CONFIG.videoDir, sessionId);
  if (!fs.existsSync(sessionDir)) {
    return { ok: false, error: 'Session not found' };
  }

  const metaPath = path.join(sessionDir, 'meta.json');
  if (!fs.existsSync(metaPath)) {
    return { ok: false, error: 'Session metadata missing' };
  }

  const meta = JSON.parse(fs.readFileSync(metaPath, 'utf8'));
  const videoFile = path.join(sessionDir, meta.videoFile);

  if (!fs.existsSync(videoFile)) {
    return { ok: false, error: 'Video file missing' };
  }

  const outputFile = path.join(OUTPUTS_DIR, `${sessionId}_ai_edit_${targetMinutes}min.mp4`);
  const narrativeJson = path.join(sessionDir, 'narrative.json');

  log(`AI narrative edit: session=${sessionId} target=${targetMinutes}min`);
  broadcastPlugin({ type: 'edit_status', status: 'ai_analyzing', sessionId });

  try {
    const result = await runAIEdit(videoFile, targetMinutes, outputFile, narrativeJson);
    if (!result.ok) {
      throw new Error(result.error || 'AI editor failed');
    }

    log(`AI edit complete: ${result.outputFile}`);
    broadcastPlugin({ type: 'edit_status', status: 'done', sessionId, outputFile: result.outputFile });

    let narrativeInfo = {};
    if (fs.existsSync(narrativeJson)) {
      narrativeInfo = JSON.parse(fs.readFileSync(narrativeJson, 'utf8'));
    }

    return {
      ok: true,
      outputFile: result.outputFile,
      title: result.title,
      summary: result.summary,
      description: result.description,
      durationSeconds: result.durationSeconds,
      narrativeInfo,
    };
  } catch (err) {
    log(`AI edit failed: ${err.message}`);
    broadcastPlugin({ type: 'edit_status', status: 'error', error: err.message });
    return { ok: false, error: err.message };
  }
}

async function sendToTelegram(outputFile, caption = '') {
  if (!CONFIG.telegramBotToken || !CONFIG.telegramChatId) {
    return { ok: false, error: 'Telegram not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID' };
  }

  if (!fs.existsSync(outputFile)) {
    return { ok: false, error: 'Output file not found' };
  }

  log(`Sending video to Telegram: ${path.basename(outputFile)}`);
  broadcastPlugin({ type: 'telegram_status', status: 'sending', file: path.basename(outputFile) });

  try {
    telegram = new TelegramSender({
      botToken: CONFIG.telegramBotToken,
      chatId: CONFIG.telegramChatId,
    });

    await telegram.sendVideo(outputFile, caption);
    log('Video sent to Telegram successfully');
    broadcastPlugin({ type: 'telegram_status', status: 'sent', file: path.basename(outputFile) });
    return { ok: true };
  } catch (err) {
    log(`Telegram send failed: ${err.message}`);
    broadcastPlugin({ type: 'telegram_status', status: 'error', error: err.message });
    return { ok: false, error: err.message };
  }
}

// ═══════════════════════════════════════════════════════════════════
// Plugin HTTP API
// ═══════════════════════════════════════════════════════════════════

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', (chunk) => (data += chunk));
    req.on('end', () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch {
        reject(new Error('Invalid JSON'));
      }
    });
  });
}

function respond(res, status, data) {
  res.writeHead(status, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
  });
  res.end(JSON.stringify(data));
}

const httpServer = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(200, {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    });
    return res.end();
  }

  const url = new URL(req.url, `http://localhost:${CONFIG.apiPort}`);
  const pathname = url.pathname;

  try {
    // ── GET ─────────────────────────────────────
    if (req.method === 'GET') {
      if (pathname === '/health') {
        return respond(res, 200, {
          ok: true,
          recording: isRecording,
          session: currentSession
            ? {
                id: currentSession.id,
                startedAt: currentSession.startedAt,
                durationSec: isRecording
                  ? Math.round((Date.now() - currentSession.startedAt) / 1000)
                  : currentSession.durationSec,
              }
            : null,
        });
      }

      if (pathname === '/sessions') {
        const sessions = fs
          .readdirSync(CONFIG.videoDir)
          .filter((d) => d.startsWith('session_'))
          .map((id) => {
            const metaPath = path.join(CONFIG.videoDir, id, 'meta.json');
            try {
              return JSON.parse(fs.readFileSync(metaPath, 'utf8'));
            } catch {
              return { id, error: 'no meta' };
            }
          })
          .filter(Boolean);
        return respond(res, 200, { ok: true, sessions });
      }

      if (pathname === '/obs/devices') {
        obs = obs || new OBSConnector();
        const devices = await obs.listDevices();
        return respond(res, 200, { ok: true, devices });
      }

      if (pathname === '/config') {
        return respond(res, 200, {
          ok: true,
          config: {
            videoDir: CONFIG.videoDir,
            defaultDuration: CONFIG.defaultDuration,
            fps: CONFIG.fps,
            resolution: CONFIG.resolution,
            defaultOutputMinutes: CONFIG.defaultOutputMinutes,
            telegramConfigured: Boolean(CONFIG.telegramBotToken && CONFIG.telegramChatId),
          },
        });
      }
    }

    // ── POST ────────────────────────────────────
    if (req.method === 'POST') {
      const body = await parseBody(req);

      if (pathname === '/record/start') {
        const result = await startRecording(body);
        return respond(res, result.ok ? 200 : 409, result);
      }

      if (pathname === '/record/stop') {
        const result = await stopRecording();
        return respond(res, result.ok ? 200 : 400, result);
      }

      if (pathname === '/analyze') {
        const { sessionId, targetMinutes } = body;
        if (!sessionId) return respond(res, 400, { ok: false, error: 'sessionId required' });
        const result = await analyzeSession(sessionId, targetMinutes || CONFIG.defaultOutputMinutes);
        return respond(res, result.ok ? 200 : 400, result);
      }

      if (pathname === '/edit') {
        const { sessionId, targetMinutes, options } = body;
        if (!sessionId) return respond(res, 400, { ok: false, error: 'sessionId required' });
        const result = await editSession(
          sessionId,
          targetMinutes || CONFIG.defaultOutputMinutes,
          options || {}
        );
        return respond(res, result.ok ? 200 : 400, result);
      }

      if (pathname === '/pipeline') {
        // Full pipeline: analyze + edit + optionally send
        const { sessionId, targetMinutes, options, sendToTelegram: sendTelegram } = body;
        if (!sessionId) return respond(res, 400, { ok: false, error: 'sessionId required' });

        const analyzeResult = await analyzeSession(sessionId, targetMinutes || CONFIG.defaultOutputMinutes);
        if (!analyzeResult.ok) return respond(res, 400, analyzeResult);

        const editResult = await editSession(
          sessionId,
          targetMinutes || CONFIG.defaultOutputMinutes,
          options || {}
        );
        if (!editResult.ok) return respond(res, 400, editResult);

        if (sendTelegram) {
          const caption = body.caption || `DaemonCraft highlights — ${targetMinutes || CONFIG.defaultOutputMinutes}min`;
          const sendResult = await sendToTelegram(editResult.outputFile, caption);
          return respond(res, sendResult.ok ? 200 : 400, {
            ok: sendResult.ok,
            analyze: analyzeResult,
            edit: editResult,
            telegram: sendResult,
          });
        }

        return respond(res, 200, {
          ok: true,
          analyze: analyzeResult,
          edit: editResult,
        });
      }

      if (pathname === '/edit/ai') {
        const { sessionId, targetMinutes, sendToTelegram: sendTelegram } = body;
        if (!sessionId) return respond(res, 400, { ok: false, error: 'sessionId required' });

        const result = await aiEditSession(
          sessionId,
          targetMinutes || CONFIG.defaultOutputMinutes,
          body.options || {}
        );
        if (!result.ok) return respond(res, 400, result);

        if (sendTelegram) {
          const narrativeInfo = result.narrativeInfo || {};
          const caption = `
🎬 <b>${narrativeInfo.title || 'Video de Minecraft'}</b>

📜 ${narrativeInfo.summary || ''}

💬 ${narrativeInfo.description || ''}

⏱️ Duración: ${(result.durationSeconds / 60).toFixed(1)} min

🎨 Editado por <b>Eko AI</b> ♡
          `.trim();
          const sendResult = await sendToTelegram(result.outputFile, caption);
          return respond(res, sendResult.ok ? 200 : 400, {
            ok: sendResult.ok,
            aiEdit: result,
            telegram: sendResult,
          });
        }

        return respond(res, 200, { ok: true, ...result });
      }

      if (pathname === '/telegram/send') {
        const { file, caption } = body;
        if (!file) return respond(res, 400, { ok: false, error: 'file path required' });
        const result = await sendToTelegram(file, caption || '');
        return respond(res, result.ok ? 200 : 400, result);
      }

      if (pathname === '/obs/virtualcam/start') {
        obs = obs || new OBSConnector();
        const result = await obs.startVirtualCam();
        return respond(res, result.ok ? 200 : 400, result);
      }

      if (pathname === '/obs/virtualcam/stop') {
        obs = obs || new OBSConnector();
        const result = await obs.stopVirtualCam();
        return respond(res, result.ok ? 200 : 400, result);
      }
    }

    respond(res, 404, { ok: false, error: `Not found: ${pathname}` });
  } catch (err) {
    respond(res, 500, { ok: false, error: err.message });
  }
});

// ═══════════════════════════════════════════════════════════════════
// Plugin WebSocket (for dashboard panel)
// ═══════════════════════════════════════════════════════════════════

import { WebSocketServer } from 'ws';

const pluginWss = new WebSocketServer({ server: httpServer, path: '/ws' });

pluginWss.on('connection', (ws) => {
  pluginClients.add(ws);
  log(`Plugin dashboard client connected (${pluginClients.size} total)`);

  // Send current state
  ws.send(
    JSON.stringify({
      type: 'state',
      recording: isRecording,
      session: currentSession
        ? {
            id: currentSession.id,
            startedAt: currentSession.startedAt,
            durationSec: isRecording
              ? Math.round((Date.now() - currentSession.startedAt) / 1000)
              : currentSession.durationSec,
          }
        : null,
    })
  );

  ws.on('close', () => {
    pluginClients.delete(ws);
  });
  ws.on('error', () => pluginClients.delete(ws));
});

function broadcastPlugin(msg) {
  const json = JSON.stringify(msg);
  for (const ws of pluginClients) {
    try {
      ws.send(json);
    } catch {
      pluginClients.delete(ws);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════
// Startup
// ═══════════════════════════════════════════════════════════════════

httpServer.listen(CONFIG.apiPort, () => {
  log('╔══════════════════════════════════════════════════════════════════╗');
  log('║     DaemonCraft Video Plugin v1.0                    ║');
  log('╠══════════════════════════════════════════════════════════════════╣');
  log(`║  API:    http://localhost:${CONFIG.apiPort}                    ║`);
  log(`║  WS:     ws://localhost:${CONFIG.apiPort}/ws                 ║`);
  log(`║  Video:  ${CONFIG.videoDir.padEnd(40)}║`);
  log(`║  Ollama: ${CONFIG.ollamaModel.padEnd(40)}║`);
  log('╚══════════════════════════════════════════════════════════════════╝');

  if (CONFIG.autoReconnect) {
    connectBot();
  } else {
    log('Auto-reconnect disabled — bot connection will start on first recording');
  }
});

// Auto-cleanup on exit
process.on('SIGINT', async () => {
  log('Shutting down...');
  if (isRecording) await stopRecording();
  if (botWs) try { botWs.close(); } catch {}
  process.exit(0);
});
