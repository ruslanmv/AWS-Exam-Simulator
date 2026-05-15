import { useRef, useState } from 'react';
import { buildExamFromQuestions } from '../../utils/examLoader';

const ImportExamPanel = ({ onImportedExam }) => {
  const fileInputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [examName, setExamName] = useState('');
  const [timeLimit, setTimeLimit] = useState(120);
  const [mode, setMode] = useState('training');

  const handleFile = async (file) => {
    setError(null);
    setPreview(null);

    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.json')) {
      setError('Please select a .json file.');
      return;
    }

    try {
      const text = await file.text();
      const raw = JSON.parse(text);
      const exam = buildExamFromQuestions(raw, {
        id: `imported-${Date.now()}`,
        name: file.name.replace(/\.json$/i, ''),
      });
      setPreview(exam);
      setExamName(exam.title);
      setTimeLimit(exam.timeLimit);
    } catch (err) {
      console.error('Failed to parse imported exam JSON:', err);
      setError(
        err instanceof SyntaxError
          ? `Could not parse JSON: ${err.message}`
          : err.message || 'Failed to import this exam file.'
      );
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  };

  const handleStart = () => {
    if (!preview) return;
    const examMeta = {
      id: preview.id,
      name: examName || preview.title,
      provider: 'Imported',
      description: `Imported exam · ${preview.totalQuestions} questions`,
      timeLimit: Number(timeLimit) || preview.timeLimit,
      totalQuestions: preview.totalQuestions,
      importedData: {
        ...preview,
        title: examName || preview.title,
        timeLimit: Number(timeLimit) || preview.timeLimit,
      },
    };
    onImportedExam(examMeta, mode);
  };

  const handleReset = () => {
    setPreview(null);
    setError(null);
    setExamName('');
    setTimeLimit(120);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <section className="max-w-6xl mx-auto mt-12 mb-32">
      <h3 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
        <i className="fas fa-file-import text-exam-blue mr-3"></i>
        Import your own exam
      </h3>
      <div className="flex justify-center">
        <div className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all border-2 border-transparent w-full max-w-sm">
          <div className="p-6">
            <h4 className="text-lg font-bold text-gray-900 mb-1">
              Import a custom exam
            </h4>
            <p className="text-sm text-gray-500 mb-4">
              Drop a JSON file to practice it here.
            </p>

            {!preview && (
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  dragOver
                    ? 'border-exam-blue bg-blue-50'
                    : 'border-gray-300 hover:border-exam-blue hover:bg-gray-50'
                }`}
              >
                <i className="fas fa-cloud-upload-alt text-3xl text-gray-400 mb-2"></i>
                <p className="text-sm font-medium text-gray-700">
                  Drop a JSON file, or click to choose
                </p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/json,.json"
                  className="hidden"
                  onChange={(e) => handleFile(e.target.files?.[0])}
                />
              </div>
            )}

            {error && (
              <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-start">
                <i className="fas fa-exclamation-circle mt-0.5 mr-2"></i>
                <div className="flex-1">{error}</div>
                <button
                  onClick={handleReset}
                  className="ml-2 text-red-700 hover:underline text-xs font-semibold"
                >
                  Try again
                </button>
              </div>
            )}

            {preview && (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded-lg text-sm">
                  <span className="text-green-800">
                    <i className="fas fa-check-circle mr-2"></i>
                    {preview.totalQuestions} questions loaded
                  </span>
                  <button
                    onClick={handleReset}
                    className="text-xs text-gray-600 hover:underline"
                  >
                    Change
                  </button>
                </div>

                <label className="block">
                  <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Name
                  </span>
                  <input
                    type="text"
                    value={examName}
                    onChange={(e) => setExamName(e.target.value)}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-exam-blue focus:outline-none"
                  />
                </label>
                <label className="block">
                  <span className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                    Time limit (min)
                  </span>
                  <input
                    type="number"
                    min="1"
                    max="600"
                    value={timeLimit}
                    onChange={(e) => setTimeLimit(e.target.value)}
                    className="mt-1 w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:border-exam-blue focus:outline-none"
                  />
                </label>

                <div className="flex gap-2">
                  <button
                    onClick={() => setMode('training')}
                    className={`flex-1 px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${
                      mode === 'training'
                        ? 'border-exam-blue bg-blue-50 text-exam-blue'
                        : 'border-gray-300 text-gray-700 hover:border-exam-blue'
                    }`}
                  >
                    Training
                  </button>
                  <button
                    onClick={() => setMode('exam')}
                    className={`flex-1 px-3 py-2 rounded-lg border text-sm font-medium transition-colors ${
                      mode === 'exam'
                        ? 'border-exam-blue bg-blue-50 text-exam-blue'
                        : 'border-gray-300 text-gray-700 hover:border-exam-blue'
                    }`}
                  >
                    Timed exam
                  </button>
                </div>

                <button
                  onClick={handleStart}
                  className="w-full px-4 py-2.5 bg-exam-blue text-white text-sm font-semibold rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Start imported exam
                  <i className="fas fa-arrow-right ml-2"></i>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};

export default ImportExamPanel;
