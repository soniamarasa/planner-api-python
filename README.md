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

1. Instale as dependências Python com `pip install -r requirements.txt`
2. Rode as migrations com `npm run db:migrate`
3. Suba a API com `npm start`

Documentação interativa:

- `http://localhost:3001/docs`

Healthcheck:

- `http://localhost:3001/health`

## Seed de Desenvolvimento

Execute `npm run seed` para criar um usuário demo e alguns itens iniciais.

Credenciais demo:

- email: `demo@planner.dev`
- senha: `12345678`