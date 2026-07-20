.DEFAULT_GOAL := help

.PHONY: setup dev-up dev-down docker-build docker-up docker-down clean help

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
STREAMLIT = $(VENV)/bin/streamlit

setup: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	touch $(VENV)/bin/activate

dev-up: setup
	@if [ -f .streamlit.pid ]; then \
		echo "Streamlit is already running (PID: $$(cat .streamlit.pid))"; \
	else \
		nohup $(STREAMLIT) run app.py > streamlit.log 2>&1 & echo $$! > .streamlit.pid; \
		echo "Streamlit started in the background (PID: $$(cat .streamlit.pid)). Logs at streamlit.log"; \
	fi

dev-down:
	@if [ -f .streamlit.pid ]; then \
		echo "Stopping Streamlit (PID: $$(cat .streamlit.pid))..."; \
		kill $$(cat .streamlit.pid) || true; \
		rm -f .streamlit.pid; \
		echo "Streamlit stopped."; \
	else \
		echo "No running Streamlit process found (no .streamlit.pid)."; \
		pkill -f "streamlit run app.py" || true; \
	fi

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf $(VENV)
	rm -f .streamlit.pid streamlit.log
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

help:
	@echo "========================================================================"
	@echo "📐 Drawer Calculator - Dev Tooling Shortcuts"
	@echo "========================================================================"
	@echo "Available make targets:"
	@echo "  make setup        - Set up Python virtual environment & install requirements"
	@echo "  make dev-up       - Launch Streamlit in the background (returns to prompt)"
	@echo "  make dev-down     - Stop the background Streamlit process"
	@echo "  make docker-build - Build production-ready Docker container image"
	@echo "  make docker-up    - Run application stack via Docker Compose (detached)"
	@echo "  make docker-down  - Terminate Docker Compose application stack"
	@echo "  make clean        - Purge virtual environments, PIDs, logs, and cache folders"
	@echo "  make help         - Display this developer help screen (default)"
	@echo "========================================================================"
