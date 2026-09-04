# ADR-002 — PostgreSQL + PostGIS

**Status:** Accepted

## Contexto
O FOCO precisa armazenar ocorrências, unidades, viaturas, municípios, coordenadas e geometrias.

## Decisão
Utilizar PostgreSQL como banco principal e PostGIS como extensão geoespacial.

## Motivos
- robustez;
- integridade;
- SQL;
- geoprocessamento;
- índices espaciais;
- integração com Python.

## Consequências
- migrations obrigatórias;
- administração PostgreSQL;
- modelagem geográfica correta;
- definição de SRID.
