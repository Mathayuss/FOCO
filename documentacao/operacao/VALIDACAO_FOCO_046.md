# Validacao incremental - FOCO-046

## Versao analisada

FOCO v0.3, pacote v0.3.1. Incremento de BI funcional em 2026-09-18.

## Status

APROVADO COM RESSALVAS para a correcao FOCO-046. A v0.3 permanece sem
homologacao completa; FOCO-043 ainda requer validacao com usuarios e
referencias institucionais.

## Resumo executivo

O clique na serie mensal escolhia a primeira opcao da API que contivesse
apenas o mes clicado. Quando os dados filtrados tinham somente um mes, as
opcoes `all`, ano e trimestre tambem atendiam a esse criterio e apareciam
antes da opcao mensal. O clique em fevereiro de 2025 mantinha o filtro em
`all`, sem aplicar o mes.

Uma regra compartilhada agora aceita somente chaves mensais `AAAA-MM` que
correspondam ao rotulo clicado. Visao Geral e Evolucao usam a mesma regra.
O clique novamente no mes selecionado restaura `all`; outros filtros
continuam ativos. Nenhum endpoint, dado importado ou regra estatistica mudou.

## Problemas criticos

Nenhum bloqueador encontrado nos cenarios deste incremento. Nao houve
auditoria completa do sistema.

## Problemas altos

Nenhum novo problema alto identificado. A validacao integral dos criterios
de aceite da v0.3 continua pendente em FOCO-043.

## Problemas medios

- BUG CORRIGIDO: opcao agregada com um mes confundida com periodo mensal
  pelo clique do grafico. Reproducao automatizada falhou antes da correcao
  (`esperado 2025-02`, `recebido all`) e passou depois.

## Problemas baixos

Nenhum ajuste adicional necessario para esta correcao. Nao foi feita
refatoracao ampla dos filtros ou das paginas.

## Seguranca

Teste usa somente dados ficticios e intercepta as chamadas de API.
Nenhuma credencial, arquivo institucional ou registro operacional foi usado
na suite. Codigo altera apenas a interpretacao da opcao mensal no frontend;
validacao de parametros continua no backend. Nenhuma auditoria ampla de
seguranca foi executada neste incremento.

## Backend

Sem alteracoes. A geracao de periodos continua oferecendo chaves `all`,
`ano-AAAA`, `AAAA-qN` e `AAAA-MM`; meses presentes podem deixar um ano ou
trimestre com um unico mes na lista. Contrato preservado.

## Frontend

- `frontend/src/filterState.ts`: funcao compartilhada para localizar a
  opcao mensal pelo formato de chave e pelo rotulo do mes.
- `frontend/src/pages/Overview.tsx` e `AnalyticsPages.tsx`: removida a
  busca duplicada que selecionava a primeira opcao com um mes.
- `frontend/tests/sparse-periods.spec.ts`: clique real nos dois graficos,
  navegacao entre paineis e preservacao de tipificacao, com resposta simulada
  na mesma ordem produzida pela API.

## Banco de dados

Nenhuma migration ou gravacao. Os testes usam fixture isolada; nao acessam
PostgreSQL/PostGIS operacional.

## UX/UI

O clique mensal aplica o recorte que o ponto representa, inclusive quando
ha apenas um mes disponivel. Se o usuario clicar novamente no mes ativo, o
periodo volta para `all`, sem remover a tipificacao. Identidade visual e
controles existentes preservados.

## Testes

- Novo teste reproduziu a falha antes da mudanca no desktop.
- Suite frontend final: 75 aprovados, 0 falhos, em desktop 1920x1080,
  notebook 1366x768 e mobile 390x844. Inclui tipagem dos testes.
- Clique mensal com base esparsa repetido cinco vezes por viewport:
  15 execucoes adicionais aprovadas, 0 falhas.
- Build TypeScript/Vite com lockfile congelado: aprovado.
- Suites backend SQLite/PostGIS e infraestrutura nao foram reexecutadas
  neste incremento somente frontend. Seus resultados anteriores nao sao
  contabilizados como testes novos. Cobertura percentual nao medida.
- Workflow remoto nao executado; sucesso local nao comprova CI remoto.

## Aderencia ao roadmap

- IMPLEMENTADO: filtro cruzado mensal correto na Visao Geral e Evolucao,
  parte do BI funcional v0.3.
- PARCIAL: aceite completo da v0.3, pendente de FOCO-043.
- NAO IMPLEMENTADO: recursos das versoes posteriores; nenhum antecipado.

## Divida tecnica

Os eventos ECharts ainda usam parametros `any` nos paineis legados.
A correção compartilha apenas a regra de periodo necessaria, sem ampliar
esse refactor. Homologacao visual e funcional com operadores segue pendente.

## Recomendacoes para a equipe

Priorizar FOCO-043: conferir com usuarios reais os totais, series, filtros
e comparacoes frente a referencias validadas. Manter testes de bases
esparsas para impedir regressao do filtro cruzado mensal.

## Backlog proposto

### FOCO-046

Situacao: IMPLEMENTADO E VALIDADO LOCALMENTE.
Titulo: Corrigir clique mensal em bases esparsas.
Descricao: Distinguir periodo mensal de opcoes agregadas que, por acaso,
contenham um unico mes; aplicar e remover o filtro nos dois graficos.
Prioridade: Media.
Versao: v0.3.
Area: Frontend / BI / testes.
Arquivos envolvidos: frontend/src/filterState.ts,
frontend/src/pages/Overview.tsx, frontend/src/pages/AnalyticsPages.tsx,
frontend/tests/sparse-periods.spec.ts.
Criterio de aceite: Clique em fevereiro de 2025 seleciona `2025-02`
mesmo que `all`, ano e trimestre contenham apenas fevereiro; selecao
persiste ao navegar; novo clique volta a `all` e conserva os demais filtros.

### FOCO-043

Situacao: PENDENTE, registrado na validacao v0.3.1.
Titulo: Validar criterios de aceite da v0.3 com usuarios.
Descricao: Confrontar filtros, totais, series e comparacoes com referencia
institucional e registrar decisoes pendentes.
Prioridade: Alta.
Versao: v0.3.
Area: BI / qualidade / UX.
Arquivos envolvidos: documentacao/operacao/VALIDACAO_V0_3_1.md,
frontend/src/pages/Overview.tsx, frontend/src/pages/AnalyticsPages.tsx,
backend/tests/test_dashboard.py.
Criterio de aceite: Usuarios reconhecem o recorte ativo e a base comparada;
numeros e distribuicoes conferem com uma referencia validada.

## Referencias

- [Validacao FOCO-045](VALIDACAO_FOCO_045.md)
- [Testes frontend](TESTES_FRONTEND.md)
- [Validacao v0.3.1](VALIDACAO_V0_3_1.md)
