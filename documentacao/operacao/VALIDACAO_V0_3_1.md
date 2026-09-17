# Validacao incremental - 2026-09-17

## Versao analisada

FOCO v0.3, pacote v0.3.1.

## Status

APROVADO COM RESSALVAS para este incremento. Nao representa homologacao
completa da v0.3 nem aprovacao para producao institucional.

## Resumo executivo

Os paineis passam a carregar uma resposta consolidada, sem alterar as regras
dos indicadores ou retirar os endpoints atuais. A API valida os filtros uma
vez e compartilha as linhas SEJUSP durante a requisicao. A inicializacao usa
Alembic; os testes nao acessam o banco operacional. Foi corrigido o overflow
do seletor de tipificacao observado em notebook.

## Problemas criticos

Nenhum bloqueador observado no escopo testado.

## Problemas altos

BUG corrigido: a reparacao local da migration 0005 poderia perder colunas.
O teste agora verifica a preservacao das colunas e dos dados em SQLite e
PostgreSQL. Nao ha novo problema alto identificado neste incremento.

## Problemas medios

- DIVIDA TECNICA: os indicadores continuam agregando a base em memoria.
  O snapshot reduz leituras repetidas, mas nao substitui agregacao SQL.
- DIVIDA TECNICA: a verificacao de navegador foi executada com Playwright
  temporario; ainda nao ha uma suite frontend integrada ao repositorio/CI.
- LIMITACAO PRESERVADA: o SLA permanece global. A resposta consolidada
  nao apresenta esse campo como indicador dos filtros selecionados.

## Problemas baixos

O TestClient emite aviso de depreciacao do AnyIO. Os testes passaram;
a atualizacao deve respeitar a compatibilidade entre as dependencias.

## Seguranca

Filtros invalidos e fontes removidas retornam HTTP 400 no novo endpoint.
Nao foram adicionados uploads, SQL interpolado ou novas credenciais.
Arquivos .env, bancos locais e backups ficam fora da imagem do backend.
Nao foi realizada auditoria completa de vulnerabilidades neste incremento.
Autenticacao institucional continua pertencendo a v0.9; a implantacao atual
deve permanecer em rede controlada.

## Backend

Novo endpoint tipado `/api/v1/analytics/dashboard`, com logica no servico.
Endpoints individuais mantidos e comparados por teste com a resposta nova.
O snapshot da sessao e liberado mesmo em caso de erro. Uma assinatura do
dataset por chamada consolidada, comprovada por teste.

## Frontend

Visao Geral e paineis analiticos usam uma chamada consolidada. Requisicoes
substituidas sao canceladas e respostas antigas ignoradas. Cancelar o fetch
nao garante interromper um calculo que ja comecou no backend.

## Banco de dados

Alembic e a unica autoridade de schema. A API recusa revisoes ausentes ou
desatualizadas. A revisao operacional permanece em 20260914_0005;
este incremento de BI nao exige migration nova.

## UX/UI

Filtros por periodo e municipio aplicados, mantidos ao navegar para Evolucao.
Cancelamento validado com atraso artificial da requisicao substituida.
Screenshots e ausencia de overflow horizontal verificados em 1920x1080,
1366x768 e 390x844, sem erros JavaScript de pagina.
Tipificacoes extensas nao ampliam mais o seletor alem da area disponivel.

## Testes

- SQLite descartavel: 51 aprovados, 0 falhos.
- PostgreSQL/PostGIS descartavel: 51 aprovados, 0 falhos.
- Build TypeScript/Vite aprovado.
- Oito testes novos: equivalencia dos paineis, todos os filtros combinados,
  base vazia, filtros invalidos, consulta unica da assinatura e limpeza apos erro.
- Playwright: carga real, filtros, navegacao, cancelamento e tres viewports aprovados.
- Cobertura percentual nao medida.

## Aderencia ao roadmap

IMPLEMENTADO neste incremento: integracao consolidada dos dashboards com a
API e melhoria de confiabilidade dos filtros globais.
PARCIAL: homologacao de todos os criterios de aceite da v0.3.
NAO IMPLEMENTADO neste incremento: funcionalidades de versoes futuras.

## Divida tecnica

Automacao persistente de testes frontend; agregacoes em memoria; etapa unica
de migration antes de multiplas replicas, caso essa arquitetura seja adotada.

## Recomendacoes para a equipe

Priorizar a suite frontend de filtros cruzados e medir tempos de carregamento
antes de substituir agregacoes existentes. Confirmar os criterios de aceite
com usuarios, sem declarar a versao pronta apenas pelos testes tecnicos.

## Backlog proposto

### FOCO-041

Titulo: Automatizar a regressao dos dashboards no frontend.
Descricao: Integrar os testes de filtros, navegacao e respostas substituidas.
Prioridade: Media.
Versao: v0.3.
Area: Frontend / qualidade.
Arquivos envolvidos: frontend/package.json, frontend/tests/, frontend/playwright.config.ts.
Criterio de aceite: Um comando reproduz os fluxos em desktop e notebook,
sem dados demonstrativos apresentados como reais nem acesso de escrita ao banco operacional.

### FOCO-042

Titulo: Medir e reduzir agregacoes repetidas do dashboard.
Descricao: Registrar tempos e consultas com bases representativas e otimizar
os pontos comprovados, mantendo equivalencia dos resultados e cobertura dos dados.
Prioridade: Media.
Versao: v0.3.
Area: Backend / BI.
Arquivos envolvidos: backend/app/services/sejusp_analytics_service.py,
backend/app/services/dashboard_service.py, backend/tests/test_dashboard.py.
Criterio de aceite: Resultados equivalentes aos endpoints atuais e medidas
reproduziveis de melhoria sem alterar regras de negocio.
