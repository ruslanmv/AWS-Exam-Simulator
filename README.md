# AWS Exam Simulator - React Application

**Version 2.0** - Production-Ready React Application

Developed by Ruslan Magana Vsevolovna

A modern, production-ready React application for simulating AWS and cloud certification exams, built with Vite, React, and Tailwind CSS.

## Features

### Student View (Exam Simulator)
- **Interactive Exam Interface**: Take practice exams with a realistic exam interface
- **Timer**: Real-time countdown timer with auto-submit when time expires
- **Question Navigation**: Navigate between questions with visual progress indicators
- **Flag Questions**: Mark questions for review
- **Auto-save Progress**: Answers are automatically tracked
- **Responsive Design**: Works on desktop, tablet, and mobile devices

### Admin Portal
- **Secure Login**: Protected admin routes with authentication
- **Dashboard**: View exam statistics and analytics
- **Results Table**: View all student exam attempts with sorting and filtering
- **Export Functionality**: Export exam results and reports

### Technical Features
- **React Context API**: Global state management for exam state, timer, and authentication
- **Real Backend Integration**: API service layer ready for backend integration
- **Protected Routes**: Secure admin routes with authentication
- **Responsive UI**: Built with Tailwind CSS for modern, responsive design
- **Production Ready**: Optimized build with Vite

## Project Structure

```
src/
├── components/
│   ├── exam/                # Exam simulator components
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   ├── Timer.jsx
│   │   ├── QuestionCard.jsx
│   │   ├── ExamInstructions.jsx
│   │   ├── ExamControls.jsx
│   │   ├── SubmitModal.jsx
│   │   └── Footer.jsx
│   ├── admin/               # Admin portal components
│   │   ├── Login.jsx
│   │   ├── Dashboard.jsx
│   │   └── ResultsTable.jsx
│   └── common/              # Shared components
│       └── ProtectedRoute.jsx
├── context/                 # React Context providers
│   ├── AuthContext.jsx
│   └── ExamContext.jsx
├── pages/                   # Page components
│   ├── ExamPage.jsx
│   ├── AdminPage.jsx
│   └── ResultsPage.jsx
├── services/                # API services
│   └── api.js
├── App.jsx                  # Main app component
├── main.jsx                 # Entry point
└── index.css                # Global styles
```

## Installation

### Prerequisites
- Node.js (v18 or higher)
- npm (v9 or higher)

### Setup

1. **Install dependencies:**
   ```bash
   make install
   # or
   npm install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your backend API URL:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api
   ```

## Usage

### Development

Start the development server:
```bash
make start
# or
npm run dev
```

The application will be available at `http://localhost:3000`

### Production Build

Build for production:
```bash
make build
# or
npm run build
```

Preview the production build:
```bash
make preview
# or
npm run preview
```

### Clean

Remove build artifacts and dependencies:
```bash
make clean
```

## Makefile Targets

- `make install` - Install npm dependencies
- `make start` - Start development server
- `make build` - Build for production
- `make preview` - Preview production build
- `make clean` - Remove dist and node_modules
- `make help` - Show help message

## API Integration

The application uses a service layer (`src/services/api.js`) for all backend communication. Configure your backend URL using the `VITE_API_BASE_URL` environment variable.

### API Endpoints

The application expects the following endpoints:

#### Exam APIs
- `GET /exams` - Get list of available exams
- `GET /exams/:examId` - Get exam data with questions
- `POST /exams/submit` - Submit exam results
- `GET /exams/history` - Get user's exam history
- `GET /exams/results/:attemptId` - Get detailed results

#### Admin APIs
- `POST /admin/login` - Admin authentication
- `POST /admin/logout` - Admin logout
- `GET /admin/logs` - Get all exam attempts (with filters)
- `GET /admin/stats` - Get dashboard statistics
- `GET /admin/attempts/:attemptId` - Get detailed attempt information

#### User APIs
- `POST /users/register` - User registration
- `POST /users/login` - User authentication
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update user profile

### API Request/Response Format

Example exam submission:
```javascript
// Request
{
  examId: "SAA-C03",
  answers: {
    1: "a",
    2: "b",
    3: "c"
  },
  timeSpent: 3600,
  flaggedQuestions: [1, 5, 10],
  startTime: "2024-01-15T10:00:00Z",
  endTime: "2024-01-15T11:00:00Z"
}

// Response
{
  score: 85,
  correctAnswers: 55,
  totalQuestions: 65,
  timeSpent: "1h 45m",
  status: "passed"
}
```

## Deployment

### Build for Production

```bash
npm run build
```

The build output will be in the `dist/` directory.

### Deploy to Vercel

```bash
npm install -g vercel
vercel
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

### Environment Variables for Production

Make sure to set the following environment variables in your hosting platform:
- `VITE_API_BASE_URL` - Your production API URL

## Development Notes

### Mock Data

If the backend API is not available, the application falls back to mock data for development purposes. This allows frontend development without a running backend.

### Authentication

- Student routes are accessible without authentication (uses mock user)
- Admin routes require authentication via `/admin` login
- Protected routes automatically redirect to login if not authenticated

### State Management

The application uses React Context API for state management:
- **ExamContext**: Manages exam state, timer, answers, and navigation
- **AuthContext**: Manages user authentication and session

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

The AWS Exam Simulator is licensed under the MIT License.

## Acknowledgments

The AWS Exam Simulator is developed by Ruslan Magana Vsevolovna. For more information about the developer, please visit [ruslanmv.com](https://ruslanmv.com/).

## Support

For issues and questions, please visit the GitHub repository or contact the developer.

---

The AWS Exam Simulator is a valuable tool for anyone preparing for an AWS exam. Its interactive quiz interface and instant feedback provide a comprehensive assessment of your skills and knowledge in AWS services. We hope you find this program helpful in your exam preparation journey!