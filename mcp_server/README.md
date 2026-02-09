# AWS Exam Tools - MCP Server

Enterprise-grade MCP (Model Context Protocol) server that exposes AWS exam
simulator capabilities as deterministic tools.

## Tools

| Tool | Description |
|------|-------------|
| `exam_list` | List all available exams with question counts |
| `exam_start_session` | Start a new exam session (learning/practice/exam mode) |
| `exam_next_question` | Get the next question (adaptive selection in learning mode) |
| `exam_submit_answer` | Submit an answer and get feedback + remediation guidance |
| `exam_get_explanation` | Get detailed explanation for any question |
| `session_get_status` | Check accuracy, weak/strong areas, mastery level |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_EXAM_QUESTION_DIR` | No | `../questions` | Path to directory containing `*.json` question banks |
| `AWS_EXAM_DB_PATH` | No | `./state/aws_exam.sqlite` | Path to SQLite database for session tracking |

## Quick Start

```bash
# Install
cd mcp_server
pip install -e .

# Set question bank path (or use default)
export AWS_EXAM_QUESTION_DIR="../questions"

# Run (stdio transport)
aws-exam-tools
```

## Integration with MCP Gateway

```bash
# Expose as SSE via mcpgateway translator
python -m mcpgateway.translate \
  --stdio "aws-exam-tools" \
  --expose-sse \
  --port 9101
```

## Question Bank Format

The server auto-detects two JSON formats:

**Format A** (SAA-C03 style - with explanations):
```json
{
  "question": "...",
  "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
  "correct": "A. ...",
  "explanation": "...",
  "references": "https://..."
}
```

**Format B** (CLF-C02 style - simple):
```json
{
  "question": "...",
  "options": ["option1", "option2", "option3", "option4"],
  "correct": "option1"
}
```

## Session Modes

- **learning**: Adaptive question selection. Biases toward weak areas. The A2A
  tutor agent uses remediation hints to teach until the concept is learned.
- **practice**: Sequential questions with immediate feedback.
- **exam**: All questions, no feedback until the end. Simulates real exam conditions.
