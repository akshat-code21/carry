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

# Auth — create an invite code (invite-only signup gate)
# Example: make invite email=friend@example.com max-uses=1 expires-in-days=30
invite:
	PYTHONPATH=. uv run python scripts/create_invite.py \
		$(if $(email),--email $(email),) \
		--role $(or $(role),user) \
		--max-uses $(or $(max-uses),1) \
		$(if $(expires-in-days),--expires-in-days $(expires-in-days),)

promote-admin:
	PYTHONPATH=. uv run python scripts/promote_admin.py --email "$(email)"

# Auth — reconcile app users with Clerk (delete rows for deleted Clerk users,
# repair placeholder emails). Dry-run by default? No: pass dry-run=1 to preview.
sync-users:
	PYTHONPATH=. uv run python scripts/sync_users_from_clerk.py $(if $(dry-run),--dry-run,)

# Auth — bulk-provision pilot users with ready credentials from a CSV
# (name,email[,role]). They can log in with those creds OR Google (same email).
provision-users:
	PYTHONPATH=. uv run python scripts/provision_pilot_users.py $(csv) \
		--out $(or $(out),credentials.csv) \
		--login-url "$(or $(login-url),http://localhost:3000/sign-in)"

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
