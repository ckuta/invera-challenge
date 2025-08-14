.PHONY: build up logs superuser seed test down extract-error-logs clean open-docs

# Build the Docker images
build:
	docker compose build

# Start the containers in detached mode
up:
	docker compose up -d

# Show logs of all containers or a specific one
logs:
	docker compose logs -f $(service)

# Create a superuser
superuser:
	docker compose exec web python manage.py createsuperuser

# Seed the database with sample data
seed:
	docker compose exec web python manage.py seed_data

# Run tests
test:
	docker compose exec web python manage.py test

# Stop containers
down:
	docker compose down

# Extract error logs
extract-error-logs:
	docker compose exec web cat logs/error.log > error_logs_$(shell date +%Y%m%d_%H%M%S).log

# Clean up: stop containers, remove volumes, and remove images
clean:
	docker compose down -v
	docker rmi $$(docker images -q invera_challenge-web)

# Open API documentation in the default browser
open-docs:
	python -m webbrowser "http://localhost:8000/api/docs/"

# Setup options - can be "docker" or "local", defaults to "docker"
ENV_TYPE ?= docker

.PHONY: setup
setup: ## Set up the initial project environment
	@echo "Setting up initial environment..."
ifeq ($(ENV_TYPE),docker)
	@python task_tracker/scripts/setup_env.py --docker
	@echo "Setting up for Docker environment"
	@make build
	@echo "Setup completed. Now you can run 'make up' to start the project."
else
	@python task_tracker/scripts/setup_env.py
	@echo "Setting up for local environment"
	@echo "Setup completed. Now you can continue with migrations."
endif

.PHONY: reset
reset: ## Reset the entire environment (data and configuration)
	@echo "Resetting the entire environment..."
	@python task_tracker/scripts/setup_env.py --force
ifeq ($(ENV_TYPE),docker)
	@make down
	@make up
endif
	@make seed
	@echo "Environment completely reset."