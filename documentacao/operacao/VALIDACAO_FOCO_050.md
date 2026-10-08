# Validacao incremental - FOCO-050

## Versao analisada

FOCO v0.3, pacote v0.3.1. Incremento local em 2026-09-19.

## Status

APROVADO COM RESSALVAS para FOCO-050. O aceite completo da v0.3 ainda
depende da validacao com usuarios e referencias institucionais (FOCO-043).

## Resumo executivo

Em um recorte com zero ocorrencias, a API devolvia os valores selecionados
nos filtros de tipo e municipio como `top_type` e `top_municipality`. A
Visao Geral os apresentava como "Maior demanda", apesar de nao haver
ocorrencia observada. Agora os lideres sao derivados apenas das metricas
retornadas. A interface tambem evita exibi-los quando o total e zero.
Os filtros continuam ativos e visiveis nos controles e chips.

## Problemas criticos

Nenhum bloqueador identificado neste escopo. Esta verificacao nao e uma
auditoria completa nem homologacao institucional.

## Problemas altos

Nenhum novo problema alto. FOCO-043 permanece pendencia alta do aceite v0.3.

## Problemas medios

- BUG CORRIGIDO: filtro selecionado apresentado como maior demanda de
  recorte vazio. A regressao de API falhou antes da mudanca (`RESGATE`
  recebido no lugar de vazio) e passou depois.
- BUG CORRIGIDO: interface mostrava uma tipificacao como lider quando a
  resposta tinha total zero. Regressao de navegador falhou antes e passou
  depois, mantendo os filtros selecionados visiveis.

## Problemas baixos

Nenhum ajuste adicional necessario para o indicador neste incremento.

## Seguranca

Testes backend executados em bancos temporarios SQLite e PostGIS; testes
frontend usam fixtures ficticias e interceptam a API. Nenhuma permissao,
credencial, upload, endpoint ou dado institucional foi alterado. Auditoria
ampla de seguranca nao executada.

## Backend

`backend/app/services/sejusp_analytics_service.py` passa a preencher
`top_type` e `top_municipality` somente a partir das listas de metricas
do recorte. Se nao existem itens, ambos retornam vazio. Para um recorte
com ocorrencias, os lideres observados permanecem iguais.

## Frontend

`frontend/src/pages/Overview.tsx` apresenta `-` e `sem dados` no cartao
"Maior demanda" quando o total e zero, mesmo se receber nomes de uma
resposta antiga. `frontend/tests/empty-top-demand.spec.ts` cobre recorte
vazio com filtros ativos e recorte preenchido nos tres viewports.

## Banco de dados

Nenhuma migration ou gravacao operacional. O teste de API usa somente
ocorrencias ficticias nos bancos descartaveis. Depois do reinicio apenas
do servidor da API, permaneceram 38.520 ocorrencias, 13 lotes,
50 unidades e revisao Alembic `20260914_0005`.

## UX/UI

O cartao diferencia ausencia de demanda de filtros selecionados. Tipo e
municipio continuam visiveis nos chips, sem serem apresentados como
resultado estatistico. Nao houve mudanca de layout nem de identidade visual.

## Testes

- Regressao backend de recorte vazio: falhou antes, passou depois;
  controle positivo de recorte com uma ocorrencia aprovado.
- Regressao frontend de cartao vazio: falhou antes, passou depois;
  controle positivo aprovado.
- Suite backend SQLite: 70 aprovados, 0 falhos.
- Suite backend PostGIS descartavel: 70 aprovados, 0 falhos; containers e
  rede de teste removidos apos a execucao.
- Suite frontend com tipos: 102 aprovados, 0 falhos, em 1920x1080,
  1366x768 e 390x844.
- Build TypeScript/Vite com lockfile congelado: aprovado.
- API operacional saudavel depois de reiniciar somente `servidor`.
- Warning nao bloqueante: alias `anyio.abc.BlockingPortal` depreciado
  no `starlette.testclient` da imagem atual.
- Cobertura percentual e workflow remoto nao verificados.

## Aderencia ao roadmap

- IMPLEMENTADO: maior demanda fiel ao recorte efetivo, parte da Visao
  Geral funcional da v0.3.
- PARCIAL: aceite completo da v0.3, pendente de FOCO-043.
- NAO IMPLEMENTADO: funcionalidades de versoes futuras.

## Divida tecnica

Permanece a validacao dos indicadores com usuarios e referencias
institucionais. A deprecacao do TestClient deve ser acompanhada antes de
atualizar dependencias principais.

## Recomendacoes para a equipe

Incluir recortes vazios na matriz de homologacao FOCO-043, verificando
que filtros ativos nao sejam confundidos com ranking ou demanda real.

## Backlog proposto

### FOCO-050

Situacao: IMPLEMENTADO E VALIDADO LOCALMENTE.
Titulo: Nao atribuir maior demanda a recorte sem ocorrencias.
Descricao: Derivar tipo e municipio lideres das metricas observadas,
mantendo filtros ativos separados dos resultados.
Prioridade: Media.
Versao: v0.3.
Area: Backend / Frontend / BI / qualidade.
Arquivos envolvidos: backend/app/services/sejusp_analytics_service.py,
backend/tests/test_dashboard.py, frontend/src/pages/Overview.tsx,
frontend/tests/empty-top-demand.spec.ts.
Criterio de aceite: Com total zero, `top_type` e `top_municipality`
retornam vazios e o cartao nao mostra lider; filtros permanecem visiveis.
Com ocorrencias, lideres observados continuam corretos. Suites SQLite,
PostGIS e frontend passam.

### FOCO-043

Situacao: PENDENTE, registrado na validacao v0.3.1.
Titulo: Validar criterios de aceite da v0.3 com usuarios.
Descricao: Confrontar filtros, totais, series e comparacoes com referencia
institucional, registrando resultados e decisoes pendentes.
Prioridade: Alta.
Versao: v0.3.
Area: BI / qualidade / UX.
Arquivos envolvidos: documentacao/operacao/VALIDACAO_V0_3_1.md,
frontend/src/pages/Overview.tsx, frontend/src/pages/AnalyticsPages.tsx,
backend/tests/test_dashboard.py.
Criterio de aceite: Usuarios identificam filtros e periodo comparado;
totais e distribuicoes conferem com referencia validada.

## Referencias

- [Validacao FOCO-049](VALIDACAO_FOCO_049.md)
- [Testes frontend](TESTES_FRONTEND.md)
- [Testes backend isolados](TESTES_ISOLADOS.md)
