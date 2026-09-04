# ADR-004 — Arquitetura API-first

**Status:** Accepted

## Contexto
O FOCO terá múltiplos consumidores: web, sala de situação e integrações.

## Decisão
Centralizar regras relevantes no backend e expô-las por API.

## Motivos
- desacoplamento;
- reutilização;
- testabilidade;
- consistência.

## Consequências
- versionamento;
- contratos estáveis;
- OpenAPI;
- cuidado com compatibilidade.
