# FOCO-082 - Credencial exclusiva por instalacao

## Problema

Os modelos de ambiente distribuem placeholders intencionais, mas a primeira
instalacao ainda dependia da edicao manual e simultanea de `BD_SENHA` e
`DATABASE_URL`. Erros nessa etapa podiam manter uma senha conhecida ou criar
configuracoes divergentes.

## Solucao

O comando abaixo prepara o ambiente antes da primeira inicializacao:

```bash
python3 infraestrutura/scripts/preparar_ambiente.py
```

O bootstrap:

- gera 256 bits aleatorios com a biblioteca padrao do sistema;
- atualiza senha e URL de conexao em conjunto;
- grava `.env` com permissao `0600` sem imprimir o segredo;
- usa escrita atomica e nao sobrescreve um destino concorrente;
- rejeita modelo incompleto e destino simbolico;
- valida e preserva uma configuracao existente coerente;
- bloqueia senha de exemplo ou URL divergente em arquivo existente.

O comando nao e um mecanismo de rotacao. Alterar apenas `.env` depois que o
volume foi inicializado dessincroniza PostgreSQL e API; a rotacao deve atualizar
o papel no banco e a configuracao como uma unica operacao controlada.

## Validacao

```bash
python3 -m unittest infraestrutura.tests.test_preparar_ambiente -v
python3 -m unittest discover -s infraestrutura/tests -v
```

O pacote de release tambem verifica a presenca do script e continua excluindo
o `.env` real.

## Criterio de aceite

Uma instalacao limpa recebe credencial exclusiva e configuracao coerente antes
do primeiro `docker compose up`; repeticoes preservam o ambiente existente e
nenhum segredo aparece na saida do comando ou no pacote distribuido.
