import { useState, useEffect, useRef } from 'react';
import { evaluateAnswer, chatWithTutor } from '../../services/tutorApi';

const LearningMode = ({ examData, onBack }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [questionResults, setQuestionResults] = useState({});
  const [mastered, setMastered] = useState(new Set());
  const chatEndRef = useRef(null);

  const question = examData?.questions?.[currentIndex];
  const totalQuestions = examData?.questions?.length || 0;
  const masteredCount = mastered.size;

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Reset state when moving to a new question
  useEffect(() => {
    setSelectedOption(null);
    setSubmitted(false);
    setChatMessages([]);
    setChatInput('');
  }, [currentIndex]);

  if (!question || !examData) return null;

  const correctOption = question.options.find((o) => o.correct);
  const correctText = correctOption?.text || '';

  const handleSubmitAnswer = async () => {
    if (selectedOption === null) return;
    setSubmitted(true);
    setAiLoading(true);

    const selectedText = question.options[selectedOption]?.text || '';
    const isCorrect = question.options[selectedOption]?.correct === true;

    try {
      const result = await evaluateAnswer({
        exam_id: examData.id,
        question_index: currentIndex,
        user_answer: selectedText,
        question_text: question.text,
        options: question.options.map((o) => o.text),
        correct_answer: correctText,
        explanation: question.explanation || '',
      });

      setChatMessages([
        {
          role: 'assistant',
          content: result.ai_response,
        },
      ]);

      setQuestionResults((prev) => ({
        ...prev,
        [currentIndex]: { correct: isCorrect, attempts: (prev[currentIndex]?.attempts || 0) + 1 },
      }));

      if (isCorrect) {
        setMastered((prev) => new Set([...prev, currentIndex]));
      }
    } catch (err) {
      setChatMessages([
        {
          role: 'assistant',
          content: `**AI Tutor Offline** - Could not reach the AI backend.\n\n${
            question.options[selectedOption]?.correct
              ? '**Your answer is correct!**'
              : `**Incorrect.** The correct answer is: ${correctText}`
          }${question.explanation ? `\n\n**Explanation:** ${question.explanation}` : ''}`,
        },
      ]);
    } finally {
      setAiLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim() || chatLoading) return;

    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const result = await chatWithTutor({
        message: userMessage,
        exam_id: examData.id,
        question_context: `Question: ${question.text}\nCorrect Answer: ${correctText}`,
        history: chatMessages.slice(-6),
      });

      setChatMessages((prev) => [...prev, { role: 'assistant', content: result.response }]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, I could not connect to the AI tutor. Please make sure `make tutor-server` is running.' },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChat();
    }
  };

  const goToNext = () => {
    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const goToPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const getOptionClass = (idx) => {
    const base = 'flex items-start p-4 border-2 rounded-lg transition-colors';
    if (!submitted) {
      if (selectedOption === idx) return `${base} border-purple-500 bg-purple-50 cursor-pointer`;
      return `${base} border-gray-300 hover:bg-gray-50 cursor-pointer`;
    }
    // After submission
    if (question.options[idx]?.correct) return `${base} bg-green-50 border-green-500`;
    if (selectedOption === idx && !question.options[idx]?.correct) return `${base} bg-red-50 border-red-500`;
    return `${base} border-gray-300 opacity-60`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button
                onClick={onBack}
                className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <i className="fas fa-arrow-left"></i>
                <span>Back</span>
              </button>
              <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center">
                <i className="fas fa-brain text-white text-xl"></i>
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">AI Learning Mode</h1>
                <p className="text-xs text-gray-500">{examData.title}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-semibold text-purple-600">{masteredCount}</span>/{totalQuestions} mastered
              </div>
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-600 h-2 rounded-full transition-all"
                  style={{ width: `${(masteredCount / totalQuestions) * 100}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 flex-grow">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Question Panel */}
          <div className="lg:w-1/2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              {/* Question Header */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200">
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded">
                    Question {currentIndex + 1} of {totalQuestions}
                  </span>
                  {mastered.has(currentIndex) && (
                    <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded flex items-center">
                      <i className="fas fa-check-circle mr-1"></i>
                      Mastered
                    </span>
                  )}
                  {questionResults[currentIndex] && !mastered.has(currentIndex) && (
                    <span className="text-sm font-medium text-orange-600 bg-orange-50 px-2 py-1 rounded flex items-center">
                      <i className="fas fa-redo mr-1"></i>
                      {questionResults[currentIndex].attempts} attempt(s)
                    </span>
                  )}
                </div>
              </div>

              {/* Question Text */}
              <h3 className="text-lg font-semibold text-gray-800 mb-6">{question.text}</h3>

              {/* Options */}
              <div className="space-y-3 mb-6">
                {question.options.map((option, idx) => (
                  <div
                    key={option.id}
                    onClick={() => !submitted && setSelectedOption(idx)}
                    className={getOptionClass(idx)}
                  >
                    <div className="flex items-center h-5">
                      <input
                        type="radio"
                        name={`learning-q-${currentIndex}`}
                        checked={selectedOption === idx}
                        onChange={() => !submitted && setSelectedOption(idx)}
                        disabled={submitted}
                        className="w-4 h-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                      />
                    </div>
                    <div className="ml-3 flex-1 flex items-center justify-between">
                      <label className="font-medium text-gray-700 cursor-pointer">
                        {String.fromCharCode(65 + idx)}. {option.text}
                      </label>
                      {submitted && (
                        <div className="ml-4">
                          {option.correct ? (
                            <span className="text-green-600 flex items-center">
                              <i className="fas fa-check-circle text-lg"></i>
                            </span>
                          ) : selectedOption === idx ? (
                            <span className="text-red-600 flex items-center">
                              <i className="fas fa-times-circle text-lg"></i>
                            </span>
                          ) : null}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Submit / Navigation */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <button
                  onClick={goToPrev}
                  disabled={currentIndex === 0}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <i className="fas fa-arrow-left mr-2"></i>Previous
                </button>

                <div className="flex items-center space-x-3">
                  {!submitted ? (
                    <button
                      onClick={handleSubmitAnswer}
                      disabled={selectedOption === null || aiLoading}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    >
                      {aiLoading ? (
                        <>
                          <i className="fas fa-spinner fa-spin mr-2"></i>Evaluating...
                        </>
                      ) : (
                        <>
                          <i className="fas fa-paper-plane mr-2"></i>Submit Answer
                        </>
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={goToNext}
                      disabled={currentIndex >= totalQuestions - 1}
                      className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                    >
                      Next Question<i className="fas fa-arrow-right ml-2"></i>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Question Navigator */}
            <div className="mt-4 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <h4 className="text-sm font-semibold text-gray-700 mb-3">Question Navigator</h4>
              <div className="flex flex-wrap gap-2">
                {examData.questions.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentIndex(idx)}
                    className={`w-8 h-8 rounded-lg text-xs font-semibold transition-colors ${
                      idx === currentIndex
                        ? 'bg-purple-600 text-white'
                        : mastered.has(idx)
                        ? 'bg-green-100 text-green-700 border border-green-300'
                        : questionResults[idx]
                        ? 'bg-orange-100 text-orange-700 border border-orange-300'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>
              <div className="flex items-center space-x-4 mt-3 text-xs text-gray-500">
                <span className="flex items-center"><span className="w-3 h-3 rounded bg-green-100 border border-green-300 mr-1"></span> Mastered</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded bg-orange-100 border border-orange-300 mr-1"></span> Attempted</span>
                <span className="flex items-center"><span className="w-3 h-3 rounded bg-gray-100 mr-1"></span> Not started</span>
              </div>
            </div>
          </div>

          {/* AI Chat Panel */}
          <div className="lg:w-1/2">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col" style={{ height: 'calc(100vh - 160px)' }}>
              {/* Chat Header */}
              <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-t-xl">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                    <i className="fas fa-robot text-white"></i>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold">AI Tutor</h3>
                    <p className="text-purple-200 text-xs">Powered by Ollama - Ask me anything about this question</p>
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.length === 0 && !aiLoading && (
                  <div className="flex flex-col items-center justify-center h-full text-gray-400">
                    <i className="fas fa-brain text-6xl mb-4"></i>
                    <p className="text-lg font-medium">AI Tutor Ready</p>
                    <p className="text-sm text-center mt-2 max-w-xs">
                      Submit your answer and I'll evaluate it, then teach you the concept in depth.
                    </p>
                  </div>
                )}

                {aiLoading && chatMessages.length === 0 && (
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <i className="fas fa-robot text-purple-600 text-sm"></i>
                    </div>
                    <div className="bg-gray-100 rounded-lg p-4 max-w-md">
                      <div className="flex items-center space-x-2">
                        <i className="fas fa-spinner fa-spin text-purple-600"></i>
                        <span className="text-gray-600 text-sm">Analyzing your answer and preparing a deep-dive lesson...</span>
                      </div>
                    </div>
                  </div>
                )}

                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex items-start space-x-3 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user' ? 'bg-blue-100' : 'bg-purple-100'
                    }`}>
                      <i className={`fas ${msg.role === 'user' ? 'fa-user text-blue-600' : 'fa-robot text-purple-600'} text-sm`}></i>
                    </div>
                    <div className={`rounded-lg p-4 max-w-lg ${
                      msg.role === 'user' ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 border border-gray-200'
                    }`}>
                      <div className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed prose prose-sm max-w-none"
                           dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }} />
                    </div>
                  </div>
                ))}

                {chatLoading && (
                  <div className="flex items-start space-x-3">
                    <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <i className="fas fa-robot text-purple-600 text-sm"></i>
                    </div>
                    <div className="bg-gray-100 rounded-lg p-3">
                      <i className="fas fa-spinner fa-spin text-purple-600"></i>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              {/* Chat Input */}
              <div className="px-4 py-3 border-t border-gray-200">
                <div className="flex items-end space-x-2">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={submitted ? "Ask a follow-up question..." : "Submit your answer first to start the AI tutor..."}
                    disabled={!submitted || chatLoading}
                    rows={2}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none resize-none disabled:opacity-50 disabled:bg-gray-50 text-sm"
                  />
                  <button
                    onClick={handleChat}
                    disabled={!submitted || !chatInput.trim() || chatLoading}
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <i className="fas fa-paper-plane"></i>
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-1">Press Enter to send. Shift+Enter for new line.</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

/**
 * Simple markdown-to-HTML formatter for AI responses.
 * Handles bold, italic, headers, lists, and code blocks.
 */
function formatMarkdown(text) {
  if (!text) return '';
  let html = text
    // Escape HTML
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Code blocks
    .replace(/```([\s\S]*?)```/g, '<pre class="bg-gray-800 text-green-300 p-3 rounded-lg my-2 overflow-x-auto text-xs"><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-gray-200 px-1 rounded text-sm">$1</code>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h4 class="font-bold text-gray-900 mt-3 mb-1">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="font-bold text-gray-900 text-lg mt-3 mb-1">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="font-bold text-gray-900 text-xl mt-3 mb-1">$1</h2>')
    // Bullet lists
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal">$2</li>')
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p class="my-2">')
    // Single newlines
    .replace(/\n/g, '<br/>');

  return `<p class="my-1">${html}</p>`;
}

export default LearningMode;
