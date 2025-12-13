.PHONY: install start build clean preview help

# Default target
.DEFAULT_GOAL := help

# Install dependencies
install:
	@echo "Installing dependencies..."
	npm install
	@echo "Dependencies installed successfully!"

# Start development server
start:
	@echo "Starting development server..."
	npm run dev

# Build for production
build:
	@echo "Building for production..."
	npm run build
	@echo "Build completed! Files are in ./dist"

# Preview production build
preview:
	@echo "Starting preview server..."
	npm run preview

# Clean build artifacts and dependencies
clean:
	@echo "Cleaning build artifacts and dependencies..."
	rm -rf dist node_modules
	@echo "Clean completed!"

# Show help
help:
	@echo "Available targets:"
	@echo "  make install  - Install npm dependencies"
	@echo "  make start    - Start development server"
	@echo "  make build    - Build for production"
	@echo "  make preview  - Preview production build"
	@echo "  make clean    - Remove dist and node_modules"
	@echo "  make help     - Show this help message"
