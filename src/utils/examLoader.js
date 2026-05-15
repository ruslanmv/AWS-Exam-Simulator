/**
 * Utility functions for loading and transforming exam data from JSON files.
 *
 * Supports two data sources:
 *  - Built-in JSON files under /questions/{examId}.json (loaded via Vite dynamic import).
 *  - User-imported JSON files (parsed in the browser, see buildExamFromQuestions).
 */

// List of available exams in the questions directory.
//
// `realExamQuestions` is the question count of the actual certification
// exam (the "snapshot" size). In Timed Exam Mode the simulator picks
// `realExamQuestions` questions at random from the full question bank so
// each attempt feels like the real thing. Training mode always uses the
// full bank so students can review every question.
const AVAILABLE_EXAMS = [
  { id: 'SAA-C03-v1', name: 'AWS Solutions Architect Associate (SAA-C03) v1', provider: 'AWS', description: 'Practice exam for AWS Solutions Architect Associate certification', timeLimit: 130, realExamQuestions: 65, bankSize: 382 },
  { id: 'SAA-C03-v2', name: 'AWS Solutions Architect Associate (SAA-C03) v2', provider: 'AWS', description: 'Alternative practice exam for SAA-C03 certification', timeLimit: 130, realExamQuestions: 65, bankSize: 666 },
  { id: 'SAP-C02-v1', name: 'AWS Solutions Architect Professional (SAP-C02)', provider: 'AWS', description: 'Practice exam for AWS Solutions Architect Professional certification', timeLimit: 180, realExamQuestions: 75, bankSize: 458 },
  { id: 'CLF-C02-v1', name: 'AWS Cloud Practitioner (CLF-C02)', provider: 'AWS', description: 'Practice exam for AWS Cloud Practitioner certification', timeLimit: 90, realExamQuestions: 65, bankSize: 542 },
  { id: 'DOP-C02-v1', name: 'AWS DevOps Engineer Professional (DOP-C02)', provider: 'AWS', description: 'Practice exam for AWS DevOps Engineer Professional certification', timeLimit: 180, realExamQuestions: 75, bankSize: 136 },
  { id: 'MLS-C01', name: 'AWS Machine Learning Specialty (MLS-C01)', provider: 'AWS', description: 'Practice exam for AWS Machine Learning Specialty certification', timeLimit: 170, realExamQuestions: 65, bankSize: 264 },
  { id: 'MLS-C01-v1', name: 'AWS Machine Learning Specialty (MLS-C01) v1', provider: 'AWS', description: 'Practice exam version 1 for MLS-C01', timeLimit: 170, realExamQuestions: 65, bankSize: 195 },
  { id: 'MLS-C01-v2', name: 'AWS Machine Learning Specialty (MLS-C01) v2', provider: 'AWS', description: 'Practice exam version 2 for MLS-C01', timeLimit: 170, realExamQuestions: 65, bankSize: 176 },
  { id: 'MLS-C01-v3', name: 'AWS Machine Learning Specialty (MLS-C01) v3', provider: 'AWS', description: 'Practice exam version 3 for MLS-C01', timeLimit: 170, realExamQuestions: 65, bankSize: 107 },
  { id: 'MLS-C01-v4', name: 'AWS Machine Learning Specialty (MLS-C01) v4', provider: 'AWS', description: 'Practice exam version 4 for MLS-C01', timeLimit: 170, realExamQuestions: 65, bankSize: 264 },
  { id: 'MLS-C01-v0624', name: 'AWS Machine Learning Specialty (MLS-C01) June 2024', provider: 'AWS', description: 'Updated practice exam for MLS-C01 (June 2024)', timeLimit: 170, realExamQuestions: 65, bankSize: 264 },
  { id: 'AI-900-v1', name: 'Microsoft Azure AI Fundamentals (AI-900) v1', provider: 'Azure', description: 'Practice exam for Azure AI Fundamentals certification', timeLimit: 60, realExamQuestions: 40, bankSize: 226 },
  { id: 'AI-900-v2', name: 'Microsoft Azure AI Fundamentals (AI-900) v2', provider: 'Azure', description: 'Alternative practice exam for AI-900', timeLimit: 60, realExamQuestions: 40, bankSize: 372 },
  { id: 'AI-900-v3', name: 'Microsoft Azure AI Fundamentals (AI-900) v3', provider: 'Azure', description: 'Third version of AI-900 practice exam', timeLimit: 60, realExamQuestions: 40, bankSize: 154 },
  { id: 'AI-102', name: 'Microsoft Azure AI Engineer Associate (AI-102)', provider: 'Azure', description: 'Practice exam for Azure AI Engineer Associate certification', timeLimit: 120, realExamQuestions: 50, bankSize: 198 },
  { id: 'DP-100-v1', name: 'Microsoft Azure Data Scientist Associate (DP-100)', provider: 'Azure', description: 'Practice exam for Azure Data Scientist Associate certification', timeLimit: 120, realExamQuestions: 50, bankSize: 270 },
  { id: 'GCP-ML-vA', name: 'Google Cloud Professional ML Engineer Version A', provider: 'GCP', description: 'Practice exam for Google Cloud Professional Machine Learning Engineer', timeLimit: 120, realExamQuestions: 50, bankSize: 75 },
  { id: 'GCP-ML-vB', name: 'Google Cloud Professional ML Engineer Version B', provider: 'GCP', description: 'Alternative practice exam for GCP ML Engineer', timeLimit: 120, realExamQuestions: 50, bankSize: 171 },
  { id: 'GCP-CA', name: 'Google Cloud Associate Cloud Engineer', provider: 'GCP', description: 'Practice exam for Google Cloud Associate Cloud Engineer certification', timeLimit: 120, realExamQuestions: 50, bankSize: 179 },
  { id: 'C1000-185-v1', name: 'IBM watsonx Generative AI Engineer - Associate (C1000-185) v1', provider: 'IBM', description: 'Practice exam for IBM watsonx Generative AI Engineer - Associate', timeLimit: 120, realExamQuestions: 62, bankSize: 190 },
];

/**
 * Transform a raw question (any of the supported source shapes) into the
 * application's internal question format.
 *
 * Supported source shapes for the correct answer:
 *   correct: "A. option"
 *   correct: "A. option | C. option"
 *   correct_answers: ["A. option", "C. option"]
 *   correct_labels: ["A", "C"]
 *
 * @param {Object} question - Question in JSON format
 * @param {number} index - Question index
 * @returns {Object} Question in app format
 */
function transformQuestion(question, index) {
  const correctAnswers = Array.isArray(question.correct_answers)
    ? question.correct_answers.map((x) => String(x).trim())
    : String(question.correct || '')
        .split('|')
        .map((x) => x.trim())
        .filter(Boolean);

  const correctLabels = Array.isArray(question.correct_labels)
    ? question.correct_labels.map((x) => String(x).trim().toUpperCase())
    : [];

  const options = (question.options || []).map((optionText, optionIndex) => {
    const optionId = String.fromCharCode(97 + optionIndex); // 'a', 'b', 'c', ...
    const optionLabel = String.fromCharCode(65 + optionIndex); // 'A', 'B', 'C', ...
    const normalizedOption = String(optionText).trim();

    const isCorrect =
      correctAnswers.includes(normalizedOption) ||
      correctLabels.includes(optionLabel) ||
      String(question.correct || '').trim() === normalizedOption;

    return {
      id: optionId,
      text: optionText,
      correct: isCorrect,
    };
  });

  return {
    id: index + 1,
    text: question.question,
    type: options.filter((option) => option.correct).length > 1 ? 'multiple-select' : 'multiple-choice',
    options,
    explanation: question.explanation || '',
    references: question.references || '',
  };
}

/**
 * Return a new exam object containing a random N-question snapshot of the
 * source exam — modelling a real attempt of the certification exam.
 *
 * Picks `count` questions uniformly at random without replacement using a
 * Fisher–Yates shuffle, and renumbers their `id`s 1..N so the sidebar /
 * progress UI stays sequential. Falls back to the original exam if it
 * already has <= `count` questions.
 *
 * @param {Object} exam - Exam returned by buildExamFromQuestions / loadExamFromJSON
 * @param {number} count - Snapshot size (typically realExamQuestions)
 * @returns {Object} A new exam object with sampled questions
 */
export function sampleExamSnapshot(exam, count) {
  if (!exam || !Array.isArray(exam.questions)) return exam;
  if (!count || count <= 0 || exam.questions.length <= count) return exam;

  const pool = exam.questions.slice();
  for (let i = pool.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j], pool[i]];
  }
  const sampled = pool.slice(0, count).map((q, idx) => ({ ...q, id: idx + 1 }));

  return {
    ...exam,
    questions: sampled,
    totalQuestions: sampled.length,
    bankSize: exam.bankSize ?? exam.questions.length,
    isSnapshot: true,
  };
}

/**
 * Build an exam object from a raw JSON payload (in-memory).
 *
 * Accepts either:
 *   - A plain array of questions (the historical /questions/*.json shape), or
 *   - An object: { meta?: {...}, questions: [...] } where `meta` may include
 *     id, name, title, provider, description, timeLimit.
 *
 * @param {Array|Object} rawData
 * @param {Object} [overrides] - Optional metadata overrides (id, name, timeLimit, ...)
 * @returns {Object} Exam in the app format
 */
export function buildExamFromQuestions(rawData, overrides = {}) {
  let questions;
  let meta = {};

  if (Array.isArray(rawData)) {
    questions = rawData;
  } else if (rawData && Array.isArray(rawData.questions)) {
    questions = rawData.questions;
    meta = rawData.meta || rawData.metadata || {};
  } else {
    throw new Error(
      'Invalid exam JSON: expected an array of questions, or an object { meta, questions: [...] }.'
    );
  }

  if (!questions.length) {
    throw new Error('Invalid exam JSON: question list is empty.');
  }

  const transformed = questions.map((q, i) => transformQuestion(q, i));

  return {
    id: overrides.id || meta.id || 'custom-imported',
    title: overrides.name || overrides.title || meta.name || meta.title || 'Imported Custom Exam',
    totalQuestions: transformed.length,
    bankSize: transformed.length,
    realExamQuestions: overrides.realExamQuestions || meta.realExamQuestions || null,
    timeLimit: overrides.timeLimit || meta.timeLimit || 120,
    questions: transformed,
  };
}

/**
 * Load and transform exam data from a built-in JSON file.
 *
 * @param {string} examId - The exam ID (e.g., 'SAA-C03-v1', 'C1000-185-v1')
 * @returns {Promise<Object>} Transformed exam data
 */
export async function loadExamFromJSON(examId) {
  try {
    // Import the JSON file dynamically
    const jsonData = await import(`../../questions/${examId}.json`);
    const questions = jsonData.default;

    // Find exam metadata
    const examMetadata = AVAILABLE_EXAMS.find((exam) => exam.id === examId);

    if (!examMetadata) {
      throw new Error(`Exam metadata not found for ${examId}`);
    }

    return buildExamFromQuestions(questions, {
      id: examId,
      name: examMetadata.name,
      timeLimit: examMetadata.timeLimit,
      realExamQuestions: examMetadata.realExamQuestions,
    });
  } catch (error) {
    console.error(`Error loading exam ${examId}:`, error);
    throw error;
  }
}

/**
 * Get list of all available exams
 * @returns {Promise<Array>} List of available exams
 */
export async function getAvailableExams() {
  return AVAILABLE_EXAMS.map((exam) => ({ ...exam }));
}

/**
 * Get exam metadata by ID
 * @param {string} examId - The exam ID
 * @returns {Object|null} Exam metadata or null if not found
 */
export function getExamMetadata(examId) {
  return AVAILABLE_EXAMS.find((exam) => exam.id === examId) || null;
}

export { AVAILABLE_EXAMS };
