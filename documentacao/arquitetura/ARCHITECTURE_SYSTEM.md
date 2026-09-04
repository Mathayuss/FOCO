# FOCO — Arquitetura do Sistema

## 1. Objetivo
Este documento descreve a arquitetura de referência do **FOCO — Ferramenta Operacional de Consolidação de Ocorrências**.

O FOCO é uma plataforma de inteligência operacional destinada à consolidação, análise e visualização de dados de ocorrências provenientes de diferentes fontes.

A arquitetura deve suportar dashboards analíticos, filtros cruzados, importação manual, integrações automáticas, georreferenciamento, análise de viaturas, indicadores de SLA, rastreabilidade, segurança e evolução futura para alertas e inteligência preditiva.

## 2. Princípios arquiteturais
1. Separação de responsabilidades entre frontend, backend, persistência e integrações.
2. API-first.
3. Dados rastreáveis e auditáveis.
4. Arquitetura modular.
5. Evolução incremental conforme roadmap.
6. Segurança por padrão.
7. Migrations obrigatórias para mudanças de schema.
8. Dados demonstrativos claramente identificados.
9. Sem feature creep.
10. Observabilidade desde cedo.

## 3. Stack principal
### Frontend
- React
- TypeScript
- Apache ECharts
- MapLibre ou Leaflet

### Backend
- Python
- FastAPI
- SQLAlchemy
- Alembic

### Banco
- PostgreSQL
- PostGIS

### Infraestrutura
- Docker
- Docker Compose
- Nginx

### Futuro
- Redis quando necessário.
- Worker assíncrono para integrações/importações volumosas.
- AD/LDAP/OIDC para autenticação institucional.

## 4. Visão de alto nível
```text
Sistemas de origem
    │
    ├── API
    ├── Banco read-only
    ├── CSV/XLSX
    └── Outras integrações
            │
            ▼
      Camada de ingestão
            │
            ▼
    Staging / validação
            │
            ▼
 Normalização / deduplicação
            │
            ▼
   PostgreSQL + PostGIS
            │
            ▼
      FastAPI / Serviços
            │
       ┌────┼─────┐
       ▼    ▼     ▼
      BI   Mapas  Sala
                  de Situação
```

## 5. Frontend
Responsabilidades:
- renderizar dashboards;
- aplicar filtros globais;
- exibir gráficos e mapas;
- permitir drill-down;
- tratar loading, erro e estado vazio;
- exibir filtros ativos;
- suportar tela cheia e sala de situação.

Não deve:
- calcular SLA complexo;
- executar geoprocessamento pesado;
- implementar deduplicação;
- concentrar regra de negócio.

Estrutura sugerida:
```text
frontend/
├── src/
│   ├── app/
│   ├── pages/
│   ├── components/
│   │   ├── charts/
│   │   ├── filters/
│   │   ├── maps/
│   │   └── tables/
│   ├── services/
│   ├── hooks/
│   ├── types/
│   ├── layouts/
│   └── utils/
```

## 6. Backend
Responsabilidades:
- API;
- validação;
- regras de negócio;
- SLA;
- agregações;
- importação;
- integrações;
- normalização;
- deduplicação;
- segurança;
- auditoria.

Estrutura:
```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── integrations/
│   ├── imports/
│   ├── security/
│   └── database/
├── migrations/
└── tests/
```

Fluxo preferencial:
```text
Route
  ↓
Schema
  ↓
Service
  ↓
Repository
  ↓
Database
```

## 7. Banco de dados
O banco principal será PostgreSQL.

PostGIS será utilizado para municípios, regiões, bairros, pontos de ocorrência, distâncias, interseções e consultas espaciais.

Regras:
- migrations obrigatórias;
- índices adequados;
- índices espaciais quando necessário;
- integridade referencial;
- referência à fonte de origem preservada.

## 8. Importação
Fluxo:
```text
Upload
  ↓
Staging
  ↓
Validação
  ↓
Mapeamento
  ↓
Normalização
  ↓
Deduplicação
  ↓
Consolidação
```

Erros críticos não devem ser ignorados silenciosamente.

## 9. Dados demonstrativos
Tipos:
- REAL
- HISTORICAL_AGGREGATE
- DEMO

Nunca misturar DEMO com dado real sem identificação explícita.

## 10. Escalabilidade
Adicionar apenas quando necessário:
- Redis;
- filas;
- workers;
- materialized views;
- cache;
- pré-agregações;
- particionamento.

## 11. Observabilidade
Desde as primeiras versões:
- health check;
- logs estruturados;
- request ID;
- erros;
- tempo de resposta.

Futuro:
- Prometheus;
- Grafana;
- alertas;
- tracing.

## 12. Decisões arquiteturais
Decisões relevantes devem ser registradas em `documentacao/adr/`.
