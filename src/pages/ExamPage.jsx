import { useEffect, useState } from 'react';
import { useExam } from '../context/ExamContext';
import { getExamData } from '../services/api';
import Header from '../components/exam/Header';
import Sidebar from '../components/exam/Sidebar';
import QuestionCard from '../components/exam/QuestionCard';
import ExamInstructions from '../components/exam/ExamInstructions';
import ExamControls from '../components/exam/ExamControls';
import Footer from '../components/exam/Footer';
import ExamSelector from '../components/exam/ExamSelector';

const ExamPage = () => {
  const { examData, initializeExam, timeRemaining, resetExam } = useExam();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showExamSelector, setShowExamSelector] = useState(true);

  useEffect(() => {
    // Auto-submit when time runs out
    if (timeRemaining === 0 && examData) {
      alert("Time's up! Your exam is being submitted automatically.");
      // The SubmitModal component handles the actual submission
    }
  }, [timeRemaining, examData]);

  const handleExamSelect = async (exam, mode = 'exam') => {
    try {
      setLoading(true);
      setError(null);
      setShowExamSelector(false);

      // Load the selected exam
      const data = await getExamData(exam.id);
      initializeExam(data, mode);
    } catch (err) {
      console.error('Error loading exam:', err);
      setError('Failed to load exam data');
      setShowExamSelector(true);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToExamSelector = () => {
    resetExam();
    setShowExamSelector(true);
    setError(null);
  };

  // Show exam selector if no exam is selected
  if (showExamSelector) {
    return <ExamSelector onExamSelect={handleExamSelect} />;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-exam-blue mb-4"></i>
          <p className="text-gray-600 text-lg">Loading exam...</p>
        </div>
      </div>
    );
  }

  if (error && !examData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <i className="fas fa-exclamation-circle text-6xl text-exam-red mb-4"></i>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Exam</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={handleBackToExamSelector}
            className="px-6 py-3 bg-exam-blue text-white rounded-lg hover:bg-blue-700"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            Back to Exam Selection
          </button>
        </div>
      </div>
    );
  }

  if (!examData) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header onBackToHome={handleBackToExamSelector} />

      <main className="exam-container px-4 py-6 flex-grow">
        <div className="flex flex-col lg:flex-row gap-6">
          <Sidebar />
          <div className="lg:w-3/4">
            <QuestionCard />
            <ExamInstructions />
            <ExamControls />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default ExamPage;
