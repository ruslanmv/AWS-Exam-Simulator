import { useAuth } from '../../context/AuthContext';

const Header = () => {
  const { user, logout } = useAuth();

  const handleNavigation = (page) => {
    console.log(`Navigating to: ${page}`);
    // In a real application, this would handle routing
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="exam-container px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-exam-blue rounded-lg flex items-center justify-center">
                <i className="fas fa-cloud text-white"></i>
              </div>
              <span className="ml-2 text-xl font-bold text-gray-800">CloudExam Pro</span>
            </div>

            <div className="hidden md:flex items-center space-x-6">
              <a
                href="#"
                className="text-gray-600 hover:text-exam-blue font-medium"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('home');
                }}
              >
                Home
              </a>
              <a
                href="#"
                className="text-gray-600 hover:text-exam-blue font-medium"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('exams');
                }}
              >
                Exams
              </a>
              <a
                href="#"
                className="text-gray-600 hover:text-exam-blue font-medium"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('practice');
                }}
              >
                Practice
              </a>
              <a
                href="#"
                className="text-gray-600 hover:text-exam-blue font-medium"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('results');
                }}
              >
                Results
              </a>
              <a
                href="#"
                className="text-gray-600 hover:text-exam-blue font-medium"
                onClick={(e) => {
                  e.preventDefault();
                  handleNavigation('help');
                }}
              >
                Help
              </a>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-2 bg-gray-100 px-3 py-1 rounded-lg">
              <i className="fas fa-user text-gray-500"></i>
              <span className="text-gray-700 font-medium">
                {user?.name || 'John Doe'}
              </span>
            </div>
            <button
              onClick={logout}
              className="bg-exam-blue text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <i className="fas fa-sign-out-alt mr-2"></i>Logout
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
