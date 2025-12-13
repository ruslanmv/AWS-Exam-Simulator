import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const ExamContext = createContext(null);

export const useExam = () => {
  const context = useContext(ExamContext);
  if (!context) {
    throw new Error('useExam must be used within an ExamProvider');
  }
  return context;
};

export const ExamProvider = ({ children }) => {
  const [examData, setExamData] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [flaggedQuestions, setFlaggedQuestions] = useState(new Set());
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [examStartTime, setExamStartTime] = useState(null);
  const [examEndTime, setExamEndTime] = useState(null);
  const [isExamActive, setIsExamActive] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [timeSpentPerQuestion, setTimeSpentPerQuestion] = useState({});
  const [lastQuestionChangeTime, setLastQuestionChangeTime] = useState(null);
  const [examMode, setExamMode] = useState('exam'); // 'exam' or 'training'
  const [showFeedback, setShowFeedback] = useState({}); // Track which questions show feedback in training mode

  // Initialize exam
  const initializeExam = (data, mode = 'exam') => {
    setExamData(data);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setFlaggedQuestions(new Set());
    setExamMode(mode);
    setShowFeedback({});

    // Only set timer for exam mode
    if (mode === 'exam') {
      setTimeRemaining(data.timeLimit * 60); // Convert minutes to seconds
      setExamStartTime(new Date());
      setLastQuestionChangeTime(new Date());
      setIsExamActive(true);
    } else {
      // Training mode: no timer
      setTimeRemaining(null);
      setExamStartTime(null);
      setLastQuestionChangeTime(null);
      setIsExamActive(false);
    }

    setExamEndTime(null);
    setIsPaused(false);
    setTimeSpentPerQuestion({});
  };

  // Timer effect
  useEffect(() => {
    if (!isExamActive || isPaused || timeRemaining === null || timeRemaining <= 0) {
      return;
    }

    const timer = setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          setIsExamActive(false);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [isExamActive, isPaused, timeRemaining]);

  // Track time spent on current question
  const trackQuestionTime = useCallback(() => {
    if (!lastQuestionChangeTime || !isExamActive || isPaused) return;

    const now = new Date();
    const timeSpent = (now - lastQuestionChangeTime) / 1000; // Convert to seconds

    setTimeSpentPerQuestion((prev) => ({
      ...prev,
      [currentQuestionIndex]: (prev[currentQuestionIndex] || 0) + timeSpent,
    }));

    setLastQuestionChangeTime(now);
  }, [currentQuestionIndex, lastQuestionChangeTime, isExamActive, isPaused]);

  // Navigate to a specific question
  const navigateToQuestion = (index) => {
    if (index < 0 || !examData || index >= examData.questions.length) return;

    trackQuestionTime();
    setCurrentQuestionIndex(index);
    setLastQuestionChangeTime(new Date());
  };

  // Navigate to next question
  const nextQuestion = () => {
    if (!examData || currentQuestionIndex >= examData.questions.length - 1) return;
    navigateToQuestion(currentQuestionIndex + 1);
  };

  // Navigate to previous question
  const previousQuestion = () => {
    if (currentQuestionIndex <= 0) return;
    navigateToQuestion(currentQuestionIndex - 1);
  };

  // Select an answer for current question
  const selectAnswer = (questionId, optionId) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));

    // In training mode, show feedback immediately
    if (examMode === 'training') {
      setShowFeedback((prev) => ({
        ...prev,
        [questionId]: true,
      }));
    }
  };

  // Clear answer for current question
  const clearAnswer = (questionId) => {
    setAnswers((prev) => {
      const newAnswers = { ...prev };
      delete newAnswers[questionId];
      return newAnswers;
    });
  };

  // Toggle flag for a question
  const toggleFlag = (questionId) => {
    setFlaggedQuestions((prev) => {
      const newFlags = new Set(prev);
      if (newFlags.has(questionId)) {
        newFlags.delete(questionId);
      } else {
        newFlags.add(questionId);
      }
      return newFlags;
    });
  };

  // Pause/Resume exam
  const togglePause = () => {
    if (!isPaused) {
      trackQuestionTime();
    } else {
      setLastQuestionChangeTime(new Date());
    }
    setIsPaused(!isPaused);
  };

  // End exam
  const endExam = () => {
    trackQuestionTime();
    setExamEndTime(new Date());
    setIsExamActive(false);
  };

  // Reset exam
  const resetExam = () => {
    setExamData(null);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setFlaggedQuestions(new Set());
    setTimeRemaining(null);
    setExamStartTime(null);
    setExamEndTime(null);
    setIsExamActive(false);
    setIsPaused(false);
    setTimeSpentPerQuestion({});
    setLastQuestionChangeTime(null);
    setExamMode('exam');
    setShowFeedback({});
  };

  // Get exam statistics
  const getExamStats = () => {
    if (!examData) return null;

    const totalQuestions = examData.questions.length;
    const answeredCount = Object.keys(answers).length;
    const unansweredCount = totalQuestions - answeredCount;
    const flaggedCount = flaggedQuestions.size;
    const progressPercentage = Math.round((answeredCount / totalQuestions) * 100);

    return {
      totalQuestions,
      answeredCount,
      unansweredCount,
      flaggedCount,
      progressPercentage,
    };
  };

  // Format time for display
  const formatTime = (seconds) => {
    if (seconds === null) return '00:00:00';

    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Get current question
  const getCurrentQuestion = () => {
    if (!examData || !examData.questions) return null;
    return examData.questions[currentQuestionIndex];
  };

  // Check if question is answered
  const isQuestionAnswered = (questionId) => {
    return answers.hasOwnProperty(questionId);
  };

  // Check if question is flagged
  const isQuestionFlagged = (questionId) => {
    return flaggedQuestions.has(questionId);
  };

  const value = {
    examData,
    currentQuestionIndex,
    answers,
    flaggedQuestions,
    timeRemaining,
    examStartTime,
    examEndTime,
    isExamActive,
    isPaused,
    timeSpentPerQuestion,
    examMode,
    showFeedback,
    initializeExam,
    navigateToQuestion,
    nextQuestion,
    previousQuestion,
    selectAnswer,
    clearAnswer,
    toggleFlag,
    togglePause,
    endExam,
    resetExam,
    getExamStats,
    formatTime,
    getCurrentQuestion,
    isQuestionAnswered,
    isQuestionFlagged,
  };

  return <ExamContext.Provider value={value}>{children}</ExamContext.Provider>;
};
