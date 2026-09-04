# Arquitetura — FOCO MVP

```text
┌────────────────────────────────────────────────────┐
│ FOCO Web                                           │
│ React + TypeScript                                 │
│ Dashboard · ECharts · Leaflet · Filtros            │
└───────────────────────┬────────────────────────────┘
                        │ REST/JSON
                        ▼
┌────────────────────────────────────────────────────┐
│ FOCO API                                           │
│ FastAPI / Python                                   │
│ API v1 · Regras · SLA · Importação · Integrações   │
└───────────────────────┬────────────────────────────┘
                        │ SQLAlchemy
                        ▼
┌────────────────────────────────────────────────────┐
│ PostgreSQL + PostGIS                               │
│ Ocorrências · VTR · Unidades · Território          │
└────────────────────────────────────────────────────┘
```

## Princípios

1. **Fonte canônica:** dados de sistemas distintos são normalizados para um modelo comum.
2. **Rastreabilidade:** o dado consolidado preserva sua origem.
3. **Separação entre fato e demonstração:** dados sintéticos nunca são apresentados como institucionais.
4. **API-first:** frontend, integrações e futuras telas de Sala de Situação consomem contratos de API versionados.
5. **Geoespacial nativo:** PostGIS é a base para municípios, regiões, bairros, hotspots e distâncias.
6. **Evolução modular:** dashboards podem crescer sem acoplar lógica analítica ao frontend.

## Estratégia de dados nesta versão

O histórico disponível hoje é agregado. Ele permanece em fixture separada para não inventar ocorrências individuais que não existem na fonte.

Em paralelo, o banco já possui o modelo canônico para a futura ingestão de ocorrências individuais. Uma pequena massa `DEMO` valida SLA, tempos e relacionamento de viaturas sem se passar por dado institucional real.
