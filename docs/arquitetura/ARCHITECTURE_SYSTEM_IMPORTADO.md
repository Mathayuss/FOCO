# FOCO — Arquitetura do Sistema

## Objetivo

Definir a arquitetura técnica oficial do FOCO — Ferramenta Operacional de Consolidação de Ocorrências.

## Tecnologias

### Interface
- React
- TypeScript
- Apache ECharts
- MapLibre ou Leaflet

### Servidor
- Python
- FastAPI
- SQLAlchemy
- Alembic

### Banco de dados
- PostgreSQL
- PostGIS

### Infraestrutura
- Docker
- Nginx

## Princípios

- separação de responsabilidades;
- API como contrato central;
- dados rastreáveis;
- arquitetura modular;
- segurança por padrão;
- evolução incremental;
- documentação em português;
- nomes técnicos criados pela equipe em português.

## Organização sugerida

```text
interface/
├── paginas/
├── componentes/
│   ├── graficos/
│   ├── filtros/
│   ├── mapas/
│   └── tabelas/
├── servicos/
├── ganchos/
├── tipos/
├── layouts/
└── utilitarios/

servidor/
├── aplicacao/
│   ├── api/
│   ├── nucleo/
│   ├── modelos/
│   ├── esquemas/
│   ├── repositorios/
│   ├── servicos/
│   ├── integracoes/
│   ├── importacoes/
│   ├── seguranca/
│   └── banco_de_dados/
├── migracoes/
└── testes/
```

## Fluxo da regra de negócio

```text
Rota
  ↓
Esquema
  ↓
Serviço
  ↓
Repositório
  ↓
Banco de dados
```

## Referências obrigatórias

Consultar também:

- `IDENTIDADE_VISUAL.md`
- `AREAS_OPERACIONAIS.md`
- `MODELO_DE_DADOS.md`
- `SEGURANCA.md`
- `ROTEIRO_DE_VERSOES.md`
- `docs/adr/`
