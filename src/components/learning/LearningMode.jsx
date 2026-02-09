import { useState, useEffect, useRef } from 'react';
import { startSession, getNextQuestion, submitAnswer, microCheck, chatWithTutor } from '../../services/tutorApi';
import MarkdownContent from './MarkdownContent';
import WeakTopicsPanel from './WeakTopicsPanel';

/**
 * Learning Mode with teach-until-learned state machine.
 *
 * Phases: question -> feedback -> teaching -> micro_check -> question
 *
 * - Agent picks questions adaptively (weak topics first)
 * - Wrong answers trigger teaching + micro-check before advancing
 * - Mastery requires: correct first-try OR correct micro-check after teaching
 * - "I don't know" is a first-class option (no guessing penalty)
 * - Multi-select support for "choose two/three" questions
 */
const LearningMode = ({ examData, onBack }) => {
  // Session state
  const [sessionId, setSessionId] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [sessionError, setSessionError] = useState(null);

  // Question state
  const [question, setQuestion] = useState(null);
  const [stats, setStats] = useState(null);
  const [phase, setPhase] = useState('question'); // question | feedback | teaching | micro_check | mastered | complete

  // Answer state
  const [selectedOption, setSelectedOption] = useState(null);
  const [selectedOptions, setSelectedOptions] = useState(new Set()); // for multi-select
  const [submitted, setSubmitted] = useState(false);
  const [answerResult, setAnswerResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  // Micro-check state
  const [microCheckQ, setMicroCheckQ] = useState(null);
  const [mcSelected, setMcSelected] = useState(null);
  const [mcResult, setMcResult] = useState(null);
  const [mcLoading, setMcLoading] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Initialize session
  useEffect(() => {
    initSession();
  }, [examData.id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, phase]);

  const initSession = async () => {
    setSessionLoading(true);
    setSessionError(null);
    try {
      const result = await startSession(examData.id);
      setSessionId(result.session_id);
      if (result.question) {
        setQuestion(result.question);
        setPhase('question');
      }
    } catch (err) {
      setSessionError('Failed to start AI learning session. Is the tutor server running? (make tutor-server)');
    } finally {
      setSessionLoading(false);
    }
  };

  const resetForNewQuestion = () => {
    setSelectedOption(null);
    setSelectedOptions(new Set());
    setSubmitted(false);
    setAnswerResult(null);
    setMicroCheckQ(null);
    setMcSelected(null);
    setMcResult(null);
    setChatMessages([]);
    setChatInput('');
  };

  // --- Actions ---

  const handleSubmitAnswer = async (idk = false) => {
    if (!sessionId || (!idk && selectedOption === null && selectedOptions.size === 0)) return;
    setSubmitted(true);
    setAiLoading(true);

    try {
      const params = { session_id: sessionId };
      if (idk) {
        params.idk = true;
      } else if (question.multi_select) {
        params.answer_indices = [...selectedOptions];
      } else {
        params.answer_index = selectedOption;
      }

      const result = await submitAnswer(params);
      setAnswerResult(result);
      setStats(result.stats);

      if (result.ai_response) {
        setChatMessages([{ role: 'assistant', content: result.ai_response }]);
      }

      if (result.needs_micro_check) {
        setPhase('teaching');
      } else {
        setPhase('feedback');
      }
    } catch (err) {
      // Fallback if backend is down
      const isCorrect = question.correct_indices?.includes(selectedOption);
      setAnswerResult({
        correct: isCorrect && !idk,
        correct_answer: question.options?.[question.correct_indices?.[0]] || '',
        ai_response: null,
        needs_micro_check: !isCorrect || idk,
      });
      setChatMessages([{
        role: 'assistant',
        content: isCorrect && !idk
          ? `**Correct!** ${question.explanation || ''}`
          : `**${idk ? "Let's learn this!" : 'Not quite.'}** The correct answer is: ${question.options?.[question.correct_indices?.[0]] || ''}${question.explanation ? `\n\n**Explanation:** ${question.explanation}` : ''}`,
      }]);
      setPhase(isCorrect && !idk ? 'feedback' : 'teaching');
    } finally {
      setAiLoading(false);
    }
  };

  const handleRetry = () => {
    setSelectedOption(null);
    setSelectedOptions(new Set());
    setSubmitted(false);
    setAnswerResult(null);
    setMicroCheckQ(null);
    setMcSelected(null);
    setMcResult(null);
    setPhase('question');
  };

  const handleStartMicroCheck = async () => {
    if (!sessionId) return;
    setMcLoading(true);
    try {
      const result = await microCheck({ session_id: sessionId, action: 'generate' });
      setMicroCheckQ(result.micro_check);
      setPhase('micro_check');
    } catch {
      // Fallback micro-check
      setMicroCheckQ({
        question: `True or False: "${question.options?.[question.correct_indices?.[0]] || ''}" is the correct answer to this question.`,
        options: ['True', 'False'],
        correct_index: 0,
        explanation: 'This was the correct answer from the original question.',
      });
      setPhase('micro_check');
    } finally {
      setMcLoading(false);
    }
  };

  const handleCheckMicroCheck = async () => {
    if (mcSelected === null || !sessionId) return;
    setMcLoading(true);
    try {
      const result = await microCheck({
        session_id: sessionId,
        action: 'check',
        answer_index: mcSelected,
      });
      setMcResult(result);
      if (result.stats) setStats(result.stats);
      setPhase(result.mastered ? 'mastered' : 'micro_check');
    } catch {
      const correct = mcSelected === (microCheckQ?.correct_index ?? 0);
      setMcResult({ correct, mastered: correct, explanation: microCheckQ?.explanation || '' });
      setPhase(correct ? 'mastered' : 'micro_check');
    } finally {
      setMcLoading(false);
    }
  };

  const handleNextQuestion = async () => {
    if (!sessionId) return;
    resetForNewQuestion();
    setAiLoading(true);
    try {
      const result = await getNextQuestion(sessionId);
      if (result.stats) setStats(result.stats);
      if (result.complete) {
        setPhase('complete');
        setQuestion(null);
      } else {
        setQuestion(result.question);
        setPhase('question');
      }
    } catch {
      setPhase('complete');
    } finally {
      setAiLoading(false);
    }
  };

  const handleSkipLearning = () => {
    handleNextQuestion();
  };

  const handleChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setChatLoading(true);
    try {
      const result = await chatWithTutor({
        message: msg,
        exam_id: examData.id,
        question_context: question ? `Question: ${question.text}\nCorrect: ${question.options?.[question.correct_indices?.[0]] || ''}` : '',
        history: chatMessages.slice(-6),
      });
      setChatMessages((prev) => [...prev, { role: 'assistant', content: result.response }]);
    } catch {
      setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Could not reach the AI tutor. Check that `make tutor-server` is running.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleChat();
    }
  };

  // --- Multi-select helpers ---
  const toggleMultiOption = (idx) => {
    setSelectedOptions((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  };

  // --- Option styling ---
  const getOptionClass = (idx) => {
    const base = 'flex items-start p-4 border-2 rounded-lg transition-colors';

    if (!submitted) {
      const isSelected = question?.multi_select ? selectedOptions.has(idx) : selectedOption === idx;
      if (isSelected) return `${base} border-purple-500 bg-purple-50 cursor-pointer`;
      return `${base} border-gray-300 hover:bg-gray-50 cursor-pointer`;
    }

    // After submission
    const isCorrect = question?.correct_indices?.includes(idx);
    const isUserPick = question?.multi_select ? selectedOptions.has(idx) : selectedOption === idx;
    if (isCorrect) return `${base} bg-green-50 border-green-500`;
    if (isUserPick && !isCorrect) return `${base} bg-red-50 border-red-500`;
    return `${base} border-gray-300 opacity-60`;
  };

  // --- Render: Loading / Error ---

  if (sessionLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-brain text-6xl text-purple-600 mb-4 animate-pulse"></i>
          <p className="text-gray-600 text-xl">Starting AI Learning Session...</p>
          <p className="text-gray-400 text-sm mt-2">Connecting to tutor backend</p>
        </div>
      </div>
    );
  }

  if (sessionError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center max-w-md">
          <i className="fas fa-exclamation-triangle text-6xl text-orange-500 mb-4"></i>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">AI Tutor Unavailable</h2>
          <p className="text-gray-600 mb-4">{sessionError}</p>
          <div className="space-y-3">
            <button onClick={initSession} className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 w-full">
              <i className="fas fa-redo mr-2"></i>Retry Connection
            </button>
            <button onClick={onBack} className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 w-full">
              <i className="fas fa-arrow-left mr-2"></i>Back to Exam Selection
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- Render: Complete ---

  if (phase === 'complete') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center max-w-lg">
          <i className="fas fa-trophy text-6xl text-yellow-500 mb-4"></i>
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Session Complete!</h2>
          {stats && (
            <div className="bg-white rounded-xl shadow-md p-6 mt-4 text-left">
              <div className="grid grid-cols-3 gap-4 text-center mb-4">
                <div><div className="text-2xl font-bold text-purple-600">{stats.mastered}</div><div className="text-xs text-gray-500">Mastered</div></div>
                <div><div className="text-2xl font-bold text-green-600">{Math.round(stats.accuracy * 100)}%</div><div className="text-xs text-gray-500">Accuracy</div></div>
                <div><div className="text-2xl font-bold text-blue-600 capitalize">{stats.mastery_level}</div><div className="text-xs text-gray-500">Level</div></div>
              </div>
              {stats.weak_tags?.length > 0 && (
                <div className="border-t pt-3">
                  <p className="text-sm font-semibold text-gray-700 mb-2">Areas to Review:</p>
                  <div className="flex flex-wrap gap-2">
                    {stats.weak_tags.map((wt) => (
                      <span key={wt.tag} className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded-full">
                        {wt.tag.replace('_', ' ')} ({Math.round(wt.accuracy * 100)}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          <button onClick={onBack} className="mt-6 px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700">
            <i className="fas fa-arrow-left mr-2"></i>Back to Exam Selection
          </button>
        </div>
      </div>
    );
  }

  if (!question) return null;

  // --- Render: Main Learning UI ---

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-indigo-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <button onClick={onBack} className="flex items-center space-x-2 px-3 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg">
                <i className="fas fa-arrow-left"></i>
                <span className="hidden sm:inline">Back</span>
              </button>
              <div className="w-9 h-9 bg-purple-600 rounded-lg flex items-center justify-center">
                <i className="fas fa-brain text-white text-lg"></i>
              </div>
              <div>
                <h1 className="text-sm font-bold text-gray-900">AI Learning Mode</h1>
                <p className="text-xs text-gray-500">{examData.title}</p>
              </div>
            </div>
            {stats && (
              <div className="flex items-center space-x-3">
                <div className="text-sm text-gray-600">
                  <span className="font-semibold text-purple-600">{stats.mastered}</span>
                  <span className="text-gray-400">/{stats.total_questions} mastered</span>
                </div>
                <div className="w-24 bg-gray-200 rounded-full h-2 hidden sm:block">
                  <div className="bg-purple-600 h-2 rounded-full transition-all"
                       style={{ width: `${stats.total_questions ? (stats.mastered / stats.total_questions) * 100 : 0}%` }}></div>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 flex-grow">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left: Question Panel */}
          <div className="lg:w-7/12">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              {/* Question Header */}
              <div className="flex items-center flex-wrap gap-2 mb-4 pb-3 border-b border-gray-200">
                <span className="text-sm font-medium text-purple-600 bg-purple-50 px-2 py-1 rounded">
                  Q{question.question_number || question.index + 1}/{question.total}
                </span>
                {question.multi_select && (
                  <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    Select Multiple
                  </span>
                )}
                {question.tags?.map((tag) => (
                  <span key={tag} className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                    {tag.replace('_', ' ')}
                  </span>
                ))}
                {phase === 'mastered' && (
                  <span className="text-sm font-medium text-green-600 bg-green-50 px-2 py-1 rounded flex items-center">
                    <i className="fas fa-check-circle mr-1"></i>Mastered
                  </span>
                )}
              </div>

              {/* Question Text */}
              <h3 className="text-base font-semibold text-gray-800 mb-5 leading-relaxed">{question.text}</h3>

              {/* Options */}
              <div className="space-y-3 mb-6">
                {question.options?.map((option, idx) => (
                  <div
                    key={idx}
                    onClick={() => {
                      if (submitted) return;
                      if (question.multi_select) toggleMultiOption(idx);
                      else setSelectedOption(idx);
                    }}
                    className={getOptionClass(idx)}
                  >
                    <div className="flex items-center h-5">
                      {question.multi_select ? (
                        <input
                          type="checkbox"
                          checked={selectedOptions.has(idx)}
                          onChange={() => !submitted && toggleMultiOption(idx)}
                          disabled={submitted}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                      ) : (
                        <input
                          type="radio"
                          name={`q-${question.index}`}
                          checked={selectedOption === idx}
                          onChange={() => !submitted && setSelectedOption(idx)}
                          disabled={submitted}
                          className="w-4 h-4 text-purple-600 border-gray-300 focus:ring-purple-500"
                        />
                      )}
                    </div>
                    <div className="ml-3 flex-1 flex items-center justify-between">
                      <label className="font-medium text-gray-700 cursor-pointer text-sm">
                        {String.fromCharCode(65 + idx)}. {option}
                      </label>
                      {submitted && (
                        <div className="ml-3 flex-shrink-0">
                          {question.correct_indices?.includes(idx) ? (
                            <i className="fas fa-check-circle text-green-600 text-lg"></i>
                          ) : (question.multi_select ? selectedOptions.has(idx) : selectedOption === idx) ? (
                            <i className="fas fa-times-circle text-red-600 text-lg"></i>
                          ) : null}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                <div className="flex items-center space-x-2">
                  {!submitted && phase === 'question' && (
                    <button
                      onClick={() => handleSubmitAnswer(true)}
                      disabled={aiLoading}
                      className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm disabled:opacity-50"
                    >
                      <i className="fas fa-question-circle mr-1"></i>I don't know
                    </button>
                  )}
                  {submitted && (phase === 'teaching' || phase === 'feedback') && (
                    <button
                      onClick={handleRetry}
                      className="px-4 py-2 border border-gray-300 text-gray-600 rounded-lg hover:bg-gray-50 text-sm"
                    >
                      <i className="fas fa-redo mr-1"></i>Retry
                    </button>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  {!submitted && phase === 'question' && (
                    <button
                      onClick={() => handleSubmitAnswer(false)}
                      disabled={(selectedOption === null && selectedOptions.size === 0) || aiLoading}
                      className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center text-sm"
                    >
                      {aiLoading ? (
                        <><i className="fas fa-spinner fa-spin mr-2"></i>Evaluating...</>
                      ) : (
                        <><i className="fas fa-paper-plane mr-2"></i>Submit</>
                      )}
                    </button>
                  )}

                  {phase === 'teaching' && !microCheckQ && (
                    <button
                      onClick={handleStartMicroCheck}
                      disabled={mcLoading}
                      className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center text-sm"
                    >
                      {mcLoading ? (
                        <><i className="fas fa-spinner fa-spin mr-2"></i>Generating...</>
                      ) : (
                        <><i className="fas fa-clipboard-check mr-2"></i>Check Understanding</>
                      )}
                    </button>
                  )}

                  {(phase === 'feedback' || phase === 'mastered') && (
                    <button
                      onClick={handleNextQuestion}
                      disabled={aiLoading}
                      className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center text-sm"
                    >
                      Next Question<i className="fas fa-arrow-right ml-2"></i>
                    </button>
                  )}

                  {(phase === 'teaching' || phase === 'micro_check') && (
                    <button
                      onClick={handleSkipLearning}
                      className="px-4 py-2 text-gray-500 hover:text-gray-700 text-sm"
                    >
                      Skip<i className="fas fa-forward ml-1"></i>
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Micro-Check Card */}
            {phase === 'micro_check' && microCheckQ && (
              <div className="mt-4 bg-white rounded-xl shadow-sm border-2 border-purple-300 p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <i className="fas fa-clipboard-check text-purple-600 text-lg"></i>
                  <h4 className="font-bold text-gray-900">Quick Check</h4>
                  <span className="text-xs text-gray-500">Verify you understood the concept</span>
                </div>
                <p className="text-sm font-medium text-gray-800 mb-4">{microCheckQ.question}</p>
                <div className="space-y-2 mb-4">
                  {microCheckQ.options?.map((opt, idx) => (
                    <div
                      key={idx}
                      onClick={() => !mcResult && setMcSelected(idx)}
                      className={`p-3 border-2 rounded-lg cursor-pointer transition-colors text-sm ${
                        mcResult
                          ? idx === microCheckQ.correct_index
                            ? 'border-green-500 bg-green-50'
                            : mcSelected === idx
                            ? 'border-red-500 bg-red-50'
                            : 'border-gray-200 opacity-60'
                          : mcSelected === idx
                          ? 'border-purple-500 bg-purple-50'
                          : 'border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span>{String.fromCharCode(65 + idx)}. {opt}</span>
                        {mcResult && idx === microCheckQ.correct_index && (
                          <i className="fas fa-check-circle text-green-600"></i>
                        )}
                        {mcResult && mcSelected === idx && idx !== microCheckQ.correct_index && (
                          <i className="fas fa-times-circle text-red-600"></i>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {!mcResult ? (
                  <button
                    onClick={handleCheckMicroCheck}
                    disabled={mcSelected === null || mcLoading}
                    className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 text-sm"
                  >
                    {mcLoading ? <><i className="fas fa-spinner fa-spin mr-2"></i>Checking...</> : 'Check Answer'}
                  </button>
                ) : mcResult.mastered ? (
                  <div className="flex items-center justify-between">
                    <span className="text-green-600 font-semibold text-sm flex items-center">
                      <i className="fas fa-check-circle mr-2"></i>Concept mastered!
                    </span>
                    <button onClick={handleNextQuestion} className="px-5 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">
                      Next Question<i className="fas fa-arrow-right ml-2"></i>
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-orange-600 text-sm">
                      {mcResult.can_retry !== false ? 'Not quite — review the teaching above and try again.' : 'Review the explanation above.'}
                    </span>
                    <div className="flex space-x-2">
                      {mcResult.can_retry !== false && (
                        <button onClick={handleStartMicroCheck} className="px-4 py-2 border border-purple-300 text-purple-600 rounded-lg hover:bg-purple-50 text-sm">
                          <i className="fas fa-redo mr-1"></i>New Check
                        </button>
                      )}
                      <button onClick={handleNextQuestion} className="px-4 py-2 text-gray-500 hover:text-gray-700 text-sm">
                        Skip<i className="fas fa-forward ml-1"></i>
                      </button>
                    </div>
                  </div>
                )}
                {mcResult?.explanation && (
                  <p className="mt-3 text-xs text-gray-600 bg-gray-50 p-2 rounded">{mcResult.explanation}</p>
                )}
              </div>
            )}
          </div>

          {/* Right: AI Tutor + Stats */}
          <div className="lg:w-5/12 space-y-4">
            {/* AI Chat Panel */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col" style={{ minHeight: '400px', maxHeight: 'calc(100vh - 240px)' }}>
              {/* Chat Header */}
              <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-t-xl">
                <div className="flex items-center space-x-2">
                  <div className="w-7 h-7 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                    <i className="fas fa-robot text-white text-sm"></i>
                  </div>
                  <div>
                    <h3 className="text-white font-semibold text-sm">AI Tutor</h3>
                    <p className="text-purple-200 text-xs">Powered by Ollama</p>
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {chatMessages.length === 0 && !aiLoading && (
                  <div className="flex flex-col items-center justify-center h-full text-gray-400 py-8">
                    <i className="fas fa-brain text-4xl mb-3"></i>
                    <p className="text-sm font-medium">AI Tutor Ready</p>
                    <p className="text-xs text-center mt-1 max-w-xs">
                      Submit your answer to get AI-powered feedback and teaching.
                    </p>
                  </div>
                )}

                {aiLoading && chatMessages.length === 0 && (
                  <div className="flex items-start space-x-2">
                    <div className="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <i className="fas fa-robot text-purple-600 text-xs"></i>
                    </div>
                    <div className="bg-gray-100 rounded-lg p-3">
                      <div className="flex items-center space-x-2">
                        <i className="fas fa-spinner fa-spin text-purple-600 text-sm"></i>
                        <span className="text-gray-600 text-xs">Analyzing your answer...</span>
                      </div>
                    </div>
                  </div>
                )}

                {chatMessages.map((msg, idx) => (
                  <div key={idx} className={`flex items-start space-x-2 ${msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''}`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                      msg.role === 'user' ? 'bg-blue-100' : 'bg-purple-100'
                    }`}>
                      <i className={`fas ${msg.role === 'user' ? 'fa-user text-blue-600' : 'fa-robot text-purple-600'} text-xs`}></i>
                    </div>
                    <div className={`rounded-lg p-3 max-w-[85%] ${
                      msg.role === 'user' ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50 border border-gray-200'
                    }`}>
                      <MarkdownContent content={msg.content} />
                    </div>
                  </div>
                ))}

                {chatLoading && (
                  <div className="flex items-start space-x-2">
                    <div className="w-7 h-7 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0">
                      <i className="fas fa-robot text-purple-600 text-xs"></i>
                    </div>
                    <div className="bg-gray-100 rounded-lg p-2">
                      <i className="fas fa-spinner fa-spin text-purple-600 text-sm"></i>
                    </div>
                  </div>
                )}

                <div ref={chatEndRef} />
              </div>

              {/* Chat Input */}
              <div className="px-3 py-2 border-t border-gray-200">
                <div className="flex items-end space-x-2">
                  <textarea
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyDown={handleChatKeyDown}
                    placeholder={submitted ? "Ask a follow-up question..." : "Submit your answer first..."}
                    disabled={!submitted || chatLoading}
                    rows={2}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none resize-none disabled:opacity-50 disabled:bg-gray-50 text-sm"
                  />
                  <button
                    onClick={handleChat}
                    disabled={!submitted || !chatInput.trim() || chatLoading}
                    className="px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
                  >
                    <i className="fas fa-paper-plane text-sm"></i>
                  </button>
                </div>
              </div>
            </div>

            {/* Weak Topics Panel */}
            <WeakTopicsPanel stats={stats} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default LearningMode;
