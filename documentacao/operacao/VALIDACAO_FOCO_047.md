# Validacao incremental - FOCO-047

## Versao analisada

FOCO v0.3, pacote v0.3.1. Incremento local em 2026-09-18.

## Status

APROVADO COM RESSALVAS para FOCO-047. A v0.3 permanece pendente de
homologacao funcional com usuarios e referencias institucionais (FOCO-043).

## Resumo executivo

O painel Temporal apresentava `00h` como pico em recortes sem qualquer
horario registrado. A API retorna corretamente 24 contagens zero nesses
casos; o frontend interpretava o indice inicial da serie como um pico.
Agora o indicador mostra `sem dados` e `sem horario registrado` quando nao
ha contagem positiva. Recortes com horarios mantem o pico calculado.

## Problemas criticos

Nenhum bloqueador identificado no escopo executado. Isto nao constitui
auditoria completa da aplicacao nem homologacao da versao.

## Problemas altos

Nenhum novo problema alto neste incremento. FOCO-043 segue como pendencia
alta de aceite da v0.3.

## Problemas medios

- BUG CORRIGIDO: pico `00h` apresentado como fato em recorte sem registros
  horarios. O teste reproduziu o erro antes da mudanca (`recebido 00h`) e
  passou depois (`sem dados`).

## Problemas baixos

Nenhum ajuste adicional necessario para a correcao localizada.

## Seguranca

Os testes de navegador usam respostas ficticias interceptadas, sem acessar
o banco operacional. Nao houve mudanca em permissoes, uploads, credenciais,
API ou CORS. Nenhuma auditoria ampla de seguranca foi realizada aqui.

## Backend

Sem alteracoes. O contrato de `hours` permanece um array de 24 contagens;
sem ocorrencias com timestamp, todas sao zero. A regra de negocio da API
nao foi modificada.

## Frontend

Em `frontend/src/pages/AnalyticsPages.tsx`, `peakHour` so possui indice
quando ha contagem positiva. O cartao e a cor de destaque do grafico usam
esse resultado, sem supor que zero horas equivale a pico de meia-noite.
Identidade visual e filtros existentes foram preservados.

## Banco de dados

Nenhuma migration, importacao ou gravacao. A regressao usa fixtures locais.

## UX/UI

Ausencia de observacoes nao e confundida com demanda em `00h`. Quando
existem registros, o horario mais frequente e seu total continuam visiveis.
Nao foram feitas alteracoes de layout ou navegacao.

## Testes

- Regressao de recorte vazio: falhou antes da correcao e passou depois.
- Regressao de pico observado `14h`, 12 ocorrencias: passou antes e depois.
- Suite frontend final: 81 aprovados, 0 falhos, nos viewports 1920x1080,
  1366x768 e 390x844. Tipagem dos testes aprovada.
- Build TypeScript/Vite com lockfile congelado: aprovado.
- Backend SQLite/PostGIS e testes de infraestrutura nao reexecutados neste
  incremento so de frontend. Cobertura percentual e CI remoto nao verificados.

## Aderencia ao roadmap

- IMPLEMENTADO: leitura correta da analise temporal em recortes sem dados,
  pertinente ao BI funcional v0.3.
- PARCIAL: aceite completo da v0.3; falta FOCO-043.
- NAO IMPLEMENTADO: modulos de versoes futuras, sem antecipacao de escopo.

## Divida tecnica

Eventos dos graficos ainda recebem parametros `any` em paginas legadas;
nao houve ampliacao da refatoracao para esta mudanca localizada.
Permanece pendente a homologacao dos indicadores com usuarios.

## Recomendacoes para a equipe

Usar FOCO-043 para validar com operadores as situacoes sem dados e com
cobertura parcial, alem de conferir os totais e as comparacoes com a fonte.

## Backlog proposto

### FOCO-047

Situacao: IMPLEMENTADO E VALIDADO LOCALMENTE.
Titulo: Nao inventar pico horario em recortes sem registros.
Descricao: Diferenciar serie horaria zerada de uma demanda real as 00h.
Prioridade: Media.
Versao: v0.3.
Area: Frontend / BI / UX.
Arquivos envolvidos: frontend/src/pages/AnalyticsPages.tsx,
frontend/tests/temporal-empty.spec.ts.
Criterio de aceite: Sem contagem horaria positiva, o cartao informa
ausencia de dados e nao destaca um pico; com dados, conserva o horario
e a quantidade observados. Testes passam nos tres viewports.

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

- [Validacao FOCO-046](VALIDACAO_FOCO_046.md)
- [Testes frontend](TESTES_FRONTEND.md)
- [Validacao v0.3.1](VALIDACAO_V0_3_1.md)
