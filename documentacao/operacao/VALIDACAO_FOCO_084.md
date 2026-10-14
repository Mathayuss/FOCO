# FOCO-084 - Smoke test BI operacional

## Uso

Na maquina que hospeda a release ativa:

```bash
python3 infraestrutura/scripts/verificar_bi_operacional.py
```

Para apontar para outro host, use o prefixo da API:

```bash
python3 infraestrutura/scripts/verificar_bi_operacional.py \
  --url https://host-institucional/api/v1
```

## Escopo

O comando executa somente requisicoes HTTP `GET`. Nao envia arquivos, nao grava
no banco e nao modifica filtros persistidos. Valida:

- saude da API e conectividade com o banco;
- escopo SEJUSP importado e disponibilidade das seis dimensoes;
- periodo mensal mais recente com cobertura no mesmo mes do ano anterior, total
  e soma da evolucao mensal;
- consistencia dos filtros aplicados nos paineis;
- comparacao com o mesmo periodo do ano anterior;
- igualdade entre os endpoints individuais de visao geral/evolucao e o
  dashboard consolidado.

A comparacao ausente e sinalizada como falha, pois a aplicacao nao consegue
demonstrar o criterio de comparacao anual no recorte ativo.

## Execucao inicial

Em 13/10/2026, a verificacao local terminou com `status=ok` no periodo
`2026-06`, que foi o mes mais recente com cobertura equivalente nos dois anos.
Todas as cinco verificacoes passaram. Nenhuma contagem, linha, municipio ou
unidade foi impressa, e nenhum dado foi alterado.

## Privacidade

A saida mostra somente o periodo validado e os nomes das verificacoes. Totais,
localidades, unidades e registros da base institucional nao sao impressos.
Respostas sao limitadas a 16 MiB e cada requisicao possui timeout configuravel.

O script usa HTTP em loopback por padrao. Ao informar outro host, use HTTPS.
