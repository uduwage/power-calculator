SHELL := /bin/sh

SOURCE_OBJECTS ?= power_calculator
DOCKERFILE ?= Dockerfile
IMAGE_NAME ?= power-calculator:latest

.PHONY: \
	format format.black format.ruff \
	lints lints.ci lints.format_check lints.ruff lints.mypy lints.dockerfile \
	docker.build docker.run

format.black:
	poetry run black $(SOURCE_OBJECTS)

format.ruff:
	poetry run ruff check --silent --fix --exit-zero $(SOURCE_OBJECTS)

format: format.ruff format.black

lints.format_check:
	poetry run black --check $(SOURCE_OBJECTS)

lints.ruff:
	poetry run ruff check $(SOURCE_OBJECTS)

lints.mypy:
	poetry run mypy $(SOURCE_OBJECTS)

lints.dockerfile:
	@if [ ! -f "$(DOCKERFILE)" ]; then \
		echo "Skipping hadolint: $(DOCKERFILE) not found"; \
	elif ! command -v hadolint >/dev/null 2>&1; then \
		echo "Skipping hadolint: hadolint is not installed"; \
	else \
		hadolint "$(DOCKERFILE)"; \
	fi

lints: lints.ruff lints.mypy lints.dockerfile

lints.ci: lints.format_check lints.ruff lints.mypy

docker.build:
	docker build -t $(IMAGE_NAME) .

docker.run:
	docker run --rm $(IMAGE_NAME) --help
