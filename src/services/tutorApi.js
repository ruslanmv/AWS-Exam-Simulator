/**
 * API service for the Ollama AI Tutor backend (port 8081).
 * Used by the Learning Mode to evaluate answers and chat with the AI.
 */

const TUTOR_BASE_URL = import.meta.env.VITE_TUTOR_URL || 'http://localhost:8081';

/**
 * Check if the AI tutor backend (Ollama) is available
 * @returns {Promise<{status: string, ollama: boolean, model: string}>}
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
 * Submit an answer for AI evaluation and deep-dive teaching
 * @param {Object} params
 * @param {string} params.exam_id - Exam ID
 * @param {number} params.question_index - Question index in the exam
 * @param {string} params.user_answer - The user's selected answer text
 * @param {string} params.question_text - The question text
 * @param {string[]} params.options - All option texts
 * @param {string} params.correct_answer - The correct answer text
 * @param {string} params.explanation - Official explanation if available
 * @returns {Promise<{correct: boolean, correct_answer: string, ai_response: string}>}
 */
export const evaluateAnswer = async (params) => {
  const response = await fetch(`${TUTOR_BASE_URL}/api/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!response.ok) throw new Error('Failed to evaluate answer');
  return await response.json();
};

/**
 * Send a follow-up chat message to the AI tutor
 * @param {Object} params
 * @param {string} params.message - User message
 * @param {string} params.exam_id - Exam ID for context
 * @param {string} params.question_context - Current question context
 * @param {Array} params.history - Conversation history [{role, content}]
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
