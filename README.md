# Planner API

Backend do planner reescrito em Python com FastAPI, SQLAlchemy e PostgreSQL no Neon.

## Visão Geral

Esta API é responsável pela autenticação de usuários e pelo gerenciamento dos itens do planner.

O projeto foi migrado da implementação original em Node.js para uma base moderna em Python, com foco em manutenção, escalabilidade e evolução futura.

## Migração

Este repositório é a continuidade oficial do backend do planner em Python.

Repositório antigo em Node.js:

- https://github.com/soniamarasa/planner-api

## Stack

- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL (Neon)
- JWT para autenticação

## Executar

Crie e ative um ambiente virtual e instale as dependências:

```bash
# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Com o ambiente ativo, rode as migrations e suba a API:

```bash
# migrations
python -m alembic upgrade head

# API (desenvolvimento, com reload)
python -m uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

### Atalhos via Make (opcional)

Se você tiver o `make` instalado, há atalhos equivalentes:

```bash
make install   # pip install -r requirements.txt
make migrate   # alembic upgrade head
make run       # uvicorn ... --reload
make run-prod  # uvicorn ... (sem reload)
make seed      # popula dados de desenvolvimento
make           # lista todos os comandos
```

Documentação interativa:

- `http://localhost:3001/docs`

Healthcheck:

- `http://localhost:3001/health`

## Seed de Desenvolvimento

Execute `python -m app.scripts.seed` (ou `make seed`) para criar um usuário demo e alguns itens iniciais.

Credenciais demo:

- email: `demo@planner.dev`
- senha: `12345678`