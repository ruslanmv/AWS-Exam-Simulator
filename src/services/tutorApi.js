/**
 * API service for the AI Tutor backend.
 *
 * Supports two backends:
 *  1. Local Ollama tutor (ollama_tutor.py on port 8081)
 *  2. OllaBridge Cloud (HuggingFace Spaces) — for Vercel deployments
 *
 * Fallback logic (in "auto" mode):
 *  - Try local tutor first (only on localhost)
 *  - If unavailable, route session/AI calls through OllaBridge Cloud
 *    using a client-side session driver.
 */

import {
  loadAISettings,
  checkOllaBridgeHealth,
  generateFeedback as obGenerateFeedback,
  generateMicroCheck as obGenerateMicroCheck,
  chatWithOllaBridge,
} from './ollabridgeService';
import { loadExamFromJSON } from '../utils/examLoader';

const TUTOR_BASE_URL = import.meta.env.VITE_TUTOR_URL || 'http://localhost:8081';

let _ollamaAvailable = null;
let _ollabridgeAvailable = null;
let _lastCheck = 0;

// Detect if the page is being served from localhost. On remote deployments
// (e.g. Vercel) probing http://localhost:8081 is meaningless and only produces
// noisy ERR_CONNECTION_REFUSED errors in the browser console.
function isLocalHost() {
  if (typeof window === 'undefined') return true;
  const host = window.location.hostname;
  return host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0' || host.endsWith('.local');
}

function getProvider() {
  const settings = loadAISettings();
  return settings.provider || 'auto';
}

function shouldUseTutor() {
  const provider = getProvider();
  if (provider === 'ollabridge') return false;
  if (provider === 'ollama') return true;
  // auto: only use the local tutor if we are actually on localhost AND
  // the previous probe succeeded.
  return _ollamaAvailable === true && isLocalHost();
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

  // Only probe the local tutor when we are actually running on localhost
  // and the user hasn't explicitly forced cloud-only mode.
  if (provider !== 'ollabridge' && isLocalHost()) {
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
  } else {
    _ollamaAvailable = false;
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

// ---------------------------------------------------------------------------
// Client-side session driver (used when the local Python tutor is offline).
//
// The OllaBridge Cloud endpoint is a stateless OpenAI-compatible API, so we
// keep the session bookkeeping (current question, mastery, weak tags, ...)
// entirely in the browser and only call the cloud LLM for AI feedback.
// ---------------------------------------------------------------------------

const _clientSessions = new Map();

function _toLearningQuestion(rawQ, idx, total) {
  const correctIndices = [];
  const options = (rawQ.options || []).map((opt, i) => {
    const text = typeof opt === 'string' ? opt : opt.text;
    if (typeof opt === 'object' && opt.correct) correctIndices.push(i);
    return text;
  });
  return {
    text: rawQ.text || rawQ.question || '',
    options,
    correct_indices: correctIndices.length ? correctIndices : [0],
    multi_select: correctIndices.length > 1,
    tags: rawQ.tags || [],
    explanation: rawQ.explanation || '',
    question_number: idx + 1,
    index: idx,
    total,
  };
}

function _buildStats(session) {
  const total = session.questions.length;
  const answered = session.answered.size;
  const mastered = session.mastered.size;
  const correct = session.correctCount;
  return {
    total_questions: total,
    answered,
    mastered,
    accuracy: answered ? correct / answered : 0,
    mastery_level: mastered >= total * 0.8 ? 'expert'
      : mastered >= total * 0.5 ? 'proficient'
      : mastered >= total * 0.2 ? 'developing'
      : 'beginner',
    weak_tags: [],
  };
}

async function _startClientSession(examId) {
  const exam = await loadExamFromJSON(examId);
  const total = exam.questions.length;
  const questions = exam.questions.map((q, i) => _toLearningQuestion(q, i, total));
  const sessionId = `cloud_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

  const session = {
    id: sessionId,
    examId,
    examTitle: exam.title,
    questions,
    cursor: 0,
    answered: new Set(),
    mastered: new Set(),
    correctCount: 0,
    lastQuestion: null,
    lastWasCorrect: false,
    lastIdk: false,
  };
  _clientSessions.set(sessionId, session);

  session.lastQuestion = questions[0] || null;
  return {
    session_id: sessionId,
    question: session.lastQuestion,
    stats: _buildStats(session),
  };
}

async function _clientNext(sessionId) {
  const s = _clientSessions.get(sessionId);
  if (!s) throw new Error('Session not found');
  // Move to the next question that has not been mastered yet
  let idx = s.cursor + 1;
  while (idx < s.questions.length && s.mastered.has(idx)) idx++;
  if (idx >= s.questions.length) {
    return { complete: true, stats: _buildStats(s) };
  }
  s.cursor = idx;
  s.lastQuestion = s.questions[idx];
  return { question: s.lastQuestion, stats: _buildStats(s) };
}

async function _clientSubmit(params) {
  const s = _clientSessions.get(params.session_id);
  if (!s) throw new Error('Session not found');
  const q = s.lastQuestion;
  if (!q) throw new Error('No active question');

  let isCorrect = false;
  let userAnswerText = '';
  if (params.idk) {
    userAnswerText = "I don't know";
  } else if (q.multi_select && Array.isArray(params.answer_indices)) {
    const picked = [...params.answer_indices].sort();
    const expected = [...q.correct_indices].sort();
    isCorrect = picked.length === expected.length && picked.every((v, i) => v === expected[i]);
    userAnswerText = picked.map((i) => q.options[i]).join(', ');
  } else if (typeof params.answer_index === 'number') {
    isCorrect = q.correct_indices.includes(params.answer_index);
    userAnswerText = q.options[params.answer_index] || '';
  }

  s.answered.add(s.cursor);
  if (isCorrect && !params.idk) {
    s.correctCount += 1;
    s.mastered.add(s.cursor);
  }
  s.lastWasCorrect = isCorrect;
  s.lastIdk = !!params.idk;

  let aiResponse = null;
  try {
    aiResponse = await obGenerateFeedback(q, userAnswerText, isCorrect, !!params.idk, loadAISettings());
  } catch (err) {
    aiResponse = isCorrect && !params.idk
      ? `**Correct!** ${q.explanation || ''}`
      : `**${params.idk ? "Let's learn this!" : 'Not quite.'}** The correct answer is: ${q.options[q.correct_indices[0]] || ''}${q.explanation ? `\n\n**Explanation:** ${q.explanation}` : ''}`;
  }

  return {
    correct: isCorrect && !params.idk,
    correct_answer: q.options[q.correct_indices[0]] || '',
    ai_response: aiResponse,
    needs_micro_check: !(isCorrect && !params.idk),
    stats: _buildStats(s),
  };
}

async function _clientMicroCheck(params) {
  const s = _clientSessions.get(params.session_id);
  if (!s) throw new Error('Session not found');
  const q = s.lastQuestion;
  if (!q) throw new Error('No active question');

  if (params.action === 'generate') {
    let mc = null;
    try {
      mc = await obGenerateMicroCheck(q, loadAISettings());
    } catch { /* fall through */ }
    if (!mc) {
      mc = {
        question: `True or False: "${q.options[q.correct_indices[0]] || ''}" is the correct answer to the previous question.`,
        options: ['True', 'False'],
        correct_index: 0,
        explanation: 'This was the correct answer from the original question.',
      };
    }
    s.lastMicroCheck = mc;
    return { micro_check: mc };
  }

  if (params.action === 'check') {
    const mc = s.lastMicroCheck;
    if (!mc) throw new Error('No micro-check in progress');
    const correct = params.answer_index === mc.correct_index;
    if (correct) {
      s.mastered.add(s.cursor);
    }
    return {
      correct,
      mastered: correct,
      can_retry: !correct,
      explanation: mc.explanation || '',
      stats: _buildStats(s),
    };
  }

  throw new Error(`Unknown micro-check action: ${params.action}`);
}

// ---------------------------------------------------------------------------
// Public session API — prefers the local Python tutor, otherwise falls back
// to the cloud-driven client-side session.
// ---------------------------------------------------------------------------

export const startSession = async (examId) => {
  if (shouldUseTutor()) {
    try {
      const response = await fetch(`${TUTOR_BASE_URL}/api/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ exam_id: examId }),
      });
      if (response.ok) return await response.json();
    } catch { /* fall through */ }
  }
  if (_ollabridgeAvailable !== false) {
    return _startClientSession(examId);
  }
  throw new Error('No AI backend available — start the local tutor or configure OllaBridge in AI Settings.');
};

export const getNextQuestion = async (sessionId) => {
  if (sessionId && _clientSessions.has(sessionId)) {
    return _clientNext(sessionId);
  }
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
  if (params?.session_id && _clientSessions.has(params.session_id)) {
    return _clientSubmit(params);
  }
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
  if (params?.session_id && _clientSessions.has(params.session_id)) {
    return _clientMicroCheck(params);
  }
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
  if (sessionId && _clientSessions.has(sessionId)) {
    return { stats: _buildStats(_clientSessions.get(sessionId)) };
  }
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
