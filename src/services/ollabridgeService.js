/**
 * OllaBridge Cloud integration service.
 *
 * Provides LLM chat completions via OllaBridge Cloud (HuggingFace Spaces)
 * with automatic fallback: local Ollama tutor -> OllaBridge Cloud.
 *
 * Uses the proxy at /api/proxy for CORS bypass on Vercel deployments.
 */

const SETTINGS_KEY = 'aws_exam_ai_settings';

const DEFAULT_SETTINGS = {
  provider: 'auto',            // 'auto' | 'ollama' | 'ollabridge'
  ollabridge: {
    base_url: 'https://ruslanmv-ollabridge.hf.space',
    model: 'qwen2.5:1.5b',
    auth_mode: 'none',         // 'none' | 'apikey' | 'pairing'
    api_key: '',
    pair_token: '',
  },
};

// ---------------------------------------------------------------------------
// Settings persistence
// ---------------------------------------------------------------------------

export function loadAISettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const saved = JSON.parse(raw);
      return { ...DEFAULT_SETTINGS, ...saved, ollabridge: { ...DEFAULT_SETTINGS.ollabridge, ...saved?.ollabridge } };
    }
  } catch { /* ignore */ }
  return { ...DEFAULT_SETTINGS, ollabridge: { ...DEFAULT_SETTINGS.ollabridge } };
}

export function saveAISettings(settings) {
  try {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  } catch { /* ignore */ }
}

// ---------------------------------------------------------------------------
// Proxy-aware fetch (for Vercel CORS bypass)
// ---------------------------------------------------------------------------

function getProxyUrl() {
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/proxy`;
  }
  return '/api/proxy';
}

async function proxiedFetch(url, options = {}) {
  const { method = 'POST', headers = {}, body } = options;

  // Try direct fetch first (works in dev with CORS-enabled backends)
  try {
    const directResp = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(60000),
    });
    if (directResp.ok || directResp.status < 500) return directResp;
  } catch {
    // CORS or network error — fall through to proxy
  }

  // Use proxy
  const proxyUrl = getProxyUrl();
  const resp = await fetch(proxyUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      method,
      headers: { 'Content-Type': 'application/json', ...headers },
      body,
    }),
    signal: AbortSignal.timeout(60000),
  });
  return resp;
}

// ---------------------------------------------------------------------------
// OllaBridge Cloud API
// ---------------------------------------------------------------------------

function getAuthHeaders(settings) {
  const headers = {};
  const ob = settings.ollabridge;
  if (ob.auth_mode === 'apikey' && ob.api_key) {
    headers['Authorization'] = `Bearer ${ob.api_key}`;
  } else if (ob.auth_mode === 'pairing' && ob.pair_token) {
    headers['Authorization'] = `Bearer ${ob.pair_token}`;
  }
  headers['X-Client-Type'] = 'aws-exam-simulator';
  return headers;
}

export async function checkOllaBridgeHealth(settings) {
  const ob = settings?.ollabridge || DEFAULT_SETTINGS.ollabridge;
  const baseUrl = ob.base_url.replace(/\/$/, '');
  try {
    const resp = await proxiedFetch(`${baseUrl}/v1/models`, {
      method: 'GET',
      headers: getAuthHeaders(settings || DEFAULT_SETTINGS),
    });
    if (!resp.ok) return { available: false, models: [], error: `HTTP ${resp.status}` };
    const data = await resp.json();
    const models = (data.data || data.models || []).map(m => m.id || m.name || m);
    return { available: true, models };
  } catch (err) {
    return { available: false, models: [], error: err.message };
  }
}

export async function chatCompletion(messages, settings, options = {}) {
  const ob = settings?.ollabridge || DEFAULT_SETTINGS.ollabridge;
  const baseUrl = ob.base_url.replace(/\/$/, '');
  const model = options.model || ob.model;

  const resp = await proxiedFetch(`${baseUrl}/v1/chat/completions`, {
    method: 'POST',
    headers: getAuthHeaders(settings || DEFAULT_SETTINGS),
    body: {
      model,
      messages,
      max_tokens: options.max_tokens || 2048,
      temperature: options.temperature ?? 0.7,
    },
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`OllaBridge error ${resp.status}: ${text}`);
  }

  const data = await resp.json();
  const content = data.choices?.[0]?.message?.content
    || data.response
    || data.text
    || '';
  return content.trim();
}

export async function pairWithOllaBridge(code, settings) {
  const ob = settings?.ollabridge || DEFAULT_SETTINGS.ollabridge;
  const baseUrl = ob.base_url.replace(/\/$/, '');
  const normalizedCode = code.trim().toUpperCase().replace(/[-\s]/g, '');

  const resp = await proxiedFetch(`${baseUrl}/pair`, {
    method: 'POST',
    body: { code: normalizedCode, label: 'aws-exam-simulator' },
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    throw new Error(`Pairing failed: ${text}`);
  }

  const data = await resp.json();
  if (!data.ok && !data.token) {
    throw new Error(data.error || 'Pairing failed');
  }

  return {
    token: data.token,
    device_id: data.device_id || '',
  };
}

// ---------------------------------------------------------------------------
// AI Tutor prompts (used when running without the Python backend)
// ---------------------------------------------------------------------------

const EVALUATE_SYSTEM = `You are an expert certification exam tutor. Your job is to evaluate answers and teach.

When the student is CORRECT:
- Confirm they're right with brief encouragement
- Explain WHY this is the correct answer (reinforce the concept)
- Mention 1-2 related concepts they should also understand

When the student is INCORRECT or said "I don't know":
- Do NOT be harsh - be encouraging but clear
- Explain the misconception in their choice
- Deep dive into AT LEAST 3 related sub-topics:
  - The core concept behind the correct answer
  - Why the wrong options are wrong (common traps)
  - A real-world analogy or example
- End with a "Key Takeaway" summary

Format with markdown: use **bold**, bullet lists, and headers.
Keep it focused and exam-relevant. Goal is mastery, not memorization.`;

const MICRO_CHECK_SYSTEM = `You are an expert exam tutor. Generate exactly ONE short verification question to check if the student understood the concept just taught.

Rules:
- The question must be different from the original exam question
- It should test the SAME underlying concept
- Provide exactly 2 options: one correct, one plausible but wrong
- Return ONLY valid JSON in this exact format, nothing else:

{"question": "your question here", "options": ["correct answer", "wrong answer"], "correct_index": 0, "explanation": "brief explanation"}

Do not include any text outside the JSON object.`;

const CHAT_SYSTEM = `You are an expert certification exam tutor helping a student master cloud computing concepts. Be concise but thorough. Use real-world examples. When the student demonstrates understanding, acknowledge it and move on. If they're confused, try a different explanation. Use markdown formatting.`;

export async function generateFeedback(question, userAnswer, isCorrect, idk, settings) {
  const optionsStr = question.options
    .map((opt, i) => `  ${String.fromCharCode(65 + i)}. ${opt}`)
    .join('\n');

  const correctAnswer = question.options?.[question.correct_indices?.[0]] || '';

  let userPrompt = `Question: ${question.text}\n\nOptions:\n${optionsStr}\n\nCorrect Answer: ${correctAnswer}\nStudent's Answer: ${userAnswer}\nStudent was: ${isCorrect ? 'CORRECT' : idk ? "said 'I don't know'" : 'INCORRECT'}`;

  if (question.explanation) {
    userPrompt += `\nOfficial Explanation: ${question.explanation}`;
  }

  if (isCorrect) {
    userPrompt += '\nThe student answered correctly. Briefly confirm, explain WHY this is correct, and mention 1-2 related concepts.';
  } else if (idk) {
    userPrompt += "\nThe student said 'I don't know'. Be encouraging. Teach the concept from scratch with 3+ sub-topics.";
  } else {
    userPrompt += '\nThe student answered incorrectly. Explain the misconception, then deep-dive into at least 3 sub-topics.';
  }

  const messages = [
    { role: 'system', content: EVALUATE_SYSTEM },
    { role: 'user', content: userPrompt },
  ];

  return chatCompletion(messages, settings);
}

export async function generateMicroCheck(question, settings) {
  const correctAnswer = question.options?.[question.correct_indices?.[0]] || '';
  const tags = question.tags?.join(', ') || 'general';

  const userPrompt = `Based on this exam question and its correct answer, generate a SHORT verification question.\n\nOriginal question: ${question.text}\nCorrect answer: ${correctAnswer}\nTopic tags: ${tags}\n\nGenerate a simple true/false or 2-option question that tests if the student understood the core concept.\nReturn ONLY valid JSON: {"question": "...", "options": ["correct", "wrong"], "correct_index": 0, "explanation": "..."}`;

  const messages = [
    { role: 'system', content: MICRO_CHECK_SYSTEM },
    { role: 'user', content: userPrompt },
  ];

  const response = await chatCompletion(messages, settings, { temperature: 0.3 });

  try {
    const jsonMatch = response.match(/\{[^{}]*"question"[^{}]*\}/s);
    if (jsonMatch) {
      const mc = JSON.parse(jsonMatch[0]);
      if (mc.question && mc.options?.length >= 2) {
        return {
          question: mc.question,
          options: mc.options.slice(0, 2),
          correct_index: mc.correct_index ?? 0,
          explanation: mc.explanation || '',
        };
      }
    }
  } catch { /* fallback below */ }

  return null;
}

export async function chatWithOllaBridge(message, questionContext, history, examTitle, settings) {
  const messages = [
    { role: 'system', content: `${CHAT_SYSTEM}\n\nTutoring for: ${examTitle || 'Cloud Certification'}` },
  ];

  if (questionContext) {
    messages.push({ role: 'user', content: `Current question context:\n${questionContext}` });
    messages.push({ role: 'assistant', content: 'I understand the context. How can I help you with this question?' });
  }

  for (const entry of (history || []).slice(-6)) {
    messages.push({ role: entry.role, content: entry.content });
  }

  messages.push({ role: 'user', content: message });

  return chatCompletion(messages, settings);
}
