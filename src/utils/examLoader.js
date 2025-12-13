/**
 * Utility functions for loading and transforming exam data from JSON files
 */

// List of available exams in the questions directory
const AVAILABLE_EXAMS = [
  { id: 'SAA-C03-v1', name: 'AWS Solutions Architect Associate (SAA-C03) v1', provider: 'AWS', description: 'Practice exam for AWS Solutions Architect Associate certification', timeLimit: 130, totalQuestions: null },
  { id: 'SAA-C03-v2', name: 'AWS Solutions Architect Associate (SAA-C03) v2', provider: 'AWS', description: 'Alternative practice exam for SAA-C03 certification', timeLimit: 130, totalQuestions: null },
  { id: 'SAP-C02-v1', name: 'AWS Solutions Architect Professional (SAP-C02)', provider: 'AWS', description: 'Practice exam for AWS Solutions Architect Professional certification', timeLimit: 180, totalQuestions: null },
  { id: 'CLF-C02-v1', name: 'AWS Cloud Practitioner (CLF-C02)', provider: 'AWS', description: 'Practice exam for AWS Cloud Practitioner certification', timeLimit: 90, totalQuestions: null },
  { id: 'DOP-C02-v1', name: 'AWS DevOps Engineer Professional (DOP-C02)', provider: 'AWS', description: 'Practice exam for AWS DevOps Engineer Professional certification', timeLimit: 180, totalQuestions: null },
  { id: 'MLS-C01', name: 'AWS Machine Learning Specialty (MLS-C01)', provider: 'AWS', description: 'Practice exam for AWS Machine Learning Specialty certification', timeLimit: 170, totalQuestions: null },
  { id: 'MLS-C01-v1', name: 'AWS Machine Learning Specialty (MLS-C01) v1', provider: 'AWS', description: 'Practice exam version 1 for MLS-C01', timeLimit: 170, totalQuestions: null },
  { id: 'MLS-C01-v2', name: 'AWS Machine Learning Specialty (MLS-C01) v2', provider: 'AWS', description: 'Practice exam version 2 for MLS-C01', timeLimit: 170, totalQuestions: null },
  { id: 'MLS-C01-v3', name: 'AWS Machine Learning Specialty (MLS-C01) v3', provider: 'AWS', description: 'Practice exam version 3 for MLS-C01', timeLimit: 170, totalQuestions: null },
  { id: 'MLS-C01-v4', name: 'AWS Machine Learning Specialty (MLS-C01) v4', provider: 'AWS', description: 'Practice exam version 4 for MLS-C01', timeLimit: 170, totalQuestions: null },
  { id: 'MLS-C01-v0624', name: 'AWS Machine Learning Specialty (MLS-C01) June 2024', provider: 'AWS', description: 'Updated practice exam for MLS-C01 (June 2024)', timeLimit: 170, totalQuestions: null },
  { id: 'AI-900-v1', name: 'Microsoft Azure AI Fundamentals (AI-900) v1', provider: 'Azure', description: 'Practice exam for Azure AI Fundamentals certification', timeLimit: 60, totalQuestions: null },
  { id: 'AI-900-v2', name: 'Microsoft Azure AI Fundamentals (AI-900) v2', provider: 'Azure', description: 'Alternative practice exam for AI-900', timeLimit: 60, totalQuestions: null },
  { id: 'AI-900-v3', name: 'Microsoft Azure AI Fundamentals (AI-900) v3', provider: 'Azure', description: 'Third version of AI-900 practice exam', timeLimit: 60, totalQuestions: null },
  { id: 'AI-102', name: 'Microsoft Azure AI Engineer Associate (AI-102)', provider: 'Azure', description: 'Practice exam for Azure AI Engineer Associate certification', timeLimit: 120, totalQuestions: null },
  { id: 'DP-100-v1', name: 'Microsoft Azure Data Scientist Associate (DP-100)', provider: 'Azure', description: 'Practice exam for Azure Data Scientist Associate certification', timeLimit: 120, totalQuestions: null },
  { id: 'GCP-ML-vA', name: 'Google Cloud Professional ML Engineer Version A', provider: 'GCP', description: 'Practice exam for Google Cloud Professional Machine Learning Engineer', timeLimit: 120, totalQuestions: null },
  { id: 'GCP-ML-vB', name: 'Google Cloud Professional ML Engineer Version B', provider: 'GCP', description: 'Alternative practice exam for GCP ML Engineer', timeLimit: 120, totalQuestions: null },
  { id: 'GCP-CA', name: 'Google Cloud Associate Cloud Engineer', provider: 'GCP', description: 'Practice exam for Google Cloud Associate Cloud Engineer certification', timeLimit: 120, totalQuestions: null },
];

/**
 * Transform a question from the JSON format to the app format
 * @param {Object} question - Question in JSON format
 * @param {number} index - Question index
 * @returns {Object} Question in app format
 */
function transformQuestion(question, index) {
  // Parse options to find which one is correct
  const options = question.options.map((optionText, optionIndex) => {
    const optionId = String.fromCharCode(97 + optionIndex); // 'a', 'b', 'c', 'd', etc.
    const isCorrect = question.correct.trim() === optionText.trim();

    return {
      id: optionId,
      text: optionText,
      correct: isCorrect,
    };
  });

  return {
    id: index + 1,
    text: question.question,
    type: 'multiple-choice',
    options: options,
    explanation: question.explanation || '',
    references: question.references || '',
  };
}

/**
 * Load and transform exam data from JSON file
 * @param {string} examId - The exam ID (e.g., 'SAA-C03-v1')
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

    // Transform questions
    const transformedQuestions = questions.map((q, index) => transformQuestion(q, index));

    // Return in the format expected by the app
    return {
      id: examId,
      title: examMetadata.name,
      totalQuestions: transformedQuestions.length,
      timeLimit: examMetadata.timeLimit,
      questions: transformedQuestions,
    };
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
  // Return the list with actual question counts if needed
  // For now, we'll return the static list
  return AVAILABLE_EXAMS.map(exam => ({
    ...exam,
    // You can add actual question counts here if you want to load them
  }));
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
