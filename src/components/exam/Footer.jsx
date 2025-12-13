const Footer = () => {
  const handleNavigation = (page) => {
    console.log(`Navigating to: ${page}`);
    // In a real application, this would handle routing
  };

  return (
    <footer className="bg-gray-800 text-white mt-12">
      <div className="exam-container px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center mb-4">
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                <i className="fas fa-cloud text-exam-blue"></i>
              </div>
              <span className="ml-2 text-xl font-bold">CloudExam Pro</span>
            </div>
            <p className="text-gray-400 text-sm">
              Professional cloud certification exam simulator for AWS, Azure, and Google Cloud
              Platform.
            </p>
          </div>

          <div>
            <h4 className="font-bold mb-4">Certifications</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('aws');
                  }}
                >
                  AWS Solutions Architect
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('azure');
                  }}
                >
                  Azure Administrator
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('gcp');
                  }}
                >
                  GCP Associate
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('security');
                  }}
                >
                  Security Specialty
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-4">Resources</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('study');
                  }}
                >
                  Study Guides
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('practice');
                  }}
                >
                  Practice Tests
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('blog');
                  }}
                >
                  Blog
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="hover:text-white"
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation('faq');
                  }}
                >
                  FAQ
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-bold mb-4">Contact</h4>
            <ul className="space-y-2 text-gray-400 text-sm">
              <li className="flex items-center space-x-2">
                <i className="fas fa-envelope"></i>
                <span>support@cloudexam.pro</span>
              </li>
              <li className="flex items-center space-x-2">
                <i className="fas fa-phone"></i>
                <span>+1 (555) 123-4567</span>
              </li>
              <li className="flex items-center space-x-2">
                <i className="fas fa-map-marker-alt"></i>
                <span>San Francisco, CA</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-700 mt-8 pt-6 text-center text-gray-400 text-sm">
          <p>
            © 2024 CloudExam Pro. All rights reserved. AWS and Azure are trademarks of their
            respective owners.
          </p>
          <p className="mt-2">This is a simulation platform for educational purposes only.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
