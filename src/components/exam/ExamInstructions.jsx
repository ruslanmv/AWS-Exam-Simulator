import { useExam } from '../../context/ExamContext';

const ExamInstructions = () => {
  const { examData } = useExam();

  return (
    <div className="mt-6 bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-gray-800">Exam Instructions</h3>
        <button className="text-exam-blue hover:text-blue-700">
          <i className="fas fa-expand"></i>
        </button>
      </div>
      <div className="text-sm text-gray-600 space-y-2">
        <div className="flex items-start space-x-2">
          <i className="fas fa-check-circle text-exam-green mt-1"></i>
          <span>
            This exam consists of {examData?.totalQuestions || 65} questions with a time limit of{' '}
            {examData?.timeLimit || 130} minutes.
          </span>
        </div>
        <div className="flex items-start space-x-2">
          <i className="fas fa-check-circle text-exam-green mt-1"></i>
          <span>You can flag questions for review and return to them later.</span>
        </div>
        <div className="flex items-start space-x-2">
          <i className="fas fa-check-circle text-exam-green mt-1"></i>
          <span>Your progress is automatically saved as you navigate through questions.</span>
        </div>
        <div className="flex items-start space-x-2">
          <i className="fas fa-check-circle text-exam-green mt-1"></i>
          <span>Once you submit the exam, you cannot return to review questions.</span>
        </div>
      </div>
    </div>
  );
};

export default ExamInstructions;
