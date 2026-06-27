# Planner API - atalhos de desenvolvimento
#
# Use o Python do ambiente virtual ativo. Para sobrescrever:
#   make run PYTHON=.venv/Scripts/python.exe   (Windows)
#   make run PYTHON=.venv/bin/python            (Linux/macOS)

PYTHON ?= python
HOST ?= 0.0.0.0
PORT ?= 3001

.DEFAULT_GOAL := help

.PHONY: help install run dev run-prod migrate revision seed

help: ## Lista os comandos disponiveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Instala as dependencias Python
	$(PYTHON) -m pip install -r requirements.txt

run dev: ## Sobe a API em modo desenvolvimento (reload)
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT) --reload

run-prod: ## Sobe a API em modo producao (sem reload)
	$(PYTHON) -m uvicorn app.main:app --host $(HOST) --port $(PORT)

migrate: ## Aplica as migrations (alembic upgrade head)
	$(PYTHON) -m alembic upgrade head

revision: ## Gera uma nova migration autogenerate
	$(PYTHON) -m alembic revision --autogenerate -m "update schema"

seed: ## Popula o banco com dados de desenvolvimento
	$(PYTHON) -m app.scripts.seed
