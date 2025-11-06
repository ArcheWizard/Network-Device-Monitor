.PHONY: help setup venv frontend-setup backend-setup dev dev-with-influx dev-frontend \
    test test-backend test-frontend lint typecheck clean docker-up docker-down \
    seed-oui grant-scapy-cap run-frontend run-backend

# Default target
help:
	@echo "Network Device Monitor - Available commands:"
	@echo "  make setup           - Install backend + frontend dev deps"
	@echo "  make venv            - Create .venv and install backend deps"
	@echo "  make dev             - Run backend in development mode"
	@echo "  make dev-with-influx - Start InfluxDB (docker) then backend"
	@echo "  make run-frontend    - Run PyQt frontend"
	@echo "  make seed-oui        - Download and cache OUI DB"
	@echo "  make test            - Run backend tests"
	@echo "  make test-frontend   - Run frontend tests (requires display/pytest-qt)"
	@echo "  make lint            - Run lint (ruff)"
	@echo "  make typecheck       - Run mypy"
	@echo "  make clean           - Clean build artifacts"
	@echo "  make grant-scapy-cap - Grant CAP_NET_RAW/ADMIN to venv python (Linux)"

# Create virtual env (if missing) and install backend dev deps
venv:
	@test -d .venv || python3.11 -m venv .venv
	. .venv/bin/activate && python -m pip install --upgrade pip setuptools
	. .venv/bin/activate && pip install -r backend/requirements/dev.txt

# Frontend deps (install into active venv)
frontend-setup:
	. .venv/bin/activate && pip install -r frontend/pyqt/requirements.txt || true

# Backend setup convenience (delegates to backend/Makefile)
backend-setup:
	$(MAKE) -C backend setup

# Full setup (backend + frontend)
setup: venv frontend-setup

# Run backend dev server (delegates to backend Makefile)
dev:
	$(MAKE) -C backend dev

# Start InfluxDB (docker-compose) and run backend dev server
dev-with-influx: docker-up dev

# Run frontend (PyQt)
run-frontend:
	@echo "Running PyQt frontend (ensure .venv is activated if needed)"
	python frontend/pyqt/src/app.py

# Convenience to run backend via script if preferred (keeps compatibility)
run-backend:
	cd scripts && ./run_backend.sh

# Docker compose helpers
docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down -v || true

# Seed OUI via existing script (keeps script but allows make seed-oui)
seed-oui:
	bash scripts/seed_oui.sh

# Grant scapy capabilities to venv python (Linux only)
grant-scapy-cap:
	@if [ -f ".venv/bin/python" ]; then \
	  sudo setcap cap_net_raw,cap_net_admin=eip "$$(readlink -f .venv/bin/python)"; \
	  getcap "$$(readlink -f .venv/bin/python)"; \
	else \
	  echo "No .venv/python found. Run 'make venv' first or adjust path."; exit 1; \
	fi

# Tests
test:
	$(MAKE) -C backend test

test-backend: test

test-frontend:
	@echo "Running frontend tests; requires display / pytest-qt"
	cd frontend/pyqt && pytest -q

# Lint / typecheck (delegates to backend)
lint:
	$(MAKE) -C backend lint

typecheck:
	$(MAKE) -C backend typecheck

# Clean
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
