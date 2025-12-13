import { useExam } from '../../context/ExamContext';

const QuestionCard = () => {
  const {
    getCurrentQuestion,
    currentQuestionIndex,
    examData,
    selectAnswer,
    clearAnswer,
    toggleFlag,
    isQuestionAnswered,
    isQuestionFlagged,
    answers,
    nextQuestion,
    previousQuestion,
    examMode,
    showFeedback,
  } = useExam();

  const question = getCurrentQuestion();

  if (!question || !examData) return null;

  const questionId = question.id;
  const selectedOption = answers[questionId];
  const isFlagged = isQuestionFlagged(questionId);
  const isFirstQuestion = currentQuestionIndex === 0;
  const isLastQuestion = currentQuestionIndex === examData.questions.length - 1;

  const handleOptionSelect = (optionId) => {
    selectAnswer(questionId, optionId);
  };

  const handleClearSelection = () => {
    clearAnswer(questionId);
  };

  const getOptionClass = (option) => {
    const baseClass =
      'flex items-start p-4 border-2 rounded-lg cursor-pointer transition-colors';

    // Training mode: show correct/incorrect feedback
    if (examMode === 'training' && showFeedback[questionId]) {
      if (option.correct) {
        return `${baseClass} bg-green-50 border-green-500 hover:bg-green-100`;
      }
      if (selectedOption === option.id && !option.correct) {
        return `${baseClass} bg-red-50 border-red-500 hover:bg-red-100`;
      }
      return `${baseClass} border-gray-300 opacity-60`;
    }

    // Regular mode: just highlight selected
    if (selectedOption === option.id) {
      return `${baseClass} border-exam-blue bg-blue-50 hover:bg-blue-100`;
    }
    return `${baseClass} border-gray-300 hover:bg-gray-50`;
  };

  return (
    <div className="lg:w-3/4">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 question-card">
        {/* Question Header */}
        <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-sm font-medium text-exam-blue bg-blue-50 px-2 py-1 rounded">
                Question {currentQuestionIndex + 1} of {examData.totalQuestions}
              </span>
              <span className="text-sm font-medium text-gray-600 bg-gray-100 px-2 py-1 rounded">
                {question.type === 'multiple-choice' ? 'Multiple Choice' : 'Multiple Select'}
              </span>
              {examMode === 'training' && (
                <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded flex items-center">
                  <i className="fas fa-book-reader mr-1"></i>
                  Training Mode
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-gray-800">
              {examData.title || 'AWS Solutions Architect Associate'}
            </h2>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => toggleFlag(questionId)}
              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              <i className={`${isFlagged ? 'fas flag-active' : 'far'} fa-flag text-gray-600`}></i>
              <span className="text-sm font-medium text-gray-700">
                {isFlagged ? 'Unflag' : 'Flag'}
              </span>
            </button>
            <button className="flex items-center space-x-2 px-3 py-2 bg-exam-blue text-white rounded-lg hover:bg-blue-700">
              <i className="fas fa-bookmark"></i>
              <span className="text-sm font-medium">Review Later</span>
            </button>
          </div>
        </div>

        {/* Question Content */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">{question.text}</h3>

          <div className="mb-6">
            <div className="flex items-center space-x-2 mb-3">
              <i className="fas fa-info-circle text-exam-blue"></i>
              <span className="text-sm text-gray-600">
                Select the correct answer. You can select only one option.
              </span>
            </div>
          </div>

          {/* Options */}
          <div className="space-y-3">
            {question.options.map((option) => (
              <div
                key={option.id}
                onClick={() => handleOptionSelect(option.id)}
                className={getOptionClass(option)}
              >
                <div className="flex items-center h-5">
                  <input
                    type="radio"
                    name={`question-${questionId}`}
                    value={option.id}
                    checked={selectedOption === option.id}
                    onChange={() => handleOptionSelect(option.id)}
                    className="w-4 h-4 text-exam-blue border-gray-300 focus:ring-exam-blue"
                  />
                </div>
                <div className="ml-3 flex-1 flex items-center justify-between">
                  <label className="font-medium text-gray-700 cursor-pointer">
                    {String.fromCharCode(65 + parseInt(option.id.charCodeAt(0) - 97))}.{' '}
                    {option.text}
                  </label>
                  {examMode === 'training' && showFeedback[questionId] && (
                    <div className="ml-4">
                      {option.correct ? (
                        <span className="text-green-600 flex items-center">
                          <i className="fas fa-check-circle text-xl"></i>
                          <span className="ml-2 text-sm font-semibold">Correct</span>
                        </span>
                      ) : selectedOption === option.id ? (
                        <span className="text-red-600 flex items-center">
                          <i className="fas fa-times-circle text-xl"></i>
                          <span className="ml-2 text-sm font-semibold">Incorrect</span>
                        </span>
                      ) : null}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Explanation in Training Mode */}
          {examMode === 'training' && showFeedback[questionId] && question.explanation && (
            <div className="mt-6 p-4 bg-blue-50 border-l-4 border-exam-blue rounded-lg">
              <div className="flex items-start">
                <i className="fas fa-lightbulb text-exam-blue text-xl mt-1"></i>
                <div className="ml-3">
                  <h4 className="font-bold text-gray-900 mb-2">Explanation</h4>
                  <p className="text-gray-700 text-sm leading-relaxed">{question.explanation}</p>
                  {question.references && (
                    <div className="mt-3 pt-3 border-t border-blue-200">
                      <p className="text-xs text-gray-600">
                        <strong>References:</strong> {question.references}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Question Navigation */}
        <div className="flex items-center justify-between pt-6 border-t border-gray-200">
          <div>
            <button
              onClick={previousQuestion}
              disabled={isFirstQuestion}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <i className="fas fa-arrow-left mr-2"></i>Previous
            </button>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleClearSelection}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              <i className="fas fa-redo mr-2"></i>Clear Selection
            </button>
            <button
              onClick={nextQuestion}
              className="px-4 py-2 bg-exam-blue text-white rounded-lg hover:bg-blue-700"
            >
              {isLastQuestion ? 'Review Exam' : 'Next Question'}
              <i className="fas fa-arrow-right ml-2"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionCard;
