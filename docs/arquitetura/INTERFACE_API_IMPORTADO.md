# FOCO — Interface da API

## Prefixo

```text
/api/v1
```

## Ocorrências

```http
GET /api/v1/ocorrencias
GET /api/v1/ocorrencias/{id}
```

## Análises

```http
GET /api/v1/analises/resumo
GET /api/v1/analises/evolucao
GET /api/v1/analises/tipificacao
GET /api/v1/analises/temporal
GET /api/v1/analises/territorio
GET /api/v1/analises/viaturas
GET /api/v1/analises/sla
```

## Importações

```http
POST /api/v1/importacoes/pre-visualizar
POST /api/v1/importacoes
GET /api/v1/importacoes/{id}
```

## Integrações

```http
GET /api/v1/integracoes
POST /api/v1/integracoes/{id}/sincronizar
GET /api/v1/integracoes/{id}/situacao
```

## Exceções de nomenclatura

Rotas técnicas exigidas por ferramentas externas podem permanecer em inglês, por exemplo:

```text
/health
/metrics
```
