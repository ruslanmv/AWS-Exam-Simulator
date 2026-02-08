.PHONY: install install-python install-node install-ollama start build clean preview help \
       test test-unit test-integration test-agent lint mcp-server agent-server agent-cli \
       tutor-server

# Default target
.DEFAULT_GOAL := help

# ──────────────────────────────────────────────
#  Installation
# ──────────────────────────────────────────────

# Install everything (Python + Node + Ollama)
install: install-python install-node install-ollama
	@echo "All dependencies installed successfully!"

# Install Python dependencies (MCP server + agent + tests)
install-python:
	@echo "Installing Python dependencies..."
	pip install -e mcp_server/
	pip install 'pydantic>=2.7' pytest pytest-asyncio
	@echo "Python dependencies installed!"

# Install Node.js dependencies (React frontend)
install-node:
	@echo "Installing Node.js dependencies..."
	npm install 2>/dev/null || echo "npm not required for Python-only setup"
	@echo "Node.js dependencies installed!"

# Install Ollama (skip if already installed)
install-ollama:
	@if command -v ollama >/dev/null 2>&1; then \
		echo "Ollama already installed: $$(ollama --version 2>/dev/null || echo 'detected')"; \
	else \
		echo "Installing Ollama..."; \
		curl -fsSL https://ollama.com/install.sh | sh; \
		echo "Ollama installed successfully!"; \
	fi
	@echo "Pulling default model (qwen2.5:3b) for AI Learning Mode..."
	@ollama pull qwen2.5:3b 2>/dev/null || echo "Could not pull model. Start Ollama first: ollama serve"

# ──────────────────────────────────────────────
#  Testing
# ──────────────────────────────────────────────

# Run all tests
test:
	@echo "Running all tests..."
	python -m pytest tests/ -v --tb=short
	@echo "All tests passed!"

# Run unit tests only (fast)
test-unit:
	@echo "Running unit tests..."
	python -m pytest tests/test_exam_bank.py tests/test_tagging.py tests/test_session_store.py -v --tb=short

# Run integration tests (MCP tools)
test-integration:
	@echo "Running integration tests..."
	python -m pytest tests/test_mcp_tools.py -v --tb=short

# Run agent mock tests
test-agent:
	@echo "Running agent mock tests..."
	python -m pytest tests/test_agent_mock.py -v --tb=short

# ──────────────────────────────────────────────
#  Running Services
# ──────────────────────────────────────────────

# Run MCP server (stdio transport)
mcp-server:
	@echo "Starting MCP server (stdio)..."
	AWS_EXAM_QUESTION_DIR=./questions aws-exam-tools

# Run A2A agent as HTTP server
agent-server:
	@echo "Starting A2A tutor agent server on port 8080..."
	AWS_EXAM_QUESTION_DIR=./questions python agent_runtime/start_agent.py --server

# Run agent in interactive CLI mode
agent-cli:
	@echo "Starting interactive tutor agent..."
	AWS_EXAM_QUESTION_DIR=./questions python agent_runtime/start_agent.py

# Run Ollama AI tutor backend (for React Learning Mode)
tutor-server:
	@echo "Starting AI Tutor backend on port 8081..."
	AWS_EXAM_QUESTION_DIR=./questions python agent_runtime/ollama_tutor.py

# Start React development server
start:
	@echo "Starting React development server..."
	npm run dev

# Build React for production
build:
	@echo "Building React for production..."
	npm run build
	@echo "Build completed! Files are in ./dist"

# Preview production build
preview:
	@echo "Starting preview server..."
	npm run preview

# ──────────────────────────────────────────────
#  Maintenance
# ──────────────────────────────────────────────

# Lint Python code
lint:
	@echo "Linting Python code..."
	python -m py_compile mcp_server/src/aws_exam_tools/server_fastmcp.py
	python -m py_compile mcp_server/src/aws_exam_tools/exam_bank.py
	python -m py_compile mcp_server/src/aws_exam_tools/session_store.py
	python -m py_compile mcp_server/src/aws_exam_tools/tagging.py
	python -m py_compile mcp_server/src/aws_exam_tools/models.py
	python -m py_compile agent_runtime/agent.py
	python -m py_compile agent_runtime/config.py
	python -m py_compile agent_runtime/server.py
	python -m py_compile agent_runtime/ollama_tutor.py
	@echo "All Python files compile successfully!"

# Clean build artifacts and dependencies
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist node_modules
	rm -rf state/*.sqlite
	rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__
	rm -rf .pytest_cache tests/.pytest_cache
	rm -rf mcp_server/src/*.egg-info
	@echo "Clean completed!"

# ──────────────────────────────────────────────
#  Help
# ──────────────────────────────────────────────

help:
	@echo ""
	@echo "AWS Exam Simulator - AI Tutor Edition"
	@echo "======================================"
	@echo ""
	@echo "Installation:"
	@echo "  make install          - Install all dependencies (Python + Node + Ollama)"
	@echo "  make install-python   - Install Python dependencies only"
	@echo "  make install-node     - Install Node.js dependencies only"
	@echo "  make install-ollama   - Install Ollama + pull AI model"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests (fast)"
	@echo "  make test-integration - Run MCP integration tests"
	@echo "  make test-agent       - Run agent mock tests"
	@echo "  make lint             - Check Python syntax"
	@echo ""
	@echo "Running:"
	@echo "  make tutor-server     - AI Learning Mode backend (port 8081)"
	@echo "  make agent-cli        - Interactive AI tutor (CLI)"
	@echo "  make agent-server     - A2A HTTP server (port 8080)"
	@echo "  make mcp-server       - MCP tool server (stdio)"
	@echo "  make start            - React dev server"
	@echo ""
	@echo "Maintenance:"
	@echo "  make build            - Build React for production"
	@echo "  make clean            - Remove build artifacts"
	@echo "  make help             - Show this help"
	@echo ""
