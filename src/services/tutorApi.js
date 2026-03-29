/**
 * API service for the AI Tutor backend.
 *
 * Supports two backends:
 *  1. Local Ollama tutor (ollama_tutor.py on port 8081)
 *  2. OllaBridge Cloud (HuggingFace Spaces) — for Vercel deployments
 *
 * Fallback logic (in "auto" mode):
 *  - Try local tutor first
 *  - If unavailable, route AI calls through OllaBridge Cloud
 */

import {
  loadAISettings,
  checkOllaBridgeHealth,
  generateFeedback as obGenerateFeedback,
  generateMicroCheck as obGenerateMicroCheck,
  chatWithOllaBridge,
} from './ollabridgeService';

const TUTOR_BASE_URL = import.meta.env.VITE_TUTOR_URL || 'http://localhost:8081';

let _ollamaAvailable = null;
let _ollabridgeAvailable = null;
let _lastCheck = 0;

function getProvider() {
  const settings = loadAISettings();
  return settings.provider || 'auto';
}

function shouldUseTutor() {
  const provider = getProvider();
  if (provider === 'ollabridge') return false;
  if (provider === 'ollama') return true;
  return _ollamaAvailable === true;
}

export const checkTutorHealth = async () => {
  const settings = loadAISettings();
  const provider = settings.provider || 'auto';
  const now = Date.now();

  if (now - _lastCheck < 10000 && _ollamaAvailable !== null) {
    return {
      status: _ollamaAvailable || _ollabridgeAvailable ? 'ok' : 'unavailable',
      ollama: _ollamaAvailable === true,
      ollabridge: _ollabridgeAvailable === true,
      model: settings.ollabridge?.model || '',
      provider: shouldUseTutor() ? 'ollama' : _ollabridgeAvailable ? 'ollabridge' : 'none',
    };
  }
  _lastCheck = now;

  if (provider !== 'ollabridge') {
    try {
      const response = await fetch(`${TUTOR_BASE_URL}/api/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(3000),
      });
      if (response.ok) {
        const data = await response.json();
        _ollamaAvailable = data.ollama === true;
      } else {
        _ollamaAvailable = false;
      }
    } catch {
      _ollamaAvailable = false;
    }
  }

  if (provider !== 'ollama') {
    try {
      const result = await checkOllaBridgeHealth(settings);
      _ollabridgeAvailable = result.available;
    } catch {
      _ollabridgeAvailable = false;
    }
  }

  const active = provider === 'ollama'
    ? (_ollamaAvailable ? 'ollama' : 'none')
    : provider === 'ollabridge'
    ? (_ollabridgeAvailable ? 'ollabridge' : 'none')
    : _ollamaAvailable ? 'ollama' : (_ollabridgeAvailable ? 'ollabridge' : 'none');

  return {
    status: active !== 'none' ? 'ok' : 'unavailable',
    ollama: _ollamaAvailable === true,
    ollabridge: _ollabridgeAvailable === true,
    model: settings.ollabridge?.model || '',
    provider: active,
  };
};

export const resetHealthCache = () => {
  _ollamaAvailable = null;
  _ollabridgeAvailable = null;
  _lastCheck = 0;
};

export const startSession = async (examId) => {
  if (shouldUseTutor()) {
    const response = await fetch(`${TUTOR_BASE_URL}/api/session/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ exam_id: examId }),
    });
    if (response.ok) return await response.json();
  }
  throw new Error('Local tutor unavailable — using OllaBridge Cloud for AI');
};

export const getNextQuestion = async (sessionId) => {
  if (shouldUseTutor()) {
    const response = await fetch(`${TUTOR_BASE_URL}/api/session/next`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (response.ok) return await response.json();
  }
  throw new Error('Local tutor unavailable');
};

export const submitAnswer = async (params) => {
  if (shouldUseTutor()) {
    const response = await fetch(`${TUTOR_BASE_URL}/api/session/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (response.ok) return await response.json();
  }
  throw new Error('Local tutor unavailable');
};

export const microCheck = async (params) => {
  if (shouldUseTutor()) {
    const response = await fetch(`${TUTOR_BASE_URL}/api/session/microcheck`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    if (response.ok) return await response.json();
  }
  throw new Error('Local tutor unavailable');
};

export const getSessionStatus = async (sessionId) => {
  if (shouldUseTutor()) {
    const response = await fetch(
      `${TUTOR_BASE_URL}/api/session/status?session_id=${encodeURIComponent(sessionId)}`,
      { method: 'GET' }
    );
    if (response.ok) return await response.json();
  }
  throw new Error('Local tutor unavailable');
};

export const chatWithTutor = async (params) => {
  if (shouldUseTutor()) {
    try {
      const response = await fetch(`${TUTOR_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      if (response.ok) return await response.json();
    } catch {
      // Fall through to OllaBridge
    }
  }

  if (_ollabridgeAvailable !== false) {
    const settings = loadAISettings();
    const text = await chatWithOllaBridge(
      params.message,
      params.question_context,
      params.history,
      params.exam_id,
      settings,
    );
    return { response: text };
  }

  throw new Error('No AI backend available');
};

export { obGenerateFeedback as generateCloudFeedback };
export { obGenerateMicroCheck as generateCloudMicroCheck };
