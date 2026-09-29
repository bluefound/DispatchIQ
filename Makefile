# ============================================================
# DispatchIQ — Makefile
# ============================================================
# Common commands for development workflow

.PHONY: help up down build logs shell migrate seed test lint format

COMPOSE = docker compose

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ──────────────────────────────────────────────────

up: ## Start all services
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

build: ## Build all images
	$(COMPOSE) build

rebuild: ## Rebuild and restart all services
	$(COMPOSE) down && $(COMPOSE) build && $(COMPOSE) up -d

logs: ## Tail logs for all services
	$(COMPOSE) logs -f

logs-backend: ## Tail backend logs
	$(COMPOSE) logs -f backend

logs-celery: ## Tail celery worker logs
	$(COMPOSE) logs -f celery-worker

ps: ## Show running services
	$(COMPOSE) ps

# ── Backend ─────────────────────────────────────────────────

shell: ## Open a shell in the backend container
	$(COMPOSE) exec backend bash

shell-db: ## Open psql shell
	$(COMPOSE) exec postgres psql -U dispatchiq -d dispatchiq

# ── Database ────────────────────────────────────────────────

migrate: ## Run database migrations
	$(COMPOSE) exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	$(COMPOSE) exec backend alembic downgrade -1

migrate-history: ## Show migration history
	$(COMPOSE) exec backend alembic history

# ── Data ────────────────────────────────────────────────────

seed: ## Seed database with sample data
	$(COMPOSE) exec backend python -m scripts.seed_data

# ── Testing ─────────────────────────────────────────────────

test: ## Run backend tests
	$(COMPOSE) exec backend pytest -v

test-cov: ## Run tests with coverage
	$(COMPOSE) exec backend pytest --cov=app --cov-report=term-missing

# ── Code Quality ────────────────────────────────────────────

lint: ## Run linters
	$(COMPOSE) exec backend ruff check app/

format: ## Auto-format code
	$(COMPOSE) exec backend ruff format app/

type-check: ## Run type checking
	$(COMPOSE) exec backend mypy app/

# ── Frontend ────────────────────────────────────────────────

fe-install: ## Install frontend dependencies
	cd frontend && npm install

fe-dev: ## Start frontend dev server (outside Docker)
	cd frontend && npm run dev

fe-build: ## Build frontend
	cd frontend && npm run build

fe-lint: ## Lint frontend
	cd frontend && npm run lint

# ── Full Stack ──────────────────────────────────────────────

setup: ## Initial project setup
	cp -n .env.example .env || true
	$(COMPOSE) build
	$(COMPOSE) up -d
	@echo "Waiting for services to be ready..."
	sleep 10
	$(COMPOSE) exec backend alembic upgrade head
	$(COMPOSE) exec backend python -m scripts.seed_data
	@echo ""
	@echo "✅ DispatchIQ is ready!"
	@echo "   Backend:    http://localhost:8000"
	@echo "   Frontend:   http://localhost:3000"
	@echo "   API Docs:   http://localhost:8000/docs"
	@echo "   Grafana:    http://localhost:3001"
	@echo "   Prometheus: http://localhost:9090"

clean: ## Remove all containers, volumes, and images
	$(COMPOSE) down -v --rmi local
