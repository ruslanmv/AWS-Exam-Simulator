const Footer = () => {
  return (
    <footer className="bg-gray-800 text-white mt-12">
      <div className="exam-container px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About Section */}
          <div>
            <div className="flex items-center mb-4">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <i className="fas fa-graduation-cap text-exam-blue"></i>
              </div>
              <span className="ml-2 text-xl font-bold">AWS Exam Simulator</span>
            </div>
            <p className="text-gray-400 text-sm">
              Professional cloud certification exam simulator to help IT professionals prepare and
              achieve their certification goals.
            </p>
          </div>

          {/* Developer Section */}
          <div>
            <h4 className="font-bold mb-4">Developer</h4>
            <div className="space-y-3 text-gray-400 text-sm">
              <p>
                Developed by{' '}
                <a
                  href="https://ruslanmv.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-exam-blue hover:text-blue-400 font-semibold"
                >
                  ruslanmv.com
                </a>
              </p>
              <p>
                Helping IT professionals train and prepare for cloud certifications including AWS,
                Azure, and Google Cloud Platform.
              </p>
              <a
                href="https://github.com/ruslanmv/AWS-Exam-Simulator"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
              >
                <i className="fab fa-github"></i>
                <span>Star on GitHub</span>
              </a>
            </div>
          </div>

          {/* Resources Section */}
          <div>
            <h4 className="font-bold mb-4">Resources</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li>
                <a
                  href="https://ruslanmv.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white flex items-center"
                >
                  <i className="fas fa-globe mr-2"></i>
                  Developer Website
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/ruslanmv/AWS-Exam-Simulator"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white flex items-center"
                >
                  <i className="fab fa-github mr-2"></i>
                  GitHub Repository
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/ruslanmv/AWS-Exam-Simulator/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white flex items-center"
                >
                  <i className="fas fa-bug mr-2"></i>
                  Report Issues
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/ruslanmv/AWS-Exam-Simulator#readme"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white flex items-center"
                >
                  <i className="fas fa-book mr-2"></i>
                  Documentation
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-6 text-center text-gray-400 text-sm">
          <p>
            © 2024 AWS Exam Simulator. Developed by{' '}
            <a
              href="https://ruslanmv.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-exam-blue hover:text-blue-400"
            >
              ruslanmv.com
            </a>
          </p>
          <p className="mt-2">
            This is an educational platform for certification preparation. AWS, Azure, and GCP are
            trademarks of their respective owners.
          </p>
          <p className="mt-2">
            If you find this project helpful,{' '}
            <a
              href="https://github.com/ruslanmv/AWS-Exam-Simulator"
              target="_blank"
              rel="noopener noreferrer"
              className="text-exam-blue hover:text-blue-400 font-semibold"
            >
              please star it on GitHub
            </a>
            !
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
