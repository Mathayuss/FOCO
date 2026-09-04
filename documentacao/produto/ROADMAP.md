# FOCO — Roadmap Oficial

## 1. Prioridades
### P0 — Crítico
Bloqueia a versão ou implantação.

### P1 — Importante
Entrega valor relevante, mas não bloqueia o núcleo.

### P2 — Evolutivo
Melhoria futura.

## 2. Versões

### v0.2 — Base estrutural
Status: base inicial concluída.
- React + TypeScript
- FastAPI
- PostgreSQL/PostGIS preparado
- Docker
- estrutura inicial de ocorrências
- estrutura inicial de viaturas
- identidade FOCO
- testes básicos

### v0.3 — BI funcional
Prioridade: P0.

Escopo:
- Visão Geral;
- filtros globais;
- período;
- município;
- unidade;
- tipo;
- subtipo;
- turno;
- Evolução;
- Tipificação;
- Temporal;
- comparação entre períodos;
- filtros cruzados;
- consumo consistente da API.

Aceite:
- responder quantas ocorrências existem no período;
- visualizar evolução;
- identificar principais tipos;
- identificar quando ocorrem;
- saber município/unidade em análise;
- saber filtros ativos.

### v0.4 — Dados e importação
Prioridade: P0.

Escopo:
- CSV/XLSX;
- staging;
- validação;
- mapeamento;
- preview;
- erros por linha;
- duplicidades;
- lotes;
- histórico;
- qualidade de dados.

### v0.5 — Território e GIS
Prioridade: P0.

Escopo:
- PostGIS;
- municípios;
- pontos;
- heatmap;
- clusters;
- ranking municipal;
- filtros geográficos;
- análise municipal;
- análise intramunicipal quando houver dados.

### v0.6 — Viaturas e Unidades
Prioridade: P0.

Escopo:
- ocorrência com múltiplas VTR;
- tipo de viatura;
- unidade;
- horários por VTR;
- dashboard de viaturas;
- dashboard de unidades.

### v0.7 — SLA operacional
Prioridade: P0.

Escopo:
- despacho;
- mobilização;
- deslocamento;
- tempo-resposta;
- atendimento;
- retorno;
- ciclo operacional;
- indisponibilidade;
- média;
- mediana;
- P75;
- P90;
- P95;
- cobertura do indicador.

### v0.8 — Integrações automáticas
Prioridade: P0/P1.

Escopo:
- conectores;
- jobs;
- retry;
- idempotência;
- logs;
- status de sincronização;
- falhas.

### v0.9 — Segurança e Administração
Prioridade: P0 antes da produção.

Escopo:
- autenticação;
- AD/LDAP/OIDC;
- RBAC;
- auditoria;
- HTTPS;
- proteção da API.

### v0.10 — Sala de Situação
Prioridade: P1.

Escopo:
- tela cheia;
- URLs individuais;
- carrossel;
- playlists;
- modo TV;
- atualização automática.

### v0.11 — Performance e Relatórios
Prioridade: P1.

Escopo:
- otimização;
- índices;
- materialized views;
- cache;
- CSV/XLSX/PDF;
- relatórios.

### v0.12 — Homologação
Prioridade: P0.

Objetivo:
- estabilização;
- UAT;
- testes;
- correções;
- revisão UX;
- documentação.

### v1.0 — Produção
Requisitos mínimos:
- BI principal;
- dados confiáveis;
- importação;
- território;
- viaturas;
- unidades;
- SLA;
- integrações;
- segurança;
- auditoria;
- backup;
- restore testado;
- documentação;
- monitoramento.

## 3. Pós 1.0
### v1.1 — Alertas
### v1.2 — Anomalias
### v1.3 — Previsão de demanda
### v1.4 — Planejamento operacional

## 4. Regra de avanço
Uma versão não deve ser considerada concluída enquanto seus critérios P0 não forem atendidos.
