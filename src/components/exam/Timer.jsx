import { useExam } from '../../context/ExamContext';

const Timer = () => {
  const { timeRemaining, formatTime, examData } = useExam();

  const isLowTime = timeRemaining !== null && timeRemaining <= 300; // 5 minutes

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mt-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold text-gray-800">Time Remaining</h3>
        <i className="fas fa-clock text-exam-blue"></i>
      </div>
      <div className="text-center">
        <div
          className={`text-3xl font-bold mb-2 ${
            isLowTime ? 'text-exam-red timer-warning' : 'text-gray-800'
          }`}
        >
          {formatTime(timeRemaining)}
        </div>
        <div className="text-sm text-gray-600">
          {examData?.title || 'AWS SAA-C03'} ({examData?.totalQuestions || 65} Questions)
        </div>
      </div>
    </div>
  );
};

export default Timer;
