# Project Makefile
# Centralized entry point for development, testing, and deployment

.PHONY: all help login lint format test db-migrate db-status build-api build-client build push-api push-client push deploy

# Configuration
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
REGISTRY_NAME = aas-solution
REGISTRY_URL = registry.digitalocean.com/$(REGISTRY_NAME)
REPO_NAME = taatoh
BACKEND_DIR = agent_api
CLIENT_DIR = client
DROPLET_IP = [IP_ADDRESS]
DROPLET_USER = root
DROPLET_PATH = ~/tatoh-agent
PLATFORM ?= linux/amd64

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
	@echo 'build           - Compile-check both API and Client'
	@echo 'build-api       - Lint + type-check backend (ruff + mypy)'
	@echo 'build-client    - Production build frontend (npm run build)'
	@echo 'push            - Push both images to DOCR'
	@echo 'push-api        - Push backend image to DOCR'
	@echo 'push-client     - Push frontend image to DOCR'
	@echo 'deploy          - Pull latest images and restart services on Droplet'

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

# --- BUILD (compile checks) ---

build-api:
	@echo "--- Checking API compiles cleanly ---"
	cd $(BACKEND_DIR) && uv run ruff check .
	cd $(BACKEND_DIR) && uv run mypy --strict api agent

build-client:
	@echo "--- Building Frontend (Client) ---"
	cd $(CLIENT_DIR) && npm run build

build: build-api build-client

# --- DEPLOYMENT ---

deploy:
	@echo "Deploying to Droplet..."
	ssh $(DROPLET_USER)@$(DROPLET_IP) "cd $(DROPLET_PATH) && git pull && docker compose pull && docker compose up -d api client"
