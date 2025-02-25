#!/usr/bin/make -f

DOCKER_COMPOSE_DEV = docker compose
DOCKER_COMPOSE_CI = docker compose -f docker-compose.yml
DOCKER_COMPOSE = $(DOCKER_COMPOSE_DEV)

VENV = venv
PIP = $(VENV)/bin/pip
PYTHON = $(VENV)/bin/python


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
	$(PYTHON) -m flake8 data_ai_bot

dev-pylint:
	$(PYTHON) -m pylint data_ai_bot

dev-mypy:
	$(PYTHON) -m mypy --check-untyped-defs data_ai_bot

dev-lint: dev-flake8 dev-pylint dev-mypy


dev-start:
	$(PYTHON) -m data_ai_bot


build:
	$(DOCKER_COMPOSE) build

flake8:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m flake8 data_ai_bot

pylint:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m pylint data_ai_bot

mypy:
	$(DOCKER_COMPOSE) run --rm data-ai-bot \
		python3 -m mypy --check-untyped-defs data_ai_bot

lint: flake8 pylint mypy


start:
	$(DOCKER_COMPOSE) up -d

logs:
	$(DOCKER_COMPOSE) logs -f


ci-build:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" build

ci-lint:
	$(MAKE) DOCKER_COMPOSE="$(DOCKER_COMPOSE_CI)" lint
