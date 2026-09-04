# ADR-001 — Python + FastAPI

**Status:** Accepted

## Contexto
O FOCO possui forte componente de ingestão, ETL, análise, integração, geoprocessamento e futura inteligência analítica.

## Decisão
Utilizar Python no backend e FastAPI como framework HTTP.

## Motivos
- ecossistema de dados;
- Pydantic;
- OpenAPI automática;
- desenvolvimento rápido;
- integração com PostgreSQL.

## Alternativas
- ASP.NET Core;
- Node.js.

## Consequências
Positivas:
- rapidez;
- integração;
- forte ecossistema analítico.

Cuidados:
- manter tipagem;
- evitar lógica nas rotas;
- testar;
- controlar dependências.
