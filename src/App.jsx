import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ExamProvider } from './context/ExamContext';
import ExamPage from './pages/ExamPage';
import AdminPage from './pages/AdminPage';
import ResultsPage from './pages/ResultsPage';

function App() {
  return (
    <Router>
      <AuthProvider>
        <ExamProvider>
          <Routes>
            {/* Main Exam Routes */}
            <Route path="/" element={<ExamPage />} />
            <Route path="/exam" element={<ExamPage />} />
            <Route path="/results" element={<ResultsPage />} />

            {/* Admin Routes */}
            <Route path="/admin/*" element={<AdminPage />} />

            {/* Catch-all redirect to home */}
            <Route path="*" element={<ExamPage />} />
          </Routes>
        </ExamProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
