import { useState } from 'react';
import { useExam } from '../../context/ExamContext';
import SubmitModal from './SubmitModal';

const ExamControls = () => {
  const { togglePause, isPaused } = useExam();
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  const handlePause = () => {
    togglePause();
  };

  return (
    <>
      <div className="mt-6 flex flex-col sm:flex-row items-center justify-between">
        <div className="flex items-center space-x-4 mb-4 sm:mb-0">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-exam-blue"></div>
            <span className="text-sm text-gray-600">Current Question</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-exam-green"></div>
            <span className="text-sm text-gray-600">Answered</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-exam-yellow"></div>
            <span className="text-sm text-gray-600">Flagged</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handlePause}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <i className={`fas ${isPaused ? 'fa-play' : 'fa-pause'} mr-2`}></i>
            {isPaused ? 'Resume Exam' : 'Pause Exam'}
          </button>
          <button
            onClick={() => setShowSubmitModal(true)}
            className="px-6 py-2 bg-exam-red text-white rounded-lg hover:bg-red-600 font-medium"
          >
            <i className="fas fa-paper-plane mr-2"></i>Submit Exam
          </button>
        </div>
      </div>

      <SubmitModal isOpen={showSubmitModal} onClose={() => setShowSubmitModal(false)} />
    </>
  );
};

export default ExamControls;
