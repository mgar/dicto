.PHONY: help up down build logs

help:
	@echo "Usage:"
	@echo "  make up              Start all services (with build)"
	@echo "  make down            Stop all services"
	@echo "  make build           Rebuild Docker images"
	@echo "  make logs            Tail logs from all services"

up:
	docker-compose up --build

down:
	docker-compose down

build:
	docker-compose build

logs:
	docker-compose logs -f
