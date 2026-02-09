/**
 * API service for the Ollama AI Tutor backend (port 8081).
 * Session-based architecture for Learning Mode.
 */

const TUTOR_BASE_URL = import.meta.env.VITE_TUTOR_URL || 'http://localhost:8081';

/**
 * Check if the AI tutor backend (Ollama) is available
 */
export const checkTutorHealth = async () => {
  try {
    const response = await fetch(`${TUTOR_BASE_URL}/api/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) throw new Error('Tutor backend unavailable');
    return await response.json();
  } catch {
    return { status: 'unavailable', ollama: false, model: '' };
  }
};

/**
 * Start a new learning session
 * @param {string} examId - Exam ID (e.g. 'SAA-C03-v1')
 * @returns {Promise<{session_id, exam_id, total_questions, question}>}
 */
export const startSession = async (examId) => {
  const response = await fetch(`${TUTOR_BASE_URL}/api/session/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ exam_id: examId }),
  });
  if (!response.ok) throw new Error('Failed to start session');
  return await response.json();
};

/**
 * Get next question (adaptive selection)
 * @param {string} sessionId
 * @returns {Promise<{session_id, complete, question?, stats}>}
 */
export const getNextQuestion = async (sessionId) => {
  const response = await fetch(`${TUTOR_BASE_URL}/api/session/next`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!response.ok) throw new Error('Failed to get next question');
  return await response.json();
};

/**
 * Submit an answer for evaluation
 * @param {Object} params
 * @param {string} params.session_id
 * @param {number|null} params.answer_index - For single select
 * @param {number[]|null} params.answer_indices - For multi-select
 * @param {boolean} params.idk - "I don't know"
 * @returns {Promise<{correct, correct_answer, ai_response, needs_micro_check, ...}>}
 */
export const submitAnswer = async (params) => {
  const response = await fetch(`${TUTOR_BASE_URL}/api/session/answer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error('Failed to submit answer');
  return await response.json();
};

/**
 * Generate or check a micro-check question
 * @param {Object} params
 * @param {string} params.session_id
 * @param {string} params.action - "generate" or "check"
 * @param {number} [params.answer_index] - For checking
 * @returns {Promise<{micro_check?, correct?, mastered?, ...}>}
 */
export const microCheck = async (params) => {
  const response = await fetch(`${TUTOR_BASE_URL}/api/session/microcheck`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error('Failed to process micro-check');
  return await response.json();
};

/**
 * Get session status and stats
 * @param {string} sessionId
 * @returns {Promise<{session_id, stats}>}
 */
export const getSessionStatus = async (sessionId) => {
  const response = await fetch(
    `${TUTOR_BASE_URL}/api/session/status?session_id=${encodeURIComponent(sessionId)}`,
    { method: 'GET' }
  );
  if (!response.ok) throw new Error('Failed to get session status');
  return await response.json();
};

/**
 * Send a follow-up chat message to the AI tutor
 * @param {Object} params
 * @param {string} params.message
 * @param {string} params.exam_id
 * @param {string} params.question_context
 * @param {Array} params.history
 * @returns {Promise<{response: string}>}
 */
export const chatWithTutor = async (params) => {
  const response = await fetch(`${TUTOR_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error('Failed to chat with tutor');
  return await response.json();
};
