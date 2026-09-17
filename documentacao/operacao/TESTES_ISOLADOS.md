# Testes isolados do backend

O pytest configura o banco antes de importar a aplicacao. `DATABASE_URL` e
`AMBIENTE` herdados do host, do container ou do `.env` nao sao usados pelos
testes. Cada teste executa a cadeia Alembic para criar tabelas vazias;
o schema descartavel e removido ao terminar e o cache analitico e invalidado.

## Execucao rapida com SQLite

Na pasta `backend`, execute `python -m pytest -q`. Um arquivo SQLite e criado
em diretorio temporario exclusivo e removido ao terminar. As chaves
estrangeiras ficam habilitadas. Tambem e seguro executar:

```sh
docker compose exec -T servidor python -m pytest -q
```

Essa execucao usa o SQLite temporario do processo pytest, nao o PostgreSQL
configurado no container do servidor. Os testes nao dependem de dados SEJUSP
previamente importados.

## Integracao com PostgreSQL/PostGIS

Na raiz do projeto:

```sh
docker compose -f compose.testes.yml up --abort-on-container-exit --exit-code-from testes
docker compose -f compose.testes.yml down
```

O projeto Compose `foco-testes` usa rede interna exclusiva, sem portas
publicadas, sem `.env` da aplicacao e com dados PostgreSQL em tmpfs. O modo
`--postgres-testes` conecta somente a `bd-testes`, banco `foco_testes`.
Nao combine esse arquivo com o Compose operacional. O banco de testes usa
autenticacao trust apenas nessa rede descartavel; esta configuracao nao
deve ser usada pelo ambiente operacional.

Se a imagem `foco-servidor` ainda nao existir, execute antes
`docker compose -f compose.testes.yml build testes`.

Execute `down` mesmo quando a suite falhar. Nao use `-v` no Compose
operacional para limpar testes. A suite valida APIs, a cadeia de migrations
e sua correspondencia com os modelos, a preservacao de dados na reparacao
da chave do lote e a rejeicao de bancos sem revisao ou atrasados no startup.
