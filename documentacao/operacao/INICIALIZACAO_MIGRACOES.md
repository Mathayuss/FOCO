# Inicializacao com migrations

As tabelas do FOCO sao criadas e alteradas pelo Alembic. O lifespan da API
verifica a revisao aplicada e recusa a inicializacao quando o banco esta
sem revisao ou atrasado; ele nao cria tabelas nem executa ALTER TABLE.

## Docker e servico

A imagem do backend executa `sh iniciar.sh`: primeiro
`python -m alembic upgrade head`, depois o Uvicorn. Se uma migration falhar,
a API nao inicia. O mesmo fluxo e usado pelo `foco.service` e no boot.

Ao atualizar esse fluxo, reconstrua a imagem:

```sh
docker compose build servidor
systemctl restart foco.service
```

Se executar apenas `docker compose restart servidor`, a imagem antiga e
mantida. Para atualizar somente o backend depois do build, execute
`docker compose up -d --no-deps servidor`.

## Execucao local

Na pasta backend:

```sh
python -m alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`sh iniciar.sh` executa os dois comandos na sequencia.

## Bancos legados

Um banco com tabelas existentes mas sem `alembic_version` precisa de
auditoria e baseline antes de usar este fluxo. Nao aplicar `stamp head`
automaticamente: ele registra uma revisao sem executar ou validar o schema.
Preserve um backup e siga o procedimento em `documentacao/dados/MIGRACOES_BANCO.md`.

O PostgreSQL existente do FOCO ja estava registrado em `20260914_0005`.
Esta mudanca nao exige nova revisao de schema. A reparacao idempotente da
0005 preserva as colunas da ocorrencia e mantem em downgrade os indices
e a chave do lote que pertencem originalmente as revisoes 0001 e 0002.

## Testes

A fixture isolada executa `upgrade head` antes de cada teste. A suite
valida o schema com `alembic check`, a reparacao com dados existentes e
a rejeicao de revisoes ausentes ou atrasadas. Consulte `TESTES_ISOLADOS.md`.

O container atual e unico. Para executar migrations automaticamente em
varias replicas, use uma etapa unica de migration antes de iniciar as APIs.
