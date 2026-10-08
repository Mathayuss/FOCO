# Validacao incremental - FOCO-045

## Versao analisada

FOCO v0.3, pacote v0.3.1. Validacao local em 2026-09-18.
Escopo: estados de carregamento, erro e recuperacao dos dashboards.

## Status

APROVADO COM RESSALVAS para este incremento. A v0.3 nao esta declarada
homologada; permanece a validacao dos criterios de aceite com usuarios.

## Resumo executivo

Durante a troca de filtros, a Visao Geral exibia graficos e indicadores do
recorte anterior abaixo dos novos filtros. Agora os resultados sao retirados
imediatamente, antes mesmo do efeito que inicia a nova requisicao.
O controle compartilhado conserva cancelamento e rejeicao de respostas antigas.

Filtros e cabecalho continuam disponiveis durante carregamento e erro.
Selecoes persistidas aparecem mesmo antes de chegar a lista de opcoes da API.
O comando "Tentar novamente" recupera uma falha sem recarregar a pagina e
mantem o recorte solicitado. Cobertura zero nao e substituida por valores
derivados da quantidade de posicoes vazias de uma serie.

## Problemas criticos

Nenhum bloqueador observado nos cenarios executados. Isso nao representa
auditoria completa de seguranca nem homologacao institucional.

## Problemas altos

- BUG CORRIGIDO: resultados antigos permaneciam visiveis na Visao Geral
  enquanto os filtros ja indicavam outro recorte. Testes reproduziram o
  comportamento antes da correcao e verificam ausencia de indicadores,
  tabelas, comparacao, mapa e canvas ate a resposta atual.
- VALIDACAO PENDENTE: confrontar a matriz completa de filtros e comparacoes
  com referencia institucional e usuarios, conforme FOCO-043.

## Problemas medios

- BUG CORRIGIDO: uma falha da API retirava os controles da Visao Geral.
- BUG CORRIGIDO: selecoes persistidas podiam aparentar valores padrao antes
  do carregamento das opcoes, apesar de a requisicao conter os filtros.
- BUG CORRIGIDO: cobertura horaria zero podia aparecer como 24 horas.
- MELHORIA IMPLEMENTADA: nova tentativa explicita, inclusive na primeira
  carga, sem perder os filtros ou exigir recarregamento da pagina.
- RISCO POR INSPECAO, NAO REPRODUZIDO NESTE INCREMENTO: a selecao mensal
  procura a primeira opcao com um unico mes. Em bases esparsas, opcoes
  agregadas podem ter essa mesma composicao. Registrar teste especifico
  antes de ajustar o comportamento (FOCO-046).

## Problemas baixos

Animacoes de entrada dos graficos foram desativadas para tornar a pintura
e a selecao de barras previsiveis. A suite aguarda pixels da barra selecionada
antes do segundo clique, sem esperas fixas ou relaxamento das assercoes.

## Seguranca

Nenhuma alteracao em permissoes, uploads, credenciais, CORS ou endpoints.
Respostas permanecem apresentadas como texto React, sem HTML injetado.
Os testes automatizados usam fixtures ficticias e bloqueiam chamadas
nao previstas; nao importam registros ou acessam o banco operacional.

A verificacao adicional da aplicacao ativa usou somente GET em contextos
temporarios de navegador. Capturas da base real foram geradas localmente,
mas a transmissao para inspecao visual foi bloqueada pelo controle de
seguranca. Elas nao foram examinadas nem enviadas; permissao explicita foi
solicitada e permanece pendente. Arquivos locais protegidos com modo 0600.
Nao foi executada uma auditoria completa de SQL Injection, XSS, CSRF ou IDOR.
Autenticacao institucional permanece no roadmap v0.9.

## Backend

Sem alteracao de contrato, regra de negocio ou codigo backend neste incremento.
GET `/api/v1/health`: status `ok`, banco `ok` apos as alteracoes.
O controle do frontend conserva AbortController e protecao de ciclo de vida.

## Frontend

- `frontend/src/hooks/useDashboardSnapshot.ts`: resposta identificada pelo
  recorte e pela tentativa, invalidacao sincrona e cancelamento da requisicao.
- `frontend/src/components/DashboardLoadState.tsx`: estado comum com
  `aria-busy`, mensagem `role="status"`, erro `role="alert"` e nova tentativa.
- `frontend/src/filterState.ts`: preservacao da selecao nas opcoes de tela;
  a API continua sendo responsavel por validar valores recebidos.
- `frontend/src/pages/Overview.tsx` e `AnalyticsPages.tsx`: integracao sem
  alterar os indicadores, o contrato da API ou o escopo existente dos paineis.
- `frontend/src/styles.css`: estilo restrito ao estado de resultados e foco
  visivel no comando de recuperacao; identidade visual preservada.

Somente as opcoes do ultimo sucesso sao conservadas durante uma nova carga;
estatisticas antigas nao sao exibidas como resultado do recorte atual.

## Banco de dados

Nenhuma migration, importacao ou gravacao operacional neste incremento.
Conferencia somente leitura: 38.520 ocorrencias, 13 lotes, 50 unidades,
revisao Alembic `20260914_0005`. Verificador de configuracao e execucao
do banco aprovado, preservando a restricao da porta a 127.0.0.1.

## UX/UI

Cabecalho, filtros ativos e seletores permanecem acessiveis nos estados de
carga e erro. A nova tentativa possui foco visivel e conserva as selecoes.
Testes em 1920x1080, 1366x768 e 390x844 verificam ausencia de overflow
horizontal e graficos com pixels nao vazios.
Inspecao manual das imagens da base real nao realizada; validacao automatizada
de layout nao substitui revisao visual nem validacao com operadores.

## Testes

- Suite frontend final: 72 aprovados, 0 falhos, nos tres viewports.
- Clique cruzado real na barra repetido cinco vezes por viewport:
  15 execucoes adicionais aprovadas.
- Tipos dos testes e build TypeScript/Vite com lockfile congelado: aprovados.
- Aplicacao ativa, somente leitura: tres viewports aprovados; total inicial
  38.520, fevereiro/2025 com 5.796, navegacao para Evolucao mantendo o recorte,
  ausencia de dados antigos durante espera, canvas nao vazio, sem overflow
  horizontal e sem erros JavaScript observados.
- API saudavel e interface em `http://localhost:5173` retornando HTTP 200.
- `git diff --check`: aprovado antes do encerramento.
- Suites backend SQLite/PostGIS e unittests de infraestrutura nao foram
  reexecutados neste incremento frontend. Os 68 + 68 + 18 resultados anteriores
  estao registrados na validacao incremental v0.3.1, nao sao novas execucoes.
- Cobertura percentual nao medida; workflow remoto nao executado aqui.

Consulte [Testes frontend](TESTES_FRONTEND.md) para instalacao e comandos.
Os testes simulados nao validam tiles externos nem substituem a integracao
com a API real ou o confronto com referencias institucionais.

## Aderencia ao roadmap

- IMPLEMENTADO NO INCREMENTO: carregamento confiavel, filtros visiveis,
  recuperacao de falhas e preservacao dos filtros cruzados existentes.
- PARCIAL: criterios de aceite da v0.3 exercitados por testes e smoke real,
  ainda sem homologacao completa com usuarios e referencias institucionais.
- NAO IMPLEMENTADO: funcionalidades das versoes futuras; nenhuma antecipada.

## Divida tecnica

Duplicacao da selecao de periodo mensal entre Visao Geral e Evolucao;
ampliar testes com bases esparsas antes de compartilhar ou ajustar esse codigo.
Validacao visual e de acessibilidade ainda nao substituida por auditoria manual.
Resultados locais nao comprovam a execucao do CI remoto.

## Recomendacoes para a equipe

Priorizar FOCO-043 para fechar os criterios de aceite sem ampliar o produto.
Depois, reproduzir o caso de periodos esparsos de FOCO-046 com teste focado.
Publicar somente alteracoes revisadas; nenhum commit ou push foi feito neste
incremento. Preservar arquivos locais de outros trabalhos.

## Backlog proposto

### FOCO-045

Situacao: IMPLEMENTADO E VALIDADO LOCALMENTE.
Titulo: Tornar confiavel o carregamento dos dashboards.
Descricao: Retirar resultados antigos ao trocar filtros, manter controles,
preservar selecoes, tratar cobertura zero e permitir nova tentativa apos erro.
Prioridade: Alta.
Versao: v0.3.
Area: Frontend / BI / qualidade / UX.
Arquivos envolvidos: frontend/src/hooks/useDashboardSnapshot.ts,
frontend/src/components/DashboardLoadState.tsx, frontend/src/filterState.ts,
frontend/src/pages/Overview.tsx, frontend/src/pages/AnalyticsPages.tsx,
frontend/src/styles.css, frontend/tests/loading-state.spec.ts,
frontend/tests/cross-filters.spec.ts.
Criterio de aceite: Nenhum resultado anterior aparece sob filtros novos;
filtros permanecem visiveis e selecionados; nova tentativa conserva o recorte;
zero nao e apresentado como cobertura positiva; suite passa nos tres viewports.

### FOCO-043

Situacao: PENDENTE, ja registrado na validacao incremental v0.3.1.
Titulo: Validar os criterios de aceite da v0.3 com usuarios.
Descricao: Confrontar filtros, totais, series e comparacoes com referencia
institucional, registrando os resultados e as decisoes pendentes.
Prioridade: Alta.
Versao: v0.3.
Area: BI / qualidade / UX.
Arquivos envolvidos: documentacao/operacao/VALIDACAO_V0_3_1.md,
frontend/src/pages/Overview.tsx, frontend/src/pages/AnalyticsPages.tsx,
backend/tests/test_dashboard.py.
Criterio de aceite: Usuarios identificam filtros e periodo comparado;
totais e distribuicoes conferem com referencia validada, sem dados demo.

### FOCO-046

Situacao: PROPOSTO; comportamento suspeito identificado por inspecao.
Titulo: Verificar filtros mensais em bases esparsas.
Descricao: Reproduzir com fixture contendo somente um mes e opcoes agregadas;
confirmar que o clique seleciona o mes, e nao uma opcao agregada com um mes.
Prioridade: Media.
Versao: v0.3.
Area: Frontend / BI / testes.
Arquivos envolvidos: frontend/src/pages/Overview.tsx,
frontend/src/pages/AnalyticsPages.tsx, frontend/tests/cross-filters.spec.ts.
Criterio de aceite: Clique mensal seleciona o periodo mensal correto nos dois
paineis, persiste na navegacao e pode ser removido sem apagar outros filtros.

## Referencias

- [Validacao anterior v0.3.1](VALIDACAO_V0_3_1.md)
- [Desempenho do dashboard](DESEMPENHO_DASHBOARD.md)
- [Operacao Docker](SERVICO_DOCKER.md)
