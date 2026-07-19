.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help:
	@echo "Knowledge Management System - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Setup development environment"
	@echo ""
	@echo "Development:"
	@echo "  make run          - Run development server"
	@echo "  make shell        - Open Python shell with app context"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests"
	@echo "  make test-fast    - Run fast tests (skip slow)"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-api     - Run API tests only"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint         - Run linters (pylint, mypy)"
	@echo "  make format       - Format code (black, isort)"
	@echo "  make check        - Run all checks (lint + format check)"
	@echo ""
	@echo "Database:"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-reset     - Reset database (WARNING: data loss)"
	@echo "  make db-seed      - Seed sample data"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make docker-logs  - View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Remove build artifacts and cache"
	@echo "  make docs         - Generate documentation"
	@echo "  make version      - Show project version"

# Install & Setup
install:
	poetry install
	poetry run pre-commit install

dev: install
	mkdir -p data logs uploads
	poetry run python -c "from src.core.database import init_db; init_db()"
	@echo "✅ Development environment ready!"

# Running
run:
	poetry run python -m uvicorn src.app.main:app --host 127.0.0.1 --port 8000 --reload

shell:
	poetry run python -c "from src.core.database import SessionLocal; from src.repositories.asset_repository import AssetRepository; db = SessionLocal(); repo = AssetRepository(db); import IPython; IPython.embed()"

# Testing
test:
	poetry run pytest -v

test-fast:
	poetry run pytest -v -m "not slow"

test-coverage:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing
	@echo "✅ Coverage report generated in htmlcov/index.html"

test-unit:
	poetry run pytest -v -m unit

test-api:
	poetry run pytest -v -m api

test-integration:
	poetry run pytest -v -m integration

# Code Quality
lint:
	poetry run pylint src tests || true
	poetry run mypy src || true

format:
	poetry run black src tests
	poetry run isort src tests

check: lint
	poetry run black --check src tests
	poetry run isort --check-only src tests

# Database
db-init:
	poetry run python -c "from src.core.database import init_db; init_db(); print('✅ Database initialized')"

db-reset:
	@read -p "⚠️  This will DELETE all data. Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -f data/knowledge_base.db; \
		poetry run python -c "from src.core.database import init_db; init_db()"; \
		echo "✅ Database reset"; \
	fi

db-seed:
	poetry run python scripts/seed_sample_data.py

# Docker
docker-build:
	docker build -t kms:latest .

docker-up:
	docker-compose up -d
	@echo "✅ Services started. Access at http://localhost:8000"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

docker-shell:
	docker-compose exec app /bin/bash

# Utilities
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	@echo "✅ Cleaned up"

docs:
	@echo "📚 Documentation files:"
	@echo "  - API.md           (API endpoints & examples)"
	@echo "  - ARCHITECTURE.md  (System design & components)"
	@echo "  - INSTALLATION.md  (Setup instructions)"
	@echo "  - TESTING.md       (Testing guide)"
	@echo ""
	@echo "API Docs available at: http://localhost:8000/api/docs"

version:
	@poetry version
	@echo ""
	@python -c "import sys; print(f'Python: {sys.version}')"

# Advanced
requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes
	poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes

update-deps:
	poetry update
	@echo "✅ Dependencies updated"

migrate:
	poetry run alembic upgrade head

fresh-install: clean
	rm -rf .venv pyproject.lock
	poetry install
	make dev

# Watch for changes
watch:
	@poetry run watchmedo auto-restart -d src -p '*.py' -- poetry run python -m uvicorn src.app.main:app --reload

# Benchmark
bench:
	poetry run python -c "import time; from src.integrations.local_vision import get_local_vision_client; start = time.time(); client = get_local_vision_client(); print(f'Model load time: {time.time() - start:.2f}s')"

# Pre-commit checks (run before commit)
pre-commit-check: check test
	@echo "✅ All pre-commit checks passed!"
