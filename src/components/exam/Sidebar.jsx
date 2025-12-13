import { useState } from 'react';
import { useExam } from '../../context/ExamContext';
import Timer from './Timer';

const Sidebar = () => {
  const {
    examData,
    currentQuestionIndex,
    navigateToQuestion,
    isQuestionAnswered,
    isQuestionFlagged,
    getExamStats,
  } = useExam();

  const [isCollapsed, setIsCollapsed] = useState(false);

  const stats = getExamStats();

  const getQuestionButtonClass = (index) => {
    const questionId = examData?.questions[index]?.id;
    let bgColor = 'bg-gray-100';
    let textColor = 'text-gray-700';

    if (index === currentQuestionIndex) {
      bgColor = 'bg-exam-blue';
      textColor = 'text-white';
    } else if (isQuestionFlagged(questionId)) {
      bgColor = 'bg-exam-yellow';
      textColor = 'text-white';
    } else if (isQuestionAnswered(questionId)) {
      bgColor = 'bg-exam-green';
      textColor = 'text-white';
    }

    return `w-10 h-10 rounded-lg flex items-center justify-center font-medium ${bgColor} ${textColor} hover:opacity-90 transition-all cursor-pointer`;
  };

  if (!examData) return null;

  return (
    <div className="lg:w-1/4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-800">Question Navigator</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-2 rounded-lg hover:bg-gray-100"
            >
              <i className={`fas ${isCollapsed ? 'fa-expand' : 'fa-bars'} text-gray-600`}></i>
            </button>
          </div>
        </div>

        {!isCollapsed && (
          <>
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">Exam Progress</span>
                <span className="text-sm font-bold text-exam-blue">
                  {stats?.progressPercentage || 0}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-exam-blue h-2 rounded-full progress-bar"
                  style={{ width: `${stats?.progressPercentage || 0}%` }}
                ></div>
              </div>
            </div>

            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                {examData.title || 'AWS Solutions Architect'}
              </h3>
              <div className="grid grid-cols-5 gap-2">
                {examData.questions.map((question, index) => (
                  <button
                    key={question.id}
                    onClick={() => navigateToQuestion(index)}
                    className={getQuestionButtonClass(index)}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-exam-blue rounded-sm"></div>
                <span className="text-sm text-gray-600">Current</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-gray-300 rounded-sm"></div>
                <span className="text-sm text-gray-600">Unanswered</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-exam-green rounded-sm"></div>
                <span className="text-sm text-gray-600">Answered</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 bg-exam-yellow rounded-sm"></div>
                <span className="text-sm text-gray-600">Flagged</span>
              </div>
            </div>
          </>
        )}
      </div>

      <Timer />
    </div>
  );
};

export default Sidebar;
