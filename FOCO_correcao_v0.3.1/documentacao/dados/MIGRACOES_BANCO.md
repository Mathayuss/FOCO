# FOCO — Migrações do Banco de Dados

## Situação da v0.3.1

O projeto ainda cria/ajusta parte do schema durante a inicialização. Esta correção
introduz o Alembic como mecanismo oficial de migração, mas mantém o comportamento
antigo temporariamente para não quebrar bancos de desenvolvimento existentes.

## Passo 1 — gerar a primeira migração

Com o ambiente do backend instalado:

```bash
cd backend
alembic revision --autogenerate -m "estrutura inicial do FOCO"
```

Revise o arquivo gerado em:

```text
backend/migracoes/versoes/
```

## Passo 2 — testar em banco limpo

```bash
alembic upgrade head
pytest -q
```

## Passo 3 — homologar PostgreSQL/PostGIS

Suba o banco:

```bash
docker compose up -d bd
```

Execute:

```sql
SELECT PostGIS_Version();
```

## Passo 4 — remover alteração automática no startup

Somente depois da migração inicial homologada, remover de `app/main.py`:

```python
Base.metadata.create_all(bind=engine)
garantir_colunas_incrementais(engine)
```

A partir daí, toda alteração de schema deve ser feita por migration.

## Regra

Nunca alterar manualmente o schema em produção sem migration versionada.
