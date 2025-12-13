import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const results = location.state?.results;

  useEffect(() => {
    // If no results data, redirect to home
    if (!results) {
      navigate('/', { replace: true });
    }
  }, [results, navigate]);

  if (!results) {
    return null;
  }

  const isPassed = results.score >= 70;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="exam-container px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-exam-blue rounded-lg flex items-center justify-center">
                <i className="fas fa-cloud text-white"></i>
              </div>
              <span className="ml-2 text-xl font-bold text-gray-800">CloudExam Pro</span>
            </div>
          </div>
        </div>
      </header>

      {/* Results Content */}
      <main className="exam-container px-4 py-12">
        <div className="max-w-3xl mx-auto">
          {/* Result Header */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 mb-6 text-center">
            <div
              className={`w-20 h-20 rounded-full mx-auto mb-4 flex items-center justify-center ${
                isPassed ? 'bg-green-100' : 'bg-red-100'
              }`}
            >
              <i
                className={`fas ${isPassed ? 'fa-check' : 'fa-times'} text-4xl ${
                  isPassed ? 'text-green-600' : 'text-red-600'
                }`}
              ></i>
            </div>

            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {isPassed ? 'Congratulations!' : 'Exam Complete'}
            </h1>

            <p className="text-gray-600 mb-6">
              {isPassed
                ? 'You have successfully passed the exam!'
                : 'Keep practicing and try again!'}
            </p>

            <div className="inline-block">
              <div className="text-6xl font-bold mb-2" style={{ color: isPassed ? '#10b981' : '#ef4444' }}>
                {results.score}%
              </div>
              <p className="text-gray-600">Your Score</p>
            </div>
          </div>

          {/* Detailed Results */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 mb-6">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Exam Summary</h2>

            <div className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                <span className="text-gray-600">Total Questions:</span>
                <span className="font-semibold text-gray-900">{results.totalQuestions}</span>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                <span className="text-gray-600">Correct Answers:</span>
                <span className="font-semibold text-green-600">{results.correctAnswers}</span>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                <span className="text-gray-600">Incorrect Answers:</span>
                <span className="font-semibold text-red-600">
                  {results.totalQuestions - results.correctAnswers}
                </span>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                <span className="text-gray-600">Time Spent:</span>
                <span className="font-semibold text-gray-900">{results.timeSpent}</span>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-gray-200">
                <span className="text-gray-600">Passing Score:</span>
                <span className="font-semibold text-gray-900">70%</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Status:</span>
                <span
                  className={`px-4 py-1 rounded-full font-semibold ${
                    isPassed
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {isPassed ? 'PASSED' : 'FAILED'}
                </span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => navigate('/')}
              className="flex-1 px-6 py-3 bg-exam-blue text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              <i className="fas fa-home mr-2"></i>
              Back to Home
            </button>
            <button
              onClick={() => window.location.reload()}
              className="flex-1 px-6 py-3 border-2 border-exam-blue text-exam-blue rounded-lg hover:bg-blue-50 font-medium"
            >
              <i className="fas fa-redo mr-2"></i>
              Take Another Exam
            </button>
            <button className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium">
              <i className="fas fa-download mr-2"></i>
              Download Certificate
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ResultsPage;
