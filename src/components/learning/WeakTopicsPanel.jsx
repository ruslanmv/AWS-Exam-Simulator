const TAG_LABELS = {
  iam: 'IAM & Access',
  vpc_networking: 'VPC & Networking',
  s3_storage: 'S3 & Storage',
  ec2_compute: 'EC2 & Compute',
  serverless: 'Serverless',
  containers: 'Containers',
  databases: 'Databases',
  monitoring_logging: 'Monitoring & Logging',
  security_encryption: 'Security & Encryption',
  high_availability: 'High Availability',
  cost_optimization: 'Cost Optimization',
  devops_cicd: 'DevOps & CI/CD',
  ml_ai: 'ML & AI',
  messaging_integration: 'Messaging & Integration',
  content_delivery: 'Content Delivery',
  analytics: 'Analytics',
  migration: 'Migration',
  general: 'General',
};

const WeakTopicsPanel = ({ stats }) => {
  if (!stats) return null;

  const { weak_tags = [], tag_summary = [], mastered = 0, total_questions = 0,
          answered = 0, correct = 0, accuracy = 0, mastery_level = 'beginner' } = stats;

  const masteryColors = {
    beginner: 'text-gray-600 bg-gray-100',
    intermediate: 'text-blue-600 bg-blue-100',
    advanced: 'text-purple-600 bg-purple-100',
    expert: 'text-green-600 bg-green-100',
  };

  return (
    <div className="space-y-4">
      {/* Session Progress */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
          <i className="fas fa-chart-line text-purple-600 mr-2"></i>
          Session Progress
        </h4>
        <div className="grid grid-cols-2 gap-3 text-center">
          <div className="bg-purple-50 rounded-lg p-2">
            <div className="text-lg font-bold text-purple-700">{mastered}</div>
            <div className="text-xs text-gray-500">Mastered</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-2">
            <div className="text-lg font-bold text-blue-700">{answered}</div>
            <div className="text-xs text-gray-500">Attempted</div>
          </div>
          <div className="bg-green-50 rounded-lg p-2">
            <div className="text-lg font-bold text-green-700">{Math.round(accuracy * 100)}%</div>
            <div className="text-xs text-gray-500">Accuracy</div>
          </div>
          <div className={`rounded-lg p-2 ${masteryColors[mastery_level] || masteryColors.beginner}`}>
            <div className="text-lg font-bold capitalize">{mastery_level}</div>
            <div className="text-xs text-gray-500">Level</div>
          </div>
        </div>
        <div className="mt-3">
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>Mastery</span>
            <span>{mastered}/{total_questions}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-purple-600 h-2 rounded-full transition-all"
              style={{ width: `${total_questions ? (mastered / total_questions) * 100 : 0}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Weak Topics */}
      {weak_tags.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
            <i className="fas fa-exclamation-triangle text-orange-500 mr-2"></i>
            Focus Areas
          </h4>
          <div className="space-y-2">
            {weak_tags.map((wt) => (
              <div key={wt.tag} className="flex items-center justify-between">
                <span className="text-xs text-gray-700 truncate flex-1">
                  {TAG_LABELS[wt.tag] || wt.tag}
                </span>
                <div className="flex items-center space-x-2 ml-2">
                  <div className="w-16 bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-orange-500 h-1.5 rounded-full"
                      style={{ width: `${wt.accuracy * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-orange-600 font-medium w-8 text-right">
                    {Math.round(wt.accuracy * 100)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Topics (collapsed) */}
      {tag_summary.length > 0 && (
        <details className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <summary className="text-sm font-semibold text-gray-700 cursor-pointer flex items-center">
            <i className="fas fa-tags text-blue-500 mr-2"></i>
            All Topics ({tag_summary.length})
          </summary>
          <div className="mt-3 space-y-1.5">
            {tag_summary.map((t) => (
              <div key={t.tag} className="flex items-center justify-between">
                <span className="text-xs text-gray-600 truncate flex-1">
                  {TAG_LABELS[t.tag] || t.tag}
                </span>
                <div className="flex items-center space-x-2 ml-2">
                  <span className="text-xs text-gray-400">{t.correct}/{t.asked}</span>
                  <div className="w-12 bg-gray-200 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${
                        t.accuracy >= 0.75 ? 'bg-green-500' : t.accuracy >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${t.accuracy * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
};

export default WeakTopicsPanel;
