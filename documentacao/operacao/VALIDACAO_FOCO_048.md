# Validacao incremental - FOCO-048

## Versao analisada

FOCO v0.3, pacote v0.3.1. Incremento local em 2026-09-19.

## Status

APROVADO COM RESSALVAS para FOCO-048. A homologacao funcional completa da
v0.3 permanece pendente de validacao com usuarios (FOCO-043).

## Resumo executivo

As tabelas de Tipificacao e Unidades permitiam filtrar por clique na linha,
mas nao ofereciam um controle acionavel por teclado. Agora o nome em cada
linha filtravel e um botao nativo, com nome acessivel e foco visivel.
O clique no restante da linha foi preservado. O evento do botao nao sobe
para a linha, evitando aplicar e remover o mesmo filtro em um so gesto.

## Problemas criticos

Nenhum bloqueador identificado no escopo executado. Isto nao representa
auditoria completa nem homologacao da aplicacao.

## Problemas altos

Nenhum novo problema alto. FOCO-043 continua a pendencia alta do aceite v0.3.

## Problemas medios

- BUG CORRIGIDO: o filtro cruzado das tabelas nao podia ser acionado por
  teclado. Os dois testes de acesso por botao falharam antes da mudanca
  porque o controle nao existia; passaram depois com Enter e Espaco.

## Problemas baixos

O cabecalho da primeira coluna da tabela de Tipificacao agora informa sua
dimensao, em vez de usar o rotulo generico "Nome".

## Seguranca

Suite de navegador usa apenas respostas ficticias interceptadas; nao envia
dados a API operacional. Nenhuma alteracao em credenciais, permissoes,
uploads, CORS, HTML dinamico ou endpoints. Auditoria ampla nao realizada.

## Backend

Sem alteracoes. As chaves `type`, `unit` e `period` continuam enviadas nos
mesmos parametros da API consolidada.

## Frontend

- `frontend/src/pages/AnalyticsPages.tsx`: botao nativo na primeira celula
  das linhas filtraveis, com nome acessivel e parada de propagacao do clique.
  O clique preexistente na linha permanece disponivel para mouse e toque.
- `frontend/src/styles.css`: botao integrado ao texto da tabela, sem cartao
  decorativo, e contorno de foco visivel. Texto longo pode quebrar linha.
- `frontend/tests/table-filters.spec.ts`: Enter, Espaco, preservacao do
  periodo, clique de linha sem dupla ativacao e nome longo responsivo.

## Banco de dados

Nenhuma migration, importacao ou gravacao neste incremento frontend.

## UX/UI

Filtro cruzado acessivel a mouse, toque e teclado, sem mudar a aparencia
geral da tabela. Nome longo da tipificacao permaneceu dentro do viewport em
1920x1080, 1366x768 e 390x844, sem overflow horizontal automatizado.
Revisao manual de acessibilidade com operadores ainda pendente.

## Testes

- Regressao inicial: dois testes de acesso por teclado falharam antes da
  correcao; o teste de clique na linha ja passava e permaneceu passando.
- Suite final com tipos: 93 aprovados, 0 falhos, nos tres viewports.
- Build TypeScript/Vite com lockfile congelado: aprovado.
- Verificacao responsiva com nome extenso ficticio: tres viewports aprovados.
- Backend SQLite/PostGIS e infraestrutura nao reexecutados neste incremento.
  Cobertura percentual e workflow remoto nao verificados.

## Aderencia ao roadmap

- IMPLEMENTADO: filtro cruzado nas tabelas de Tipificacao e Unidades pode
  ser acionado por teclado, pertinente ao BI funcional v0.3.
- PARCIAL: aceite institucional da v0.3, dependente de FOCO-043.
- NAO IMPLEMENTADO: funcoes das versoes futuras; nenhuma antecipada.

## Divida tecnica

Os eventos dos graficos usam parametros `any` nas paginas legadas; esta
correcao nao amplia essa refatoracao. A acessibilidade integral e a
homologacao com usuarios continuam pendentes.

## Recomendacoes para a equipe

Validar com operadores os filtros cruzados, foco e leitura de tabela junto
com totais e comparacoes do FOCO-043, usando dados institucionais aprovados.

## Backlog proposto

### FOCO-048

Situacao: IMPLEMENTADO E VALIDADO LOCALMENTE.
Titulo: Tornar filtros cruzados das tabelas acionaveis por teclado.
Descricao: Adicionar botoes nas linhas filtraveis de Tipificacao e Unidades,
preservando clique existente e demais filtros globais.
Prioridade: Media.
Versao: v0.3.
Area: Frontend / BI / acessibilidade.
Arquivos envolvidos: frontend/src/pages/AnalyticsPages.tsx,
frontend/src/styles.css, frontend/tests/table-filters.spec.ts.
Criterio de aceite: Enter e Espaco aplicam/removem filtro; periodo persiste;
clique na linha dispara uma vez; nomes longos nao causam overflow nos tres
viewports e o foco fica visivel.

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
Criterio de aceite: Usuarios identificam filtros e periodo comparado;
totais e distribuicoes conferem com referencia validada.

## Referencias

- [Validacao FOCO-047](VALIDACAO_FOCO_047.md)
- [Testes frontend](TESTES_FRONTEND.md)
- [Validacao v0.3.1](VALIDACAO_V0_3_1.md)
