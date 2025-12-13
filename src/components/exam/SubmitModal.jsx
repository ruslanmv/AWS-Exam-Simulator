import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useExam } from '../../context/ExamContext';
import { submitResults } from '../../services/api';

const SubmitModal = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const {
    examData,
    answers,
    flaggedQuestions,
    examStartTime,
    endExam,
    getExamStats,
    timeRemaining,
    timeSpentPerQuestion,
  } = useExam();

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const stats = getExamStats();

  const calculateTimeUsed = () => {
    if (!examData || timeRemaining === null) return '00:00';

    const totalSeconds = examData.timeLimit * 60;
    const timeUsed = totalSeconds - timeRemaining;
    const hours = Math.floor(timeUsed / 3600);
    const minutes = Math.floor((timeUsed % 3600) / 60);

    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async () => {
    try {
      setIsSubmitting(true);
      setError(null);

      const examEndTime = new Date();
      const totalTimeSpent = examData.timeLimit * 60 - timeRemaining;

      const examResults = {
        examId: examData.id || examData.title,
        answers,
        timeSpent: totalTimeSpent,
        flaggedQuestions: Array.from(flaggedQuestions),
        startTime: examStartTime,
        endTime: examEndTime,
        timeSpentPerQuestion,
      };

      // Submit to backend
      const response = await submitResults(examResults);

      // End the exam in context
      endExam();

      // Navigate to results page with the response data
      navigate('/results', { state: { results: response } });
    } catch (err) {
      console.error('Error submitting exam:', err);
      setError(err.response?.data?.message || 'Failed to submit exam. Please try again.');
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-800">Submit Exam</h3>
          <button onClick={onClose} disabled={isSubmitting} className="text-gray-500 hover:text-gray-700">
            <i className="fas fa-times"></i>
          </button>
        </div>

        <div className="mb-6">
          {stats?.unansweredCount > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <div className="flex items-center">
                <i className="fas fa-exclamation-triangle text-yellow-500 mr-3"></i>
                <p className="text-yellow-800">
                  You have <span className="font-bold">{stats.unansweredCount}</span> unanswered
                  questions. Are you sure you want to submit?
                </p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <div className="flex items-center">
                <i className="fas fa-exclamation-circle text-red-500 mr-3"></i>
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Total Questions:</span>
              <span className="font-medium">{stats?.totalQuestions || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Answered:</span>
              <span className="font-medium text-exam-green">{stats?.answeredCount || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Flagged:</span>
              <span className="font-medium text-exam-yellow">{stats?.flaggedCount || 0}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-700">Time Used:</span>
              <span className="font-medium">{calculateTimeUsed()}</span>
            </div>
          </div>
        </div>

        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            disabled={isSubmitting}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting}
            className="px-4 py-2 bg-exam-red text-white rounded-lg hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <i className="fas fa-spinner fa-spin mr-2"></i>
                Submitting...
              </>
            ) : (
              <>
                <i className="fas fa-paper-plane mr-2"></i>
                Submit Exam
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubmitModal;
