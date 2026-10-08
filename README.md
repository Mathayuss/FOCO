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

O arquivo `.env` deve definir `BD_SENHA` antes de subir o banco. A porta do
PostgreSQL fica disponível somente no host local (`127.0.0.1:5432`).

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

## Importação de planilhas

A tela de importações aceita CSV, XLS e XLSX de até 512 MB por padrão. CSV pode
estar em UTF-8 ou Windows-1252. Sempre execute a prévia antes da confirmação:
bloqueios estruturais impedem a gravação, enquanto problemas de linha permitem
importar somente o subconjunto válido e ficam registrados no lote.

As regras e equivalências SEJUSP estão em [API de importação](documentacao/arquitetura/API.md#6-importações).

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

## Testes da interface

Depois de instalar as dependencias do frontend e o Chromium:

```bash
pnpm --dir frontend exec playwright install --with-deps chromium
pnpm run test:frontend
```

A suite inicia um Vite separado, simula as chamadas da API e nao acessa o banco
operacional. Valida desktop, notebook e celular. Os detalhes de instalacao,
isolamento e relatorios estao em [testes frontend](documentacao/operacao/TESTES_FRONTEND.md).

## Desempenho do dashboard

O medidor somente leitura permite comparar tempos, consultas e hashes das
respostas sem modificar os dados importados:

```bash
docker compose exec -T servidor python -m scripts.medir_dashboard --repeticoes 7
```

Consulte [desempenho do dashboard](documentacao/operacao/DESEMPENHO_DASHBOARD.md)
para recortes, resultados observados e limites da medicao.

## Estrutura do projeto

```text
backend/   API FastAPI, serviços, modelos, schemas, dados e testes
frontend/  Aplicação React + TypeScript/Vite
documentacao/ Documentação organizada por área
```

A documentação principal está indexada em `documentacao/README.md`.
