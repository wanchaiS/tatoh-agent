# Project Makefile
# Centralized entry point for development, testing, and deployment

.PHONY: all help login lint format test db-migrate db-status push-backend push-frontend push-all

# Configuration
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
REGISTRY_NAME = aas-solution
REGISTRY_URL = registry.digitalocean.com/$(REGISTRY_NAME)
REPO_NAME = taatoh
BACKEND_DIR = agent_api
CLIENT_DIR = client

# Default target
all: help

help:
	@echo '---- Project Management ----'
	@echo 'login           - Login to DigitalOcean Container Registry'
	@echo 'check           - Run all quality checks (API + Client)'
	@echo 'check-api       - Run linting and type checks on Backend'
	@echo 'check-client    - Run linting and type checks on Frontend'
	@echo 'format          - Format backend code'
	@echo 'test            - Run backend tests'
	@echo 'db-migrate      - Run database migrations'
	@echo 'db-status       - Check database migration status'
	@echo '---- Deployment ----'
	@echo 'push            - Build and push both images to DOCR'
	@echo 'push-api        - Build and push backend image to DOCR'
	@echo 'push-client     - Build and push frontend image to DOCR'

# --- AUTHENTICATION ---

login:
	doctl registry login

# --- QUALITY ASSURANCE ---

check: check-api check-client

check-api:
	@echo "--- Checking Backend (API) ---"
	cd $(BACKEND_DIR) && uv run ruff check .
	cd $(BACKEND_DIR) && uv run ruff format . --diff
	cd $(BACKEND_DIR) && uv run mypy --strict agent api

check-client:
	@echo "--- Checking Frontend (Client) ---"
	cd $(CLIENT_DIR) && npm run lint
	@echo "--- Type Checking Frontend ---"
	cd $(CLIENT_DIR) && npx tsc -b

format: format-backend

format-backend:
	cd $(BACKEND_DIR) && uv run ruff format .
	cd $(BACKEND_DIR) && uv run ruff check --select I --fix .

test: test-backend

test-backend:
	cd $(BACKEND_DIR) && uv run python -m pytest tests/unit_tests/

# --- DATABASE ---

db-migrate:
	cd $(BACKEND_DIR) && uv run python -m scripts.db_manager migrate

db-status:
	cd $(BACKEND_DIR) && uv run python -m scripts.db_manager status

# --- DEPLOYMENT ---

push-api:
	@echo "Building and pushing backend (API)..."
	docker build -t $(REGISTRY_URL)/$(REPO_NAME):api-$(BRANCH) ./$(BACKEND_DIR)
	docker push $(REGISTRY_URL)/$(REPO_NAME):api-$(BRANCH)

push-client:
	@echo "Building and pushing frontend (Client)..."
	docker build -t $(REGISTRY_URL)/$(REPO_NAME):client-$(BRANCH) ./$(CLIENT_DIR)
	docker push $(REGISTRY_URL)/$(REPO_NAME):client-$(BRANCH)

push: push-api push-client
