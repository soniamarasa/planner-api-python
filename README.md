# Planner API

Backend do planner reescrito em Python com FastAPI, SQLAlchemy e PostgreSQL no Neon.

## Stack

- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL (Neon)
- JWT para autenticacao

## Executar

1. Instale as dependencias Python com `pip install -r requirements.txt`
2. Rode as migrations com `npm run db:migrate`
3. Suba a API com `npm start`

Documentacao interativa:

- `http://localhost:3001/docs`

Healthcheck:

- `http://localhost:3001/health`

## Seed de desenvolvimento

Execute `npm run seed` para criar um usuario demo e alguns itens iniciais.

Credenciais demo:

- email: `demo@planner.dev`
- senha: `12345678`

## Observacao

Arquivos antigos em Node.js podem existir temporariamente no repositorio como legado de migracao, mas o runtime atual da API e o schema do banco estao em Python.