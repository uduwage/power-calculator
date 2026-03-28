SHELL := /bin/sh

SOURCE_OBJECTS ?= power_calculator
DOCKERFILE ?= Dockerfile
IMAGE_NAME ?= power-calculator:latest
PROJECT ?= power-calculator

.PHONY: \
	setup setup.sysdeps setup.python setup.project setup.uninstall \
	test.clean test.unit test.integration \
	format format.black format.ruff \
	lints lints.ci lints.format_check lints.ruff lints.mypy lints.dockerfile \
	docker.build docker.run

# Format source files with Black.
format.black:
	poetry run black $(SOURCE_OBJECTS)

# Auto-fix Ruff issues across the repository where possible.
format.ruff:
	poetry run ruff check --silent --fix .

# Run all formatting steps.
format: format.ruff format.black

# Check Black formatting without changing files.
lints.format_check:
	poetry run black --check $(SOURCE_OBJECTS)

# Run Ruff lint checks across the repository.
lints.ruff:
	poetry run ruff check .

# Run static type checks with mypy.
lints.mypy:
	poetry run mypy $(SOURCE_OBJECTS)

# Lint Dockerfile with hadolint when available.
lints.dockerfile:
	@if [ ! -f "$(DOCKERFILE)" ]; then \
		echo "Skipping hadolint: $(DOCKERFILE) not found"; \
	elif ! command -v hadolint >/dev/null 2>&1; then \
		echo "Skipping hadolint: hadolint is not installed"; \
	else \
		hadolint "$(DOCKERFILE)"; \
	fi

# Run all local lint checks, including Dockerfile linting.
lints: lints.format_check lints.ruff lints.mypy lints.dockerfile

# CI lint set (excludes optional Dockerfile linting).
lints.ci: lints.format_check lints.ruff lints.mypy

# Stop containers/images for this project and clean dangling images.
test.clean:
	docker-compose down
	-docker rmi $$(docker images -a | grep "$(PROJECT)" | tr -s ' ' | cut -d' ' -f3)
	-docker image prune -f

COVERAGE_MIN ?= 80

# IMPORTANT: Run `make setup` before running `make test.unit` the first time.
# Run unit tests only (integration tests excluded) with coverage reports.
test.unit:
	poetry run pytest \
		--ignore tests/integration \
		--cov=./power_calculator \
		--cov-fail-under=$(COVERAGE_MIN) \
		--cov-report=xml:coverage-report-unit-tests.xml \
		--junitxml=coverage-junit-unit-tests.xml \
		--cov-report term

# Run integration tests only.
test.integration:
	poetry run pytest tests/integration

# Bootstrap the full local development environment.
setup: setup.sysdeps setup.python setup.project

# Install and update asdf-managed tools from .tool-versions.
setup.sysdeps:
	@if ! command -v asdf >/dev/null 2>&1; then \
		echo "asdf is required for setup.sysdeps"; \
		exit 1; \
	fi
	@for p in $$(cut -d' ' -f1 .tool-versions | sort -u); do \
		asdf plugin add $$p >/dev/null 2>&1 || true; \
	done
	@asdf plugin update --all || true
	@asdf install

# Validate active Python version and bind Poetry to that interpreter.
setup.python:
	@echo "Active Python version: $$(python --version)"
	@echo "Base Interpreter path: $$(python -c 'import sys; print(sys.executable)')"
	@_python_version=$$(awk '/^python / {print $$2}' .tool-versions); \
	test "$$(python --version | awk '{print $$2}')" = "$$_python_version" \
	|| (echo "Please activate python version: $$_python_version" && exit 1)
	@poetry env use "$$(python -c 'import sys; print(sys.executable)')"
	@echo "Active interpreter path: $$(poetry env info --path)/bin/python"

# Install project dependencies into the Poetry environment.
setup.project:
	poetry install

# Remove the Poetry virtual environment (or local .venv fallback).
setup.uninstall:
	@_venv_path=$$(poetry env info --path 2>/dev/null || true); \
	if [ -z "$$_venv_path" ]; then \
		echo "setup.uninstall: didn't find a virtualenv to clean up"; \
		exit 0; \
	fi; \
	echo "attempting cleanup of $$_venv_path"; \
	_venv_name=$$(basename "$$_venv_path"); \
	(poetry env remove "$$_venv_name" >/dev/null 2>&1 || rm -rf ./.venv) \
	&& echo "all cleaned up!" \
	|| (echo "setup.uninstall: failed to remove the virtualenv." && exit 1)

# Build the Docker image for this project.
docker.build:
	docker build -t $(IMAGE_NAME) .

# Run the Docker image and show CLI help.
docker.run:
	docker run --rm $(IMAGE_NAME) --help
