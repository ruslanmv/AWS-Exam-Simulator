import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/admin';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// EXAM API FUNCTIONS
// ============================================================================

/**
 * Get exam data by exam ID or type
 * @param {string} examId - The exam ID or type (e.g., 'SAA-C03', 'DVA-C02')
 * @returns {Promise} Exam data including questions
 */
export const getExamData = async (examId) => {
  try {
    const response = await api.get(`/exams/${examId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching exam data:', error);
    throw error;
  }
};

/**
 * Get list of available exams
 * @returns {Promise} List of available exams
 */
export const getExamList = async () => {
  try {
    const response = await api.get('/exams');
    return response.data;
  } catch (error) {
    console.error('Error fetching exam list:', error);
    throw error;
  }
};

/**
 * Submit exam results
 * @param {Object} examResults - The exam results data
 * @param {string} examResults.examId - The exam ID
 * @param {Object} examResults.answers - User answers {questionId: selectedOption}
 * @param {number} examResults.timeSpent - Time spent in seconds
 * @param {Array} examResults.flaggedQuestions - Array of flagged question IDs
 * @returns {Promise} Submission result including score
 */
export const submitResults = async (examResults) => {
  try {
    const response = await api.post('/exams/submit', {
      examId: examResults.examId,
      answers: examResults.answers,
      timeSpent: examResults.timeSpent,
      flaggedQuestions: examResults.flaggedQuestions,
      startTime: examResults.startTime,
      endTime: examResults.endTime,
    });
    return response.data;
  } catch (error) {
    console.error('Error submitting exam results:', error);
    throw error;
  }
};

/**
 * Get user's exam history
 * @returns {Promise} User's exam history
 */
export const getExamHistory = async () => {
  try {
    const response = await api.get('/exams/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching exam history:', error);
    throw error;
  }
};

/**
 * Get detailed results for a specific exam attempt
 * @param {string} attemptId - The attempt ID
 * @returns {Promise} Detailed exam results
 */
export const getExamResults = async (attemptId) => {
  try {
    const response = await api.get(`/exams/results/${attemptId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching exam results:', error);
    throw error;
  }
};

// ============================================================================
// ADMIN API FUNCTIONS
// ============================================================================

/**
 * Admin login
 * @param {Object} credentials - Login credentials
 * @param {string} credentials.username - Admin username
 * @param {string} credentials.password - Admin password
 * @returns {Promise} Authentication response with token
 */
export const adminLogin = async (credentials) => {
  try {
    const response = await api.post('/admin/login', {
      username: credentials.username,
      password: credentials.password,
    });

    // Store token and user info
    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }

    return response.data;
  } catch (error) {
    console.error('Error during admin login:', error);
    throw error;
  }
};

/**
 * Admin logout
 * @returns {Promise} Logout response
 */
export const adminLogout = async () => {
  try {
    await api.post('/admin/logout');
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  } catch (error) {
    console.error('Error during logout:', error);
    // Clear local storage even if API call fails
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
    throw error;
  }
};

/**
 * Get admin logs - all exam attempts and results
 * @param {Object} filters - Optional filters
 * @param {number} filters.page - Page number
 * @param {number} filters.limit - Results per page
 * @param {string} filters.examType - Filter by exam type
 * @param {string} filters.status - Filter by status (passed/failed)
 * @param {string} filters.startDate - Filter by start date
 * @param {string} filters.endDate - Filter by end date
 * @returns {Promise} Admin logs data
 */
export const getAdminLogs = async (filters = {}) => {
  try {
    const params = new URLSearchParams();

    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.examType) params.append('examType', filters.examType);
    if (filters.status) params.append('status', filters.status);
    if (filters.startDate) params.append('startDate', filters.startDate);
    if (filters.endDate) params.append('endDate', filters.endDate);

    const response = await api.get(`/admin/logs?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching admin logs:', error);
    throw error;
  }
};

/**
 * Get admin dashboard statistics
 * @returns {Promise} Dashboard statistics
 */
export const getAdminStats = async () => {
  try {
    const response = await api.get('/admin/stats');
    return response.data;
  } catch (error) {
    console.error('Error fetching admin stats:', error);
    throw error;
  }
};

/**
 * Get detailed information about a specific exam attempt
 * @param {string} attemptId - The attempt ID
 * @returns {Promise} Detailed attempt information
 */
export const getAttemptDetails = async (attemptId) => {
  try {
    const response = await api.get(`/admin/attempts/${attemptId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching attempt details:', error);
    throw error;
  }
};

// ============================================================================
// USER API FUNCTIONS
// ============================================================================

/**
 * User registration
 * @param {Object} userData - User registration data
 * @returns {Promise} Registration response
 */
export const registerUser = async (userData) => {
  try {
    const response = await api.post('/users/register', userData);
    return response.data;
  } catch (error) {
    console.error('Error during user registration:', error);
    throw error;
  }
};

/**
 * User login
 * @param {Object} credentials - Login credentials
 * @returns {Promise} Authentication response
 */
export const userLogin = async (credentials) => {
  try {
    const response = await api.post('/users/login', credentials);

    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }

    return response.data;
  } catch (error) {
    console.error('Error during user login:', error);
    throw error;
  }
};

/**
 * Get current user profile
 * @returns {Promise} User profile data
 */
export const getUserProfile = async () => {
  try {
    const response = await api.get('/users/profile');
    return response.data;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};

/**
 * Update user profile
 * @param {Object} profileData - Profile data to update
 * @returns {Promise} Updated profile data
 */
export const updateUserProfile = async (profileData) => {
  try {
    const response = await api.put('/users/profile', profileData);
    return response.data;
  } catch (error) {
    console.error('Error updating user profile:', error);
    throw error;
  }
};

// Export the axios instance for custom requests
export default api;
