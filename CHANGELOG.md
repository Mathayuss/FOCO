# Changelog

## v0.3.1 - 2026-09-17

### BI

- Dashboard consolidado em `/api/v1/analytics/dashboard`, preservando os endpoints individuais.
- Mesma leitura de linhas SEJUSP para os paineis de uma requisicao, com validacao unica de filtros.
- Visao Geral e paineis analiticos usam a resposta consolidada.
- Cancelamento de carregamentos substituidos ao trocar filtros ou sair do painel.
- Seletor de tipificacao limitado a area disponivel para evitar overflow em notebook e mobile.

### Confiabilidade e operacao

- Alembic como unico responsavel por criar e alterar o schema.
- Migrations antes do Uvicorn no container e validacao da revisao no startup da API.
- Reparacao idempotente da migration 0005 sem perda de colunas ou registros.
- Testes isolados em SQLite temporario e PostgreSQL/PostGIS descartavel, usando migrations reais.
- Healthcheck verifica a disponibilidade do banco.
- Politica de reinicio dos containers e unidade systemd para inicializacao automatica.
- Bancos locais, backups e arquivos de ambiente excluidos da imagem do backend.
- Limite de importacao configuravel e validado no backend e frontend.

### Validacao

- 51 testes aprovados em SQLite e 51 em PostgreSQL/PostGIS.
- Build TypeScript/Vite aprovado.
- Testes de equivalencia entre dashboard consolidado e endpoints individuais,
  base vazia, filtros invalidos e liberacao do snapshot apos erros.

Esta entrega nao declara a v0.3 homologada nem antecipa novos indicadores de SLA.
