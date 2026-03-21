.PHONY: help up down build logs test test-cov

help:
	@echo "Usage:"
	@echo "  make up              Start all services (with build)"
	@echo "  make down            Stop all services"
	@echo "  make build           Rebuild Docker images"
	@echo "  make logs            Tail logs from all services"
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