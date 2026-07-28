.PHONY: up down migrate seed run worker beat test lint subscribe-websub simulate-websub

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

beat:
	uv run celery -A src.tasks beat --loglevel=info

# Re-subscribe all channels to YouTube WebSub (after ngrok URL change / first setup)
subscribe-websub:
	PYTHONPATH=. uv run python scripts/subscribe_all_channels_websub.py

# Fake a "channel just uploaded" WebSub push (no real YouTube upload needed)
# Example:
#   make simulate-websub channel=UCp4CBeq4nzeg9smAvdjPrig video=XXXXXXXXXXX
#   make simulate-websub channel=UCp4CBeq4nzeg9smAvdjPrig video=XXXXXXXXXXX mode=discovery_only
simulate-websub:
	PYTHONPATH=. uv run python scripts/simulate_websub.py \
		--youtube-channel-id "$(channel)" \
		--video-id "$(video)" \
		--mode "$(or $(mode),full)" \
		--title "$(or $(title),Simulated new upload (dry run))"

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
