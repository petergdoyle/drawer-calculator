.DEFAULT_GOAL := help

.PHONY: setup _check-setup dev-up dev-down dev-restart dev-status test docker-build docker-up docker-down clean help

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
STREAMLIT = $(VENV)/bin/streamlit
PORT = 8501

setup: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	@echo "📦 Setting up virtual environment..."
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate
	@echo "✅ Setup complete."

_check-setup:
	@if [ ! -f $(VENV)/bin/activate ]; then \
		echo "❌ Virtual environment not found. Please run 'make setup' first."; \
		exit 1; \
	fi

dev-up: _check-setup
	@if curl -sf http://localhost:$(PORT)/_stcore/health > /dev/null 2>&1 || curl -sf http://localhost:$(PORT) > /dev/null 2>&1; then \
		echo "⚡ Streamlit is already running on http://localhost:$(PORT)"; \
	else \
		echo "🚀 Starting Streamlit server on port $(PORT)..."; \
		rm -f .streamlit.pid; \
		nohup $(STREAMLIT) run app.py --server.port $(PORT) > streamlit.log 2>&1 & echo $$! > .streamlit.pid; \
		echo "Waiting for app to start..."; \
		for i in 1 2 3 4 5; do \
			if curl -sf http://localhost:$(PORT) > /dev/null 2>&1; then break; fi; \
			sleep 1; \
		done; \
	fi
	@$(MAKE) --no-print-directory dev-status

dev-down:
	@IS_RUNNING=0; \
	if curl -sf http://localhost:$(PORT) > /dev/null 2>&1 || [ -f .streamlit.pid ]; then IS_RUNNING=1; fi; \
	if [ $$IS_RUNNING -eq 0 ]; then \
		echo "ℹ️  Streamlit is not running. Nothing to stop."; \
	else \
		echo "🛑 Stopping Streamlit server..."; \
		if [ -f .streamlit.pid ]; then \
			kill -9 $$(cat .streamlit.pid) 2>/dev/null || true; \
			rm -f .streamlit.pid; \
		fi; \
		pkill -f "streamlit run app.py" 2>/dev/null || true; \
		echo "✅ Streamlit stopped."; \
	fi

dev-restart: _check-setup
	@echo "🔄 Restarting Streamlit server..."
	@$(MAKE) --no-print-directory dev-down
	@sleep 1
	@$(MAKE) --no-print-directory dev-up

dev-status:
	@if curl -sf http://localhost:$(PORT)/_stcore/health > /dev/null 2>&1 || curl -sf http://localhost:$(PORT) > /dev/null 2>&1; then \
		echo "========================================================================"; \
		echo "✅ Streamlit is RUNNING"; \
		if [ -f .streamlit.pid ]; then echo "   📍 Process PID: $$(cat .streamlit.pid)"; fi; \
		if [ -f streamlit.log ]; then \
			grep -E "Local URL:|Network URL:" streamlit.log | sed 's/^[[:space:]]*/   🌐 /' || echo "   🌐 URL: http://localhost:$(PORT)"; \
		else \
			echo "   🌐 URL: http://localhost:$(PORT)"; \
		fi; \
		echo "========================================================================"; \
	else \
		if [ -f .streamlit.pid ]; then rm -f .streamlit.pid; fi; \
		echo "========================================================================"; \
		echo "⛔ Streamlit is NOT running."; \
		echo "========================================================================"; \
	fi

test: _check-setup
	@echo "🧪 Running unit tests..."
	@$(PYTHON) -m unittest discover tests

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	@echo "🧹 Cleaning up environments and temporary logs..."
	@$(MAKE) --no-print-directory dev-down 2>/dev/null || true
	rm -rf $(VENV)
	rm -f .streamlit.pid streamlit.log
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✨ Clean complete."

help:
	@echo "========================================================================"
	@echo "📐 Drawer Calculator - Dev Lifecycle Targets"
	@echo "========================================================================"
	@echo ""
	@echo "  ── Dev Lifecycle ──────────────────────────────────────────────────────"
	@echo "  make setup        - Install dependencies into local virtual environment"
	@echo "  make dev-up       - Start Streamlit app (idempotent, shows URLs)"
	@echo "  make dev-down     - Stop Streamlit app cleanly"
	@echo "  make dev-restart  - Restart Streamlit app cleanly"
	@echo "  make dev-status   - Check server status & display application URLs"
	@echo "  make test         - Run automated unit test suite"
	@echo ""
	@echo "  ── Docker ─────────────────────────────────────────────────────────────"
	@echo "  make docker-build - Build production Docker image"
	@echo "  make docker-up    - Run application in Docker Compose"
	@echo "  make docker-down  - Stop Docker Compose application"
	@echo ""
	@echo "  ── Utility ────────────────────────────────────────────────────────────"
	@echo "  make clean        - Purge virtual environments, PIDs, logs, and caches"
	@echo "  make help         - Display this help message"
	@echo ""
	@echo "========================================================================"
