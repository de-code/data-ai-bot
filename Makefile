#!/usr/bin/make -f

DOCKER_COMPOSE_DEV = docker compose
DOCKER_COMPOSE_CI = docker compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)

VENV = venv
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python

PYTEST_WATCH_MODULES = tests/unit_tests

.require-%:
	@ if [ "${${*}}" = "" ]; then \
			echo "Environment variable $* not set"; \
			exit 1; \
	fi


venv-clean:
	@if [ -d "$(VENV)" ]; then \
		rm -rf "$(VENV)"; \
	fi


venv-create:
	python3 -m venv $(VENV)


venv-activate:
	chmod +x venv/bin/activate
	bash -c "venv/bin/activate"


dev-install:
	$(PIP) install --disable-pip-version-check \
		-r requirements.build.txt \
		-r requirements.txt \
		-r requirements.dev.txt \


dev-venv: venv-create dev-install


dev-flake8:
	$(PYTHON) -m flake8 data_ai_bot tests

dev-pylint:
	$(PYTHON) -m pylint data_ai_bot tests

dev-mypy:
	$(PYTHON) -m mypy --check-untyped-defs data_ai_bot tests

dev-lint: dev-flake8 dev-pylint dev-mypy


dev-unit-tests:
	$(PYTHON) -m pytest

dev-watch:
	$(PYTHON) -m pytest_watcher \
		--runner=$(VENV)/bin/python \
		. \
		-m pytest -vv $(PYTEST_WATCH_MODULES)


dev-test: dev-lint dev-unit-tests


dev-start-telemetry-server:
	$(PYTHON) -m phoenix.server.main serve

dev-start:
	CONFIG_FILE=config/agent.yaml \
		$(PYTHON) -m data_ai_bot

dev-start-local-config:
	CONFIG_FILE=config/local-agent.yaml \
		$(PYTHON) -m data_ai_bot

dev-start-with-telemetry:
	CONFIG_FILE=config/agent.yaml \
		OTLP_ENDPOINT=http://0.0.0.0:6006/v1/traces \
		$(PYTHON) -m data_ai_bot


dev-start-with-telemetry-local-config:
	CONFIG_FILE=config/local-agent.yaml \
		OTLP_ENDPOINT=http://0.0.0.0:6006/v1/traces \
		$(PYTHON) -m data_ai_bot


build:
	$(DOCKER_COMPOSE) build

flake8:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m flake8 data_ai_bot tests

pylint:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m pylint data_ai_bot tests

mypy:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m mypy --check-untyped-defs data_ai_bot tests

lint: flake8 pylint mypy


unit-tests:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m pytest


test: lint unit-tests


start:
	$(DOCKER_COMPOSE) up -d

start-mcp-server:
	$(DOCKER_COMPOSE) up -d mcp-server

logs:
	$(DOCKER_COMPOSE) logs -f

stop:
	$(DOCKER_COMPOSE) down

clean:
	$(DOCKER_COMPOSE) down -v


ci-build:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" build

ci-lint:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" lint


ci-unit-tests:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" unit-tests
