.PHONY: help up down build logs test test-cov migrate migration stamp-head

help:
	@echo "Usage:"
	@echo "  make up              Start all services (with build)"
	@echo "  make down            Stop all services"
	@echo "  make build           Rebuild Docker images"
	@echo "  make logs            Tail logs from all services"
	@echo "  make migration msg=  Generate a new Alembic migration (e.g. msg='add index')"
	@echo "  make migrate         Apply pending migrations against the running DB"
	@echo "  make stamp-head      Mark existing DB as up-to-date (use on first deploy of existing DB)"
	@echo "  make test            Run backend tests (inside Docker)"
	@echo "  make test-cov        Run backend tests with coverage report"

up:
	docker-compose up --build

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f

test:
	docker-compose run --rm \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/requirements-test.txt:/app/requirements-test.txt \
		-v $(PWD)/backend/tests:/app/tests \
		-v $(PWD)/backend/pytest.ini:/app/pytest.ini \
		api sh -c "pip install -q -r requirements.txt -r requirements-test.txt && pytest"

test-cov:
	docker-compose run --rm \
		-v $(PWD)/backend/requirements.txt:/app/requirements.txt \
		-v $(PWD)/backend/requirements-test.txt:/app/requirements-test.txt \
		-v $(PWD)/backend/tests:/app/tests \
		-v $(PWD)/backend/pytest.ini:/app/pytest.ini \
		api sh -c "pip install -q -r requirements.txt -r requirements-test.txt && pytest --cov=app --cov-report=term-missing"


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