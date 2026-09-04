# ADR-005 — Separação entre dados reais, históricos e DEMO

**Status:** Accepted

## Contexto
Alguns campos operacionais ainda não existem em todas as fontes.

## Decisão
Diferenciar explicitamente:
- REAL;
- HISTORICAL_AGGREGATE;
- DEMO.

## Regras
- DEMO nunca deve ser apresentado como real;
- totais históricos não devem ser decompostos artificialmente;
- dashboards devem indicar origem e cobertura.

## Consequências
- maior transparência;
- menor risco de interpretação;
- necessidade de metadados de origem.
