# FOCO - Ferramenta Operacional de Consolidacao de Ocorrencias

MVP com backend FastAPI e frontend React/Vite para dashboard de ocorrencias. A v0.3 prioriza BI funcional com Visao Geral, Evolucao, Tipificacao, Temporal, Territorio, Unidades, Qualidade, filtros globais persistidos e cruzados, comparacao entre periodos e importacao CSV/XLS/XLSX. Os paineis usam apenas dados SEJUSP importados, sem dados demonstrativos ou historicos consolidados.

## Rodando localmente

Primeiro, copie o exemplo de ambiente:

```bash
cp .env.example .env
```

Atalhos a partir da raiz do repositório:

```bash
pnpm run backend:dev
pnpm run frontend:dev
pnpm run test
pnpm run build
```

Backend local (SQLite, para desenvolvimento leve):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m alembic upgrade head
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Docker completo com PostgreSQL/PostGIS:

```bash
docker compose up --build
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

Observacao: executar o backend a partir de `backend/` usa SQLite local. Executar pela raiz com `docker compose` usa `./.env` e aponta para o PostgreSQL/PostGIS do servico `bd`.


Os testes usam bancos descartaveis, sem herdar a conexao operacional. Para validar no PostgreSQL/PostGIS:

```bash
docker compose -f compose.testes.yml up --abort-on-container-exit --exit-code-from testes
docker compose -f compose.testes.yml down
```

Consulte [testes isolados](documentacao/operacao/TESTES_ISOLADOS.md),
[inicializacao com migrations](documentacao/operacao/INICIALIZACAO_MIGRACOES.md)
e [servico Docker](documentacao/operacao/SERVICO_DOCKER.md).

## Estrutura do projeto

```text
backend/   API FastAPI, serviços, modelos, schemas, dados e testes
frontend/  Aplicação React + TypeScript/Vite
documentacao/ Documentação organizada por área
```

A documentação principal está indexada em `documentacao/README.md`.
