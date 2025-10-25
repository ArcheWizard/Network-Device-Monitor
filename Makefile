.PHONY: help setup dev test lint typecheck clean

# Default target
help:
	@echo "Network Device Monitor - Available commands:"
	@echo "  make setup      - Install all dependencies"
	@echo "  make dev        - Run backend in development mode"
	@echo "  make test       - Run all tests"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make typecheck  - Run type checker (mypy)"
	@echo "  make clean      - Clean build artifacts"

# Backend commands
setup:
	$(MAKE) -C backend setup

dev:
	$(MAKE) -C backend dev

test:
	$(MAKE) -C backend test

lint:
	$(MAKE) -C backend lint

typecheck:
	$(MAKE) -C backend typecheck

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
