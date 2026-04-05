.PHONY: help up down build logs test test-cov test-frontend test-all e2e migration migrate stamp-head seed reset

help:
	@echo "Usage:"
	@echo "  make up              Start all services (with build)"
	@echo "  make down            Stop all services"
	@echo "  make build           Rebuild Docker images"
	@echo "  make logs            Tail logs from all services"
	@echo "  make test            Run backend tests (inside Docker)"
	@echo "  make test-cov        Run backend tests with coverage report"
	@echo "  make test-frontend   Run frontend unit tests (Vitest)"
	@echo "  make test-all        Run backend + frontend unit tests"
	@echo "  make e2e             Start db+api+web, wait for readiness, run Playwright E2E"
	@echo "  make migration msg=  Generate a new Alembic migration (e.g. msg='add index')"
	@echo "  make migrate         Apply pending migrations against the running DB"
	@echo "  make stamp-head      Mark existing DB as up-to-date (use on first deploy of existing DB)"
	@echo "  make seed            Populate the DB with initial Spanish learning content"
	@echo "  make reset           Remove all volumes and start fresh (wipes database)"

up:
	docker-compose up --build

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

test:
	docker-compose run --rm --no-deps \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/requirements-test.txt:/app/requirements-test.txt \
		-v $(PWD)/backend/tests:/app/tests \
		-v $(PWD)/backend/pytest.ini:/app/pytest.ini \
		api sh -c "pip install -q -r requirements-test.txt && pytest"

test-cov:
	docker-compose run --rm --no-deps \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/requirements-test.txt:/app/requirements-test.txt \
		-v $(PWD)/backend/tests:/app/tests \
		-v $(PWD)/backend/pytest.ini:/app/pytest.ini \
		api sh -c "pip install -q -r requirements-test.txt && pytest --cov=app --cov-report=term-missing"

test-frontend:
	cd frontend && npm ci && npm run test

test-all: test test-frontend

e2e:
	@test -f .env || cp .env.example .env
	@set -e; \
	trap 'docker-compose down' EXIT INT TERM; \
	docker-compose up -d --build db api web; \
	echo "Waiting for API (http://127.0.0.1:8000/api/health)..."; \
	i=0; \
	while [ $$i -lt 90 ]; do \
		curl -sf http://127.0.0.1:8000/api/health >/dev/null && break; \
		i=$$((i+1)); \
		sleep 2; \
	done; \
	curl -sf http://127.0.0.1:8000/api/health >/dev/null || (echo "API did not become ready in time." && docker-compose logs --tail=80 api && exit 1); \
	echo "Seeding learning content (idempotent; required for Learn/Study/Review E2E)..."; \
	docker-compose run --rm api python scripts/seed.py; \
	echo "Waiting for Vite (http://127.0.0.1:5173/)..."; \
	i=0; \
	while [ $$i -lt 90 ]; do \
		curl -sf -o /dev/null http://127.0.0.1:5173/ && break; \
		i=$$((i+1)); \
		sleep 2; \
	done; \
	curl -sf -o /dev/null http://127.0.0.1:5173/ || (echo "Frontend did not become ready in time." && docker-compose logs --tail=80 web && exit 1); \
	cd frontend && npm ci && npx playwright install chromium && npm run test:e2e

migration:
	@test -n "$(msg)" || (echo "Usage: make migration msg='describe your change'" && exit 1)
	docker-compose run --rm \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/alembic.ini:/app/alembic.ini \
		-v $(PWD)/backend/alembic:/app/alembic \
		-v $(PWD)/backend/alembic/versions:/app/alembic/versions \
		api sh -c "pip install -q -r requirements.txt && alembic revision --autogenerate -m \"$(msg)\""

migrate:
	docker-compose run --rm \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/alembic.ini:/app/alembic.ini \
		-v $(PWD)/backend/alembic:/app/alembic \
		api sh -c "pip install -q -r requirements.txt && alembic upgrade head"

stamp-head:
	docker-compose run --rm \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/alembic.ini:/app/alembic.ini \
		-v $(PWD)/backend/alembic:/app/alembic \
		api sh -c "pip install -q -r requirements.txt && alembic stamp head"
seed:
	docker-compose run --rm api python scripts/seed.py

reset:
	@echo "Stopping containers and removing all volumes..."
	docker-compose down -v
	@echo "Volumes removed. Starting fresh..."
	docker-compose up --build -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Seeding initial data..."
	docker-compose run --rm api python scripts/seed.py
	@echo "Done! Access the app at http://localhost:5173"