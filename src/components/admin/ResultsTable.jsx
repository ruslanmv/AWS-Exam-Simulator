import { useState } from 'react';

const ResultsTable = ({ data, onViewDetails }) => {
  const [sortConfig, setSortConfig] = useState({ key: 'date', direction: 'desc' });
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const handleSort = (key) => {
    const direction =
      sortConfig.key === key && sortConfig.direction === 'asc' ? 'desc' : 'asc';
    setSortConfig({ key, direction });
  };

  const getStatusBadge = (status, score) => {
    const isPassed = status === 'passed' || score >= 70;
    return (
      <span
        className={`px-3 py-1 rounded-full text-xs font-semibold ${
          isPassed
            ? 'bg-green-100 text-green-800'
            : 'bg-red-100 text-red-800'
        }`}
      >
        {isPassed ? 'Passed' : 'Failed'}
      </span>
    );
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-600 font-bold';
    if (score >= 70) return 'text-exam-green font-semibold';
    if (score >= 50) return 'text-exam-yellow font-semibold';
    return 'text-exam-red font-semibold';
  };

  // Filter and sort data
  const filteredData = data
    .filter((item) => {
      const matchesStatus =
        filterStatus === 'all' ||
        (filterStatus === 'passed' && (item.status === 'passed' || item.score >= 70)) ||
        (filterStatus === 'failed' && (item.status === 'failed' || item.score < 70));

      const matchesSearch =
        searchTerm === '' ||
        item.studentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.examType.toLowerCase().includes(searchTerm.toLowerCase());

      return matchesStatus && matchesSearch;
    })
    .sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (sortConfig.direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      {/* Table Header with Filters */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <i className="fas fa-search text-gray-400"></i>
              </div>
              <input
                type="text"
                placeholder="Search students or exams..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-exam-blue focus:border-exam-blue text-sm"
              />
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 text-sm focus:ring-exam-blue focus:border-exam-blue"
            >
              <option value="all">All Status</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
            </select>

            <button className="px-4 py-2 bg-exam-blue text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
              <i className="fas fa-download mr-2"></i>
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th
                onClick={() => handleSort('studentName')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Student Name
                  <i
                    className={`fas fa-sort ml-2 ${
                      sortConfig.key === 'studentName' ? 'text-exam-blue' : 'text-gray-400'
                    }`}
                  ></i>
                </div>
              </th>
              <th
                onClick={() => handleSort('examType')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Exam Type
                  <i
                    className={`fas fa-sort ml-2 ${
                      sortConfig.key === 'examType' ? 'text-exam-blue' : 'text-gray-400'
                    }`}
                  ></i>
                </div>
              </th>
              <th
                onClick={() => handleSort('score')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Score
                  <i
                    className={`fas fa-sort ml-2 ${
                      sortConfig.key === 'score' ? 'text-exam-blue' : 'text-gray-400'
                    }`}
                  ></i>
                </div>
              </th>
              <th
                onClick={() => handleSort('date')}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
              >
                <div className="flex items-center">
                  Date
                  <i
                    className={`fas fa-sort ml-2 ${
                      sortConfig.key === 'date' ? 'text-exam-blue' : 'text-gray-400'
                    }`}
                  ></i>
                </div>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Time Spent
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan="7" className="px-6 py-12 text-center text-gray-500">
                  <i className="fas fa-inbox text-4xl text-gray-300 mb-3"></i>
                  <p>No results found</p>
                </td>
              </tr>
            ) : (
              filteredData.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-10 h-10 rounded-full bg-exam-blue flex items-center justify-center text-white font-semibold">
                        {item.studentName.charAt(0).toUpperCase()}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{item.studentName}</div>
                        <div className="text-sm text-gray-500">{item.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{item.examType}</div>
                    <div className="text-sm text-gray-500">{item.examCode}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`text-lg ${getScoreColor(item.score)}`}>{item.score}%</div>
                    <div className="text-xs text-gray-500">
                      {item.correctAnswers}/{item.totalQuestions}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(item.date).toLocaleDateString()}
                    <div className="text-xs text-gray-400">
                      {new Date(item.date).toLocaleTimeString()}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(item.status, item.score)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {item.timeSpent}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => onViewDetails(item)}
                      className="text-exam-blue hover:text-blue-700 mr-3"
                    >
                      <i className="fas fa-eye mr-1"></i>
                      View
                    </button>
                    <button className="text-gray-600 hover:text-gray-800">
                      <i className="fas fa-download"></i>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {filteredData.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              Showing {filteredData.length} of {data.length} results
            </div>
            <div className="flex space-x-2">
              <button className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                Previous
              </button>
              <button className="px-3 py-1 bg-exam-blue text-white rounded-lg hover:bg-blue-700 text-sm">
                1
              </button>
              <button className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                2
              </button>
              <button className="px-3 py-1 border border-gray-300 rounded-lg hover:bg-gray-50 text-sm">
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsTable;
