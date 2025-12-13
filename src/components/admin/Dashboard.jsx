import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getAdminLogs, getAdminStats } from '../../services/api';
import ResultsTable from './ResultsTable';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExam, setSelectedExam] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch admin logs and stats in parallel
      const [logsResponse, statsResponse] = await Promise.all([
        getAdminLogs({ page: 1, limit: 100 }),
        getAdminStats(),
      ]);

      setLogs(logsResponse.data || logsResponse);
      setStats(statsResponse.data || statsResponse);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err.response?.data?.message || 'Failed to load dashboard data');

      // Set mock data for development if API fails
      setStats({
        totalExams: 156,
        totalStudents: 42,
        averageScore: 78.5,
        passRate: 73.2,
      });

      setLogs([
        {
          id: 1,
          studentName: 'John Doe',
          email: 'john.doe@example.com',
          examType: 'AWS Solutions Architect',
          examCode: 'SAA-C03',
          score: 85,
          correctAnswers: 55,
          totalQuestions: 65,
          status: 'passed',
          date: new Date('2024-01-15T10:30:00'),
          timeSpent: '1h 45m',
        },
        {
          id: 2,
          studentName: 'Jane Smith',
          email: 'jane.smith@example.com',
          examType: 'Azure Administrator',
          examCode: 'AZ-104',
          score: 92,
          correctAnswers: 46,
          totalQuestions: 50,
          status: 'passed',
          date: new Date('2024-01-14T14:20:00'),
          timeSpent: '1h 30m',
        },
        {
          id: 3,
          studentName: 'Bob Johnson',
          email: 'bob.johnson@example.com',
          examType: 'AWS Developer',
          examCode: 'DVA-C02',
          score: 68,
          correctAnswers: 44,
          totalQuestions: 65,
          status: 'failed',
          date: new Date('2024-01-13T09:15:00'),
          timeSpent: '2h 10m',
        },
        {
          id: 4,
          studentName: 'Alice Williams',
          email: 'alice.williams@example.com',
          examType: 'AWS Solutions Architect',
          examCode: 'SAA-C03',
          score: 78,
          correctAnswers: 51,
          totalQuestions: 65,
          status: 'passed',
          date: new Date('2024-01-12T11:00:00'),
          timeSpent: '1h 55m',
        },
        {
          id: 5,
          studentName: 'Charlie Brown',
          email: 'charlie.brown@example.com',
          examType: 'GCP Associate',
          examCode: 'GCP-ACE',
          score: 95,
          correctAnswers: 48,
          totalQuestions: 50,
          status: 'passed',
          date: new Date('2024-01-11T15:45:00'),
          timeSpent: '1h 20m',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (exam) => {
    setSelectedExam(exam);
  };

  const StatCard = ({ icon, title, value, subtitle, color }) => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className={`text-3xl font-bold ${color}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${color} bg-opacity-10`}>
          <i className={`${icon} text-2xl`}></i>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-exam-blue mb-4"></i>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-10 h-10 bg-exam-blue rounded-lg flex items-center justify-center">
                <i className="fas fa-shield-alt text-white text-xl"></i>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
                <p className="text-sm text-gray-500">Exam Results Management System</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="hidden md:flex items-center space-x-2 bg-gray-100 px-3 py-2 rounded-lg">
                <i className="fas fa-user-shield text-gray-600"></i>
                <span className="text-gray-700 font-medium">{user?.name || 'Admin'}</span>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 bg-exam-red text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                <i className="fas fa-sign-out-alt mr-2"></i>
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <i className="fas fa-exclamation-triangle text-yellow-500 mr-3"></i>
              <div>
                <p className="text-yellow-800 font-medium">API Connection Issue</p>
                <p className="text-yellow-700 text-sm">
                  Using sample data. Configure VITE_API_BASE_URL to connect to your backend.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon="fas fa-clipboard-list"
            title="Total Exams"
            value={stats?.totalExams || 0}
            subtitle="All time"
            color="text-exam-blue"
          />
          <StatCard
            icon="fas fa-users"
            title="Total Students"
            value={stats?.totalStudents || 0}
            subtitle="Registered users"
            color="text-exam-green"
          />
          <StatCard
            icon="fas fa-chart-line"
            title="Average Score"
            value={`${stats?.averageScore || 0}%`}
            subtitle="Across all exams"
            color="text-exam-yellow"
          />
          <StatCard
            icon="fas fa-check-circle"
            title="Pass Rate"
            value={`${stats?.passRate || 0}%`}
            subtitle="≥70% score"
            color="text-exam-green"
          />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <button className="bg-white border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-exam-blue hover:bg-blue-50 transition-all text-center group">
            <i className="fas fa-plus-circle text-3xl text-gray-400 group-hover:text-exam-blue mb-2"></i>
            <p className="font-medium text-gray-700 group-hover:text-exam-blue">Add New Exam</p>
          </button>
          <button className="bg-white border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-exam-blue hover:bg-blue-50 transition-all text-center group">
            <i className="fas fa-user-plus text-3xl text-gray-400 group-hover:text-exam-blue mb-2"></i>
            <p className="font-medium text-gray-700 group-hover:text-exam-blue">Add Student</p>
          </button>
          <button className="bg-white border-2 border-dashed border-gray-300 rounded-xl p-6 hover:border-exam-blue hover:bg-blue-50 transition-all text-center group">
            <i className="fas fa-file-export text-3xl text-gray-400 group-hover:text-exam-blue mb-2"></i>
            <p className="font-medium text-gray-700 group-hover:text-exam-blue">Export Reports</p>
          </button>
        </div>

        {/* Results Table */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Recent Exam Results</h2>
            <button
              onClick={fetchDashboardData}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm font-medium"
            >
              <i className="fas fa-sync-alt mr-2"></i>
              Refresh
            </button>
          </div>
          <ResultsTable data={logs} onViewDetails={handleViewDetails} />
        </div>
      </main>

      {/* Exam Details Modal */}
      {selectedExam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-2xl w-full p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-gray-900">Exam Details</h3>
              <button
                onClick={() => setSelectedExam(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                <i className="fas fa-times text-xl"></i>
              </button>
            </div>

            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Student Name</p>
                  <p className="font-semibold text-gray-900">{selectedExam.studentName}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Email</p>
                  <p className="font-semibold text-gray-900">{selectedExam.email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Exam Type</p>
                  <p className="font-semibold text-gray-900">{selectedExam.examType}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Exam Code</p>
                  <p className="font-semibold text-gray-900">{selectedExam.examCode}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Score</p>
                  <p className="text-2xl font-bold text-exam-blue">{selectedExam.score}%</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Status</p>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      selectedExam.score >= 70
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {selectedExam.score >= 70 ? 'Passed' : 'Failed'}
                  </span>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Date</p>
                  <p className="font-semibold text-gray-900">
                    {new Date(selectedExam.date).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Time Spent</p>
                  <p className="font-semibold text-gray-900">{selectedExam.timeSpent}</p>
                </div>
              </div>

              <div className="flex space-x-3">
                <button className="flex-1 px-4 py-2 bg-exam-blue text-white rounded-lg hover:bg-blue-700">
                  <i className="fas fa-file-pdf mr-2"></i>
                  Download Report
                </button>
                <button className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
                  <i className="fas fa-envelope mr-2"></i>
                  Email Student
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
