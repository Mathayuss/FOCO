# FOCO - Ferramenta Operacional de Consolidacao de Ocorrencias

MVP com backend FastAPI e frontend React/Vite para dashboard de ocorrencias. A v0.3 prioriza BI funcional com Visao Geral, Evolucao, Tipificacao, Temporal, Territorio, Unidades, Qualidade, filtros globais persistidos, filtros por periodo e tipificacao via API, filtros dimensionais consolidados, comparativo temporal 2025 x 2026, SLA demonstrativo identificado como demo e preview seguro de importacao CSV.

## Rodando localmente

Backend:

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
COREPACK_ENABLE_PROJECT_SPEC=0 pnpm install
COREPACK_ENABLE_PROJECT_SPEC=0 pnpm run dev --host 0.0.0.0
```

URLs:

- Frontend: http://localhost:5173
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

## Testes

```bash
cd backend
.venv/bin/pytest -q
```

Observacao: executar o backend a partir de `backend/` usa SQLite local. Executar pela raiz le `./.env`, que aponta para PostgreSQL no servico Docker `db`.


## Estrutura do projeto

```text
backend/   API FastAPI, serviços, modelos, schemas, dados e testes
frontend/  Aplicação React + TypeScript/Vite
documentacao/ Documentação organizada por área
```

A documentação principal está indexada em `documentacao/README.md`.
