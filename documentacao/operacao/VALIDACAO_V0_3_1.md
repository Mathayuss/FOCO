# Validacao incremental - 2026-09-18

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

O incremento FOCO-042 reutiliza periodos, recortes e metadados por requisicao,
com serie mensal agrupada em uma passagem. Na base de 38.520 ocorrencias,
a mediana local do servico caiu de 500,90 para 138,68 ms. Os hashes das respostas
internas permaneceram iguais no recorte completo e em fevereiro/2025.
Consulte DESEMPENHO_DASHBOARD.md para metodologia e limites.

FOCO-044: ativado o bind do banco em 127.0.0.1:5432, mantendo o volume
foco_dados_postgis. Backup privado gerado antes da recriacao, API reconectada
e dados preservados. Um verificador somente leitura distingue configuracao
resolvida e portas do container ativo; 18 testes novos foram integrados ao CI.

## Problemas criticos

Nenhum bloqueador observado no escopo testado.

## Problemas altos

BUG corrigido: a reparacao local da migration 0005 poderia perder colunas.
O teste agora verifica a preservacao das colunas e dos dados em SQLite e
PostgreSQL.

BUG ALTO CORRIGIDO NO FOCO-044: o banco continuava publicado em todas as
interfaces apesar do bind local ja configurado. Foi recriado somente o
container bd com o mesmo volume; a porta real agora e 127.0.0.1:5432,
confirmada pelo Docker e pelo socket do host. Nenhum problema alto pendente
identificado no escopo testado; isso nao equivale a auditoria integral.

## Problemas medios

- DIVIDA TECNICA: os indicadores continuam agregando a base em memoria.
  O snapshot reduz leituras e calculos repetidos, mas nao substitui agregacao SQL.
  Carga concorrente, memoria maxima e bases maiores ainda nao foram medidas.
- DIVIDA RESOLVIDA NO INCREMENTO FOCO-041: a verificacao temporaria foi
  convertida em suite frontend integrada. Consulte TESTES_FRONTEND.md.
- LIMITACAO PRESERVADA: o SLA permanece global. A resposta consolidada
  nao apresenta esse campo como indicador dos filtros selecionados.
- DIVIDA TECNICA DE OPERACAO: backup privado em /tmp e temporario; retencao
  institucional e ensaio de restauracao ainda devem ser definidos antes de producao.

## Problemas baixos

O TestClient emite aviso de depreciacao do AnyIO. Os testes passaram;
a atualizacao deve respeitar a compatibilidade entre as dependencias.

## Seguranca

Filtros invalidos e fontes removidas retornam HTTP 400 no novo endpoint.
Nao foram adicionados uploads, SQL interpolado ou novas credenciais.
O medidor bloqueia escritas na sua conexao e nao expoe dados individuais.
Arquivos .env, bancos locais e backups ficam fora da imagem do backend.
Nao foi realizada auditoria completa de vulnerabilidades neste incremento.
Autenticacao institucional continua pertencendo a v0.9; a implantacao atual
deve permanecer em rede controlada. O bind local do banco agora foi ativado
e conferido, sem mudar as portas 8000 e 5173. O verificador rejeita binds
externos, senha ausente e formatos inesperados, sem imprimir secrets da
configuracao nem stdout/stderr do Compose. Ele nao audita complexidade da
senha, vulnerabilidades do Docker ou regras de firewall.

## Backend

Novo endpoint tipado `/api/v1/analytics/dashboard`, com logica no servico.
Endpoints individuais mantidos e comparados por teste com a resposta nova.
O snapshot da sessao e liberado mesmo em caso de erro. Uma assinatura do
dataset por chamada consolidada, comprovada por teste. Periodos e recortes
sao reutilizados; metadados sao copias independentes. Os testes cobrem
contextos aninhados, sessoes diferentes, filtros vazios e novos registros
entre requisicoes. A API ativa foi comparada por HTTP com os nove endpoints
individuais e com o contrato Pydantic, em tres cenarios.

## Frontend

Visao Geral e paineis analiticos usam uma chamada consolidada. Requisicoes
substituidas sao canceladas e respostas antigas ignoradas. Cancelar o fetch
nao garante interromper um calculo que ja comecou no backend.

## Banco de dados

Alembic e a unica autoridade de schema. A API recusa revisoes ausentes ou
desatualizadas. A revisao operacional permanece em 20260914_0005;
este incremento de BI nao exige migration nova. A atualizacao preservou
38.520 ocorrencias, 13 lotes e 50 unidades. API e banco saudaveis, interface
HTTP 200; docker.service e foco.service ativos e habilitados.
No FOCO-044 o backup foi gerado com pg_dump custom, listado por pg_restore
e copiado para /tmp/foco-backup.YSW7P5/foco_ocorrencias.dump no host;
diretorio 0700 e arquivo 0600. Nao foi ensaiada restauracao desse backup.
Nenhuma migration, restauracao ou alteracao manual de schema foi realizada.

## UX/UI

Filtros por periodo e municipio aplicados, mantidos ao navegar para Evolucao.
Cancelamento validado com atraso artificial da requisicao substituida.
Renderizacao nao vazia dos graficos e ausencia de overflow horizontal
verificadas automaticamente em 1920x1080, 1366x768 e 390x844, sem erros
JavaScript de pagina. Isso nao substitui avaliacao visual com usuarios.
Tipificacoes extensas nao ampliam mais o seletor alem da area disponivel.

## Testes

- Infraestrutura: 18 aprovados, 0 falhos, com casos de IPv4/IPv6, divergencia
  entre configuracao e container, erro do Docker e protecao de segredos.
- Verificador no host: configuracao e execucao aprovadas; socket 127.0.0.1:5432.
- SQLite descartavel: 68 aprovados, 0 falhos.
- PostgreSQL/PostGIS descartavel: 68 aprovados, 0 falhos.
- Build TypeScript/Vite aprovado.
- FOCO-042: 17 casos adicionais de dashboard, incluindo equivalencia por dimensao,
  cache por chave, isolamento e preservacao de metadados; regressao reproduzida
  antes da correcao com 40 definicoes de periodo e 21 filtragens.
- Oito casos anteriores de dashboard mantidos: base vazia, filtros invalidos,
  equivalencia combinada, assinatura unica e limpeza apos erro.
- Playwright: 33 aprovados, 0 falhos, nos tres viewports; API simulada e nenhum
  acesso ao banco operacional. Tipos TypeScript aprovados.
- API ativa apos reconexao: nove paineis equivalentes em tres recortes reais
  positivos (38.520 no total, 5.796 em fevereiro e 1 com os seis filtros);
  hashes HTTP anteriores preservados nos dois primeiros recortes.
- API ativa no incremento anterior: nove paineis equivalentes em tres cenarios somente leitura;
  contratos tipados verificados. Hash interno distingue inteiros e floats,
  enquanto o HTTP faz a conversao existente de zeros do SLA para 0.0.
- Medidor: sete repeticoes por recorte antes/depois, hashes completos iguais;
  tempos nao incluem rede, serializacao HTTP ou renderizacao.
- CI atualizado com testes de infraestrutura e verificacao real do Compose
  usando ambiente de exemplo, sem iniciar containers. Essa checagem foi reproduzida
  localmente em pasta temporaria, sem usar o .env operacional; aprovada.
  Execucao remota do workflow nao verificada.
- Cobertura percentual nao medida. Lint dedicado e auditoria de dependencias
  nao executados neste incremento.

## Aderencia ao roadmap

IMPLEMENTADO neste incremento: integracao consolidada dos dashboards com a
API, melhoria de confiabilidade dos filtros globais e reducao de calculos
repetidos sem alterar regras dos indicadores. No FOCO-044 foi corrigida
uma exposicao basica de infraestrutura, sem antecipar autenticacao da v0.9.
PARCIAL: homologacao de todos os criterios de aceite da v0.3.
NAO IMPLEMENTADO neste incremento: funcionalidades de versoes futuras.

## Divida tecnica

Agregacoes em memoria; etapa unica de migration antes de multiplas replicas,
caso essa arquitetura seja adotada. A automacao frontend foi adicionada no
incremento FOCO-041, sem substituir os testes de integracao da API. Politica
de backups permanentes e ensaio de restauracao continuam pendentes.

## Recomendacoes para a equipe

Executar o verificador apos alteracoes de Compose ou implantacao. Confirmar
os criterios de aceite da v0.3 com usuarios e filtros representativos.
Definir retencao protegida dos backups e ensaiar restauracao em base isolada
antes de producao, sem utilizar o banco operacional como ambiente de teste.
Avaliar memoria e carga concorrente antes de substituir agregacoes existentes.
Nao declarar a versao pronta apenas pelos testes tecnicos.

## Backlog proposto

### FOCO-041

Situacao: IMPLEMENTADO LOCALMENTE. Suite completa com 33 testes aprovados,
mais 45 execucoes de estabilidade dos casos de clique/cancelamento/resposta antiga; tipos
TypeScript e build aprovados. CI configurado, execucao remota nao verificada.
Documentacao: TESTES_FRONTEND.md.

Titulo: Automatizar a regressao dos dashboards no frontend.
Descricao: Integrar os testes de filtros, navegacao e respostas substituidas.
Prioridade: Media.
Versao: v0.3.
Area: Frontend / qualidade.
Arquivos envolvidos: frontend/package.json, frontend/tests/, frontend/playwright.config.ts.
Criterio de aceite: Um comando reproduz os fluxos em desktop e notebook,
sem dados demonstrativos apresentados como reais nem acesso de escrita ao banco operacional.

### FOCO-042

Situacao: IMPLEMENTADO LOCALMENTE E ATIVADO NO DOCKER. Medicoes reproduziveis,
hashes equivalentes e 68 testes aprovados em cada banco. Documentacao:
DESEMPENHO_DASHBOARD.md. Agregacao em memoria permanece como divida tecnica.

Titulo: Medir e reduzir agregacoes repetidas do dashboard.
Descricao: Registrar tempos e consultas com bases representativas e otimizar
os pontos comprovados, mantendo equivalencia dos resultados e cobertura dos dados.
Prioridade: Media.
Versao: v0.3.
Area: Backend / BI.
Arquivos envolvidos: backend/app/services/sejusp_analytics_service.py,
backend/tests/test_dashboard.py, backend/scripts/medir_dashboard.py.
A composicao existente em dashboard_service.py foi preservada.
Criterio de aceite: Resultados equivalentes aos endpoints atuais e medidas
reproduziveis de melhoria sem alterar regras de negocio.


### FOCO-043

Situacao: PROPOSTO, nao implementado neste incremento.
Titulo: Validar os criterios de aceite da v0.3 com usuarios.
Descricao: Executar uma matriz de filtros e comparacoes com dados SEJUSP
representativos, confrontando quantidades e series com uma referencia validada.
Prioridade: Alta.
Versao: v0.3.
Area: BI / qualidade / UX.
Arquivos envolvidos: documentacao/operacao/VALIDACAO_V0_3_1.md,
frontend/src/pages/Overview.tsx, frontend/src/pages/AnalyticsPages.tsx,
backend/tests/test_dashboard.py.
Criterio de aceite: Os usuarios identificam periodo, municipio, unidade,
tipificacao, subtipo, turno e filtros ativos; totais, evolucao, distribuicoes
e periodo comparado sao confirmados, sem dados demo e sem inventar cobertura.


### FOCO-044

Situacao: ATIVADO E VERIFICADO NO HOST. Verificador adicionado, 18 testes
aprovados e CI configurado; execucao remota nao verificada. Volume, contagens
e revisao mantidos; API saudavel apos reconexao.
Titulo: Ativar a restricao de rede da porta do banco.
Descricao: Aplicar o bind local ja configurado no Compose, preservando o
volume e as credenciais existentes; avaliar o impacto da breve reconexao da API.
Prioridade: Alta.
Versao: v0.3 (seguranca basica de implantacao, nao autenticacao futura).
Area: Infraestrutura / seguranca.
Arquivos envolvidos: docker-compose.yml (configuracao local preservada),
infraestrutura/scripts/verificar_banco_docker.py,
infraestrutura/tests/test_verificar_banco_docker.py,
.github/workflows/integracao_continua.yml, documentacao/operacao/SERVICO_DOCKER.md.
Criterio de aceite: A porta 5432 nao e publicada em interfaces externas;
API saudavel apos a ativacao, contagens e revisao do banco preservadas,
nenhuma credencial versionada e volumes operacionais mantidos.
