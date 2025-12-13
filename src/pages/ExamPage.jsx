import { useEffect, useState } from 'react';
import { useExam } from '../context/ExamContext';
import { getExamData } from '../services/api';
import Header from '../components/exam/Header';
import Sidebar from '../components/exam/Sidebar';
import QuestionCard from '../components/exam/QuestionCard';
import ExamInstructions from '../components/exam/ExamInstructions';
import ExamControls from '../components/exam/ExamControls';
import Footer from '../components/exam/Footer';

const ExamPage = () => {
  const { examData, initializeExam, timeRemaining } = useExam();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Auto-submit when time runs out
    if (timeRemaining === 0 && examData) {
      alert("Time's up! Your exam is being submitted automatically.");
      // The SubmitModal component handles the actual submission
    }
  }, [timeRemaining, examData]);

  useEffect(() => {
    // Load exam data on mount if not already loaded
    if (!examData) {
      loadExam();
    }
  }, []);

  const loadExam = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try to fetch exam data from API
      const data = await getExamData('SAA-C03');
      initializeExam(data);
    } catch (err) {
      console.error('Error loading exam:', err);
      setError('Failed to load exam data');

      // Fallback to mock data if API fails
      const mockExamData = {
        id: 'SAA-C03',
        title: 'AWS Solutions Architect Associate (SAA-C03)',
        totalQuestions: 4,
        timeLimit: 2, // 2 minutes for demo
        questions: [
          {
            id: 1,
            text: 'A company is designing a multi-tier web application that will run on AWS. The application consists of a web tier, an application tier, and a database tier. The company wants to ensure high availability and fault tolerance across multiple Availability Zones. Which combination of AWS services should the company use to meet these requirements?',
            type: 'multiple-choice',
            options: [
              {
                id: 'a',
                text: 'Amazon EC2 instances with Elastic Load Balancing and Amazon RDS Multi-AZ deployment',
                correct: true,
              },
              {
                id: 'b',
                text: 'Amazon S3 for static content and Amazon DynamoDB for database',
                correct: false,
              },
              {
                id: 'c',
                text: 'AWS Lambda functions with Amazon API Gateway and Amazon DynamoDB',
                correct: false,
              },
              {
                id: 'd',
                text: 'Amazon EC2 instances with Auto Scaling groups and Amazon Aurora with read replicas',
                correct: false,
              },
            ],
            domain: 'Design Resilient Architectures',
          },
          {
            id: 2,
            text: 'A company needs to store sensitive data in Amazon S3 and ensure that the data is encrypted at rest. The company wants to maintain control over the encryption keys. Which encryption method should the company use?',
            type: 'multiple-choice',
            options: [
              {
                id: 'a',
                text: 'Server-side encryption with Amazon S3-managed keys (SSE-S3)',
                correct: false,
              },
              {
                id: 'b',
                text: 'Server-side encryption with AWS KMS-managed keys (SSE-KMS)',
                correct: true,
              },
              {
                id: 'c',
                text: 'Client-side encryption with customer-provided keys',
                correct: false,
              },
              {
                id: 'd',
                text: 'Server-side encryption with customer-provided keys (SSE-C)',
                correct: false,
              },
            ],
            domain: 'Design Secure Applications and Architectures',
          },
          {
            id: 3,
            text: 'Which AWS service provides a fully managed NoSQL database with single-digit millisecond latency at any scale?',
            type: 'multiple-choice',
            options: [
              {
                id: 'a',
                text: 'Amazon RDS',
                correct: false,
              },
              {
                id: 'b',
                text: 'Amazon DynamoDB',
                correct: true,
              },
              {
                id: 'c',
                text: 'Amazon Redshift',
                correct: false,
              },
              {
                id: 'd',
                text: 'Amazon ElastiCache',
                correct: false,
              },
            ],
            domain: 'Design High-Performing Architectures',
          },
          {
            id: 4,
            text: 'A company wants to implement a disaster recovery strategy with the lowest possible RTO and RPO. Which AWS disaster recovery approach should they use?',
            type: 'multiple-choice',
            options: [
              {
                id: 'a',
                text: 'Backup and Restore',
                correct: false,
              },
              {
                id: 'b',
                text: 'Pilot Light',
                correct: false,
              },
              {
                id: 'c',
                text: 'Warm Standby',
                correct: false,
              },
              {
                id: 'd',
                text: 'Multi-site Active-Active',
                correct: true,
              },
            ],
            domain: 'Design Resilient Architectures',
          },
        ],
      };

      initializeExam(mockExamData);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <i className="fas fa-spinner fa-spin text-4xl text-exam-blue mb-4"></i>
          <p className="text-gray-600 text-lg">Loading exam...</p>
        </div>
      </div>
    );
  }

  if (error && !examData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <i className="fas fa-exclamation-circle text-6xl text-exam-red mb-4"></i>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Error Loading Exam</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={loadExam}
            className="px-6 py-3 bg-exam-blue text-white rounded-lg hover:bg-blue-700"
          >
            <i className="fas fa-redo mr-2"></i>
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!examData) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <main className="exam-container px-4 py-6 flex-grow">
        <div className="flex flex-col lg:flex-row gap-6">
          <Sidebar />
          <div className="lg:w-3/4">
            <QuestionCard />
            <ExamInstructions />
            <ExamControls />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default ExamPage;
