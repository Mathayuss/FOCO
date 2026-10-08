# Validacao incremental - FOCO-049

## Versao analisada

FOCO v0.3, pacote v0.3.1. Incremento local em 2026-09-19.

## Status

APROVADO COM RESSALVAS para FOCO-049. A v0.3 ainda depende de validacao
funcional com usuarios e referencia institucional (FOCO-043).

## Resumo executivo

Quando o recorte atual e a base anterior continham zero ocorrencias para
um filtro, o backend retornava `0,0%` e simultaneamente explicava que nao
era possivel calcular a variacao percentual. O quociente `0/0` nao define
um percentual. Agora `delta_pct` e `null` nesse caso; a diferenca absoluta
continua zero e a comparacao mensal continua disponivel.

Visao Geral e Evolucao distinguem base ausente de base existente com total
zero. O indicador percentual mostra `indisponivel` e identifica que a base
anterior tem zero ocorrencias; a Visao Geral exibe o motivo fornecido pela
API. Comparacoes com denominador positivo mantem o resultado anterior.

## Problemas criticos

Nenhum bloqueador identificado neste escopo. Nao constitui auditoria
completa ou homologacao institucional.

## Problemas altos

Nenhum novo problema alto. FOCO-043 permanece pendencia alta do aceite v0.3.

## Problemas medios

- BUG CORRIGIDO: `0/0` apresentado como estabilidade de `0,0%` apesar do
  motivo de impossibilidade de calculo. Teste de API reproduziu a falha
  antes da correcao (`recebido 0.0`, `esperado null`).
- BUG CORRIGIDO: interface chamava a base anterior zerada de "sem base" e
  ocultava o motivo; teste de navegador reproduziu o comportamento antes
  da mudanca.

## Problemas baixos

Nenhuma alteracao adicional necessaria para este caso-limite.

## Seguranca

Testes backend usaram bancos descartaveis criados por migrations, nao o
PostgreSQL operacional. Testes frontend usam fixtures ficticias e API
interceptada. Nenhuma permissao, credencial, upload ou endpoint foi mudado.
Nao foi executada auditoria de seguranca completa.

## Backend

Em `backend/app/services/sejusp_analytics_service.py`, a variacao percentual
somente e calculada se o total da base anterior for positivo. Com base zero,
`delta_pct` e `null`; `available`, rotulos, totais, diferenca absoluta,
motivo e pontos mensais preservam seus contratos e significados.

## Frontend

- `frontend/src/pages/Overview.tsx`: estado `indisponivel` para percentual,
  resumo da base zero, diferenca absoluta em tom neutro e motivo legivel
  na faixa comparativa.
- `frontend/src/pages/AnalyticsPages.tsx`: mesma distincao no painel
  Evolucao, sem alterar filtros, serie ou navegacao.
- `frontend/tests/zero-baseline.spec.ts`: verifica ambos os paineis nos
  tres viewports com resposta controlada.

## Banco de dados

Nenhuma migration ou alteracao de registros. O teste de API insere apenas
ocorrencias ficticias nos bancos temporarios SQLite e PostGIS. Depois do
reinicio somente da API operacional, permaneceram 38.520 ocorrencias,
13 lotes, 50 unidades e revisao Alembic `20260914_0005`.

## UX/UI

Uma base temporal coberta mas zerada nao e confundida com base ausente,
nem com variacao percentual de 0%. O motivo aparece integralmente na
Visao Geral. O painel Evolucao resume a causa junto ao indicador.
Layout e identidade visual foram preservados.

## Testes

- Regressao API `0/0`: falhou antes da mudanca e passou depois.
- Regressao frontend da base zero: falhou antes da mudanca e passou depois.
- Suite backend SQLite isolada: 69 aprovados, 0 falhos.
- Suite backend PostGIS descartavel em tmpfs/rede interna: 69 aprovados,
  0 falhos; containers e rede de testes removidos depois.
- Suite frontend com tipos: 96 aprovados, 0 falhos, nos viewports
  1920x1080, 1366x768 e 390x844.
- Build TypeScript/Vite com lockfile congelado: aprovado.
- Health da API: banco `ok` apos reiniciar somente `servidor`.
- Warning nao bloqueante: alias `anyio.abc.BlockingPortal` depreciado no
  `starlette.testclient` da imagem atual.
- Cobertura percentual nao medida; workflow CI remoto nao executado aqui.

## Aderencia ao roadmap

- IMPLEMENTADO: comparacao entre periodos com percentual honesto para
  base zero, diretamente no BI funcional v0.3.
- PARCIAL: aceite completo da v0.3, dependente de FOCO-043.
- NAO IMPLEMENTADO: funcoes das versoes futuras, sem antecipacao de escopo.

## Divida tecnica

Permanece a validacao de totais e comparacoes com fonte institucional por
usuarios. A deprecacao do TestClient deve ser acompanhada sem atualizar
dependencias principais automaticamente.

## Recomendacoes para a equipe

Na homologacao FOCO-043, confrontar tambem filtros que produzam base zero
e confirmar que a diferenca absoluta e o percentual sao interpretados
corretamente pelos operadores.

## Backlog proposto

### FOCO-049

Situacao: IMPLEMENTADO E VALIDADO LOCALMENTE.
Titulo: Nao apresentar `0/0` como variacao percentual de 0%.
Descricao: Retornar percentual nulo quando a base anterior estiver zerada
e informar o motivo nos paineis, mantendo os totais e diferenca absoluta.
Prioridade: Media.
Versao: v0.3.
Area: Backend / Frontend / BI / qualidade.
Arquivos envolvidos: backend/app/services/sejusp_analytics_service.py,
backend/tests/test_dashboard.py, frontend/src/pages/Overview.tsx,
frontend/src/pages/AnalyticsPages.tsx, frontend/tests/zero-baseline.spec.ts.
Criterio de aceite: Com base anterior zero, percentual nao e inventado;
Visao Geral e Evolucao identificam a causa; comparacoes com base positiva
continuam corretas; suites SQLite, PostGIS e frontend passam.

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

- [Validacao FOCO-048](VALIDACAO_FOCO_048.md)
- [Testes frontend](TESTES_FRONTEND.md)
- [Testes backend isolados](TESTES_ISOLADOS.md)
