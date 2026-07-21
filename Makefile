.PHONY: up down migrate seed run worker test lint

# Infrastructure
up:
	docker compose up -d --build

up-db:
	docker compose up -d postgres redis

down:
	docker compose down

# Database
migrate:
	uv run alembic upgrade head

migration:
	uv run alembic revision --autogenerate -m "$(msg)"

seed:
	uv run python -m src.pipeline.seed

# Application
run:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

worker:
	uv run celery -A src.tasks worker --loglevel=info

# Development
test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff format src/ tests/

# Pipeline
process-video:
	uv run python -m src.pipeline.ingestion --video-id $(id)

backfill:
	uv run python -m src.pipeline.ingestion --backfill --channel $(channel)
