# FOCO — Migrações do Banco de Dados

## Situação da v0.3.1

O projeto ainda cria/ajusta parte do schema durante a inicialização. Esta correção
introduz o Alembic como mecanismo oficial de migração, mas mantém o comportamento
antigo temporariamente para não quebrar bancos de desenvolvimento existentes.

A migração inicial versionada já foi criada em:

```text
backend/migracoes/versoes/20260907_0001_estrutura_inicial_foco.py
```

Ela declara as tabelas centrais com nomes em português:

- `unidade_operacional`
- `viatura`
- `ocorrencia`
- `ocorrencia_viatura`

A migração `20260908_0002_lote_importacao.py` adiciona rastreabilidade de importação:

- `lote_importacao`
- `linha_importacao_rejeitada`
- `ocorrencia.id_lote_importacao`

A migração `20260908_0003_lote_legado_sejusp.py` cria um lote legado para ocorrências SEJUSP já existentes que ainda não possuíam `id_lote_importacao`.

## Passo 1 — aplicar a migração

```bash
cd backend
alembic upgrade head
```

## Passo 2 — validar alinhamento com os modelos

```bash
alembic check
```

## Passo 3 — executar testes

```bash
pytest -q
```

## Passo 4 — homologar PostgreSQL/PostGIS

Suba o banco:

```bash
docker compose up -d bd
```

Execute:

```sql
SELECT PostGIS_Version();
```

## Passo 5 — remover alteração automática no startup

Somente depois da migração inicial homologada, remover de `app/main.py`:

```python
Base.metadata.create_all(bind=engine)
garantir_colunas_incrementais(engine)
```

A partir daí, toda alteração de schema deve ser feita por migration.

## Regra

Nunca alterar manualmente o schema em produção sem migration versionada.
