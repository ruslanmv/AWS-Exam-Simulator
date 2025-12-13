import { useState, useEffect } from 'react';
import { getExamList } from '../../services/api';

const ExamSelector = ({ onExamSelect }) => {
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedExam, setSelectedExam] = useState(null);
  const [selectedMode, setSelectedMode] = useState('training'); // 'training' or 'exam'
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      setLoading(true);
      const examList = await getExamList();
      setExams(examList);
    } catch (error) {
      console.error('Error loading exams:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExamSelect = (exam) => {
    setSelectedExam(exam);
  };

  const handleStartExam = () => {
    if (selectedExam) {
      onExamSelect(selectedExam, selectedMode);
    }
  };

  const filteredExams = exams.filter((exam) =>
    exam.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    exam.description?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Group exams by provider
  const groupedExams = filteredExams.reduce((acc, exam) => {
    const provider = exam.provider || 'Other';
    if (!acc[provider]) {
      acc[provider] = [];
    }
    acc[provider].push(exam);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-6xl text-exam-blue mb-4"></i>
          <p className="text-gray-600 text-xl">Loading exams...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-exam-blue rounded-lg flex items-center justify-center">
                <i className="fas fa-graduation-cap text-white text-2xl"></i>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AWS Exam Simulator</h1>
                <p className="text-sm text-gray-600">Prepare for your certification exams</p>
              </div>
            </div>
            <a
              href="https://github.com/ruslanmv/AWS-Exam-Simulator"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              <i className="fab fa-github"></i>
              <span>Star on GitHub</span>
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-12">
        {/* Welcome Section */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Welcome to AWS Exam Simulator
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Choose your certification exam below and start preparing with our comprehensive practice
            tests. Developed by{' '}
            <a
              href="https://ruslanmv.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-exam-blue hover:underline font-semibold"
            >
              ruslanmv.com
            </a>{' '}
            to help IT professionals achieve their certification goals.
          </p>
        </div>

        {/* Search Bar */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="relative">
            <input
              type="text"
              placeholder="Search for an exam..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-6 py-4 pl-14 text-lg border-2 border-gray-300 rounded-xl focus:border-exam-blue focus:outline-none shadow-sm"
            />
            <i className="fas fa-search absolute left-5 top-1/2 transform -translate-y-1/2 text-gray-400 text-xl"></i>
          </div>
        </div>

        {/* Mode Selection */}
        <div className="max-w-2xl mx-auto mb-12">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 text-center">Select Study Mode</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Training Mode */}
            <button
              onClick={() => setSelectedMode('training')}
              className={`p-6 rounded-xl border-2 transition-all ${
                selectedMode === 'training'
                  ? 'border-exam-blue bg-blue-50 shadow-lg ring-2 ring-exam-blue ring-opacity-50'
                  : 'border-gray-300 bg-white hover:border-exam-blue hover:shadow-md'
              }`}
            >
              <div className="flex items-start space-x-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  selectedMode === 'training' ? 'bg-exam-blue' : 'bg-gray-200'
                }`}>
                  <i className={`fas fa-book-reader text-2xl ${
                    selectedMode === 'training' ? 'text-white' : 'text-gray-600'
                  }`}></i>
                </div>
                <div className="flex-1 text-left">
                  <h4 className="text-xl font-bold text-gray-900 mb-2">Training Mode</h4>
                  <p className="text-sm text-gray-600 mb-2">
                    Study at your own pace with instant feedback
                  </p>
                  <ul className="text-xs text-gray-500 space-y-1">
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      See correct answers immediately
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      View explanations and references
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      No time limit
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      Navigate freely between questions
                    </li>
                  </ul>
                </div>
              </div>
            </button>

            {/* Exam Mode */}
            <button
              onClick={() => setSelectedMode('exam')}
              className={`p-6 rounded-xl border-2 transition-all ${
                selectedMode === 'exam'
                  ? 'border-exam-blue bg-blue-50 shadow-lg ring-2 ring-exam-blue ring-opacity-50'
                  : 'border-gray-300 bg-white hover:border-exam-blue hover:shadow-md'
              }`}
            >
              <div className="flex items-start space-x-4">
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                  selectedMode === 'exam' ? 'bg-exam-blue' : 'bg-gray-200'
                }`}>
                  <i className={`fas fa-stopwatch text-2xl ${
                    selectedMode === 'exam' ? 'text-white' : 'text-gray-600'
                  }`}></i>
                </div>
                <div className="flex-1 text-left">
                  <h4 className="text-xl font-bold text-gray-900 mb-2">Exam Mode</h4>
                  <p className="text-sm text-gray-600 mb-2">
                    Take a timed exam simulation
                  </p>
                  <ul className="text-xs text-gray-500 space-y-1">
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      Timed exam experience
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      See results after submission
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      Real exam simulation
                    </li>
                    <li className="flex items-center">
                      <i className="fas fa-check text-green-500 mr-2"></i>
                      Track your performance
                    </li>
                  </ul>
                </div>
              </div>
            </button>
          </div>
        </div>

        {/* Exam Grid */}
        <div className="max-w-6xl mx-auto">
          {Object.keys(groupedExams).length === 0 ? (
            <div className="text-center py-12">
              <i className="fas fa-search text-6xl text-gray-400 mb-4"></i>
              <p className="text-xl text-gray-600">No exams found matching your search.</p>
            </div>
          ) : (
            Object.entries(groupedExams).map(([provider, providerExams]) => (
              <div key={provider} className="mb-12">
                <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
                  {provider === 'AWS' && <i className="fab fa-aws text-orange-500 mr-3"></i>}
                  {provider === 'Azure' && <i className="fab fa-microsoft text-blue-500 mr-3"></i>}
                  {provider === 'GCP' && <i className="fab fa-google text-red-500 mr-3"></i>}
                  {provider} Certifications
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {providerExams.map((exam) => (
                    <div
                      key={exam.id}
                      onClick={() => handleExamSelect(exam)}
                      className={`bg-white rounded-xl shadow-md hover:shadow-xl transition-all cursor-pointer border-2 ${
                        selectedExam?.id === exam.id
                          ? 'border-exam-blue ring-2 ring-exam-blue ring-opacity-50'
                          : 'border-transparent hover:border-gray-300'
                      }`}
                    >
                      <div className="p-6">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h4 className="text-lg font-bold text-gray-900 mb-1">{exam.name}</h4>
                            <p className="text-sm text-gray-500">{exam.id}</p>
                          </div>
                          {selectedExam?.id === exam.id && (
                            <i className="fas fa-check-circle text-exam-blue text-2xl"></i>
                          )}
                        </div>
                        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                          {exam.description || 'Practice exam for certification preparation'}
                        </p>
                        <div className="flex items-center justify-between text-sm text-gray-500">
                          <div className="flex items-center space-x-4">
                            <span className="flex items-center">
                              <i className="fas fa-question-circle mr-1"></i>
                              {exam.totalQuestions} questions
                            </span>
                            <span className="flex items-center">
                              <i className="fas fa-clock mr-1"></i>
                              {exam.timeLimit} min
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Start Button */}
        {selectedExam && (
          <div className="fixed bottom-8 left-1/2 transform -translate-x-1/2 z-50">
            <button
              onClick={handleStartExam}
              className="px-8 py-4 bg-exam-blue text-white text-lg font-bold rounded-xl shadow-2xl hover:bg-blue-700 transition-all flex items-center space-x-3"
            >
              <i className={`fas ${selectedMode === 'training' ? 'fa-book-reader' : 'fa-stopwatch'}`}></i>
              <span>Start {selectedMode === 'training' ? 'Training' : 'Exam'}: {selectedExam.name}</span>
              <i className="fas fa-arrow-right"></i>
            </button>
          </div>
        )}
      </main>
    </div>
  );
};

export default ExamSelector;
