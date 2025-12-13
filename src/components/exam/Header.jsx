import { useAuth } from '../../context/AuthContext';

const Header = ({ onBackToHome }) => {
  const { user, logout } = useAuth();

  const handleNavigation = (page) => {
    if (page === 'home' && onBackToHome) {
      onBackToHome();
    } else {
      console.log(`Navigating to: ${page}`);
      // In a real application, this would handle routing
    }
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
              <span className="ml-2 text-xl font-bold text-gray-800">AWS Exam Simulator</span>
            </div>

            <div className="hidden md:flex items-center space-x-6">
              <button
                className="text-gray-600 hover:text-exam-blue font-medium"
                onClick={() => handleNavigation('home')}
              >
                <i className="fas fa-home mr-1"></i>
                Home
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-2 bg-gray-100 px-3 py-1 rounded-lg">
              <i className="fas fa-user text-gray-500"></i>
              <span className="text-gray-700 font-medium">
                {user?.name || 'Guest'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
