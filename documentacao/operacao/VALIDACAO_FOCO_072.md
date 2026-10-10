# FOCO-072 - Interface operacional compacta

## Versão analisada

FOCO v0.3.1, otimização incremental da interface do BI v0.3.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

As capturas fornecidas mostravam uma área superior alta e com fonte, filtros e
contexto repetidos. A Visão Geral foi compactada sem esconder filtros ativos nem
reduzir a legibilidade. Gráficos e mapa passam a aparecer mais cedo na tela.

## Problemas críticos

Nenhum bloqueador conhecido após a implementação.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- A navegação móvel ainda é horizontal e deve ser homologada em dispositivos reais.

## Problemas baixos

- Os ícones legados de atualização e tela cheia ainda usam caracteres de texto.

## Segurança

- Nenhuma alteração em autenticação, permissões, API, upload ou exposição de dados.
- A remoção do seletor de fonte não altera o parâmetro fixo `source=sejusp` enviado à API.

## Backend

Nenhuma alteração. Contratos e comparativos da FOCO-070 foram preservados.

## Frontend

- Barra fixa reduzida de 72 para 54 px.
- Título e descrição da Visão Geral integrados à barra fixa.
- Fonte de opção única removida dos filtros visuais.
- Chips locais e resumo superior duplicados removidos.
- Cabeçalho da Visão Geral mantém somente título e descrição curta.
- Filtros ativos continuam removíveis na barra fixa.
- Visão Geral mantém três KPIs aderentes à v0.3.

## Banco de dados

Nenhuma migration, consulta nova ou escrita operacional.

## UX/UI

- Primeiro comparativo antecipado em aproximadamente 130 px no desktop.
- Cabeçalho separado removido; filtros começam imediatamente abaixo da barra superior.
- Filtros secundários organizados em duas colunas no celular.
- Chips da barra são ocultados no celular para evitar compressão; a seleção continua visível nos controles.
- Gráficos e início do mapa aparecem na primeira tela em 1920x1080.
- SLA saiu somente da Visão Geral e permanece no módulo específico.

## Testes

- Playwright: 135 aprovados, 0 falhos.
- Viewports: 1920x1080, 1366x768 e 390x844.
- Tipagem TypeScript: aprovada.
- Build TypeScript/Vite: aprovado.
- Inspeção visual com dados operacionais: aprovada.
- Backend não reexecutado por não ter sido alterado neste incremento.
- CI remoto e cobertura percentual: não verificados.

## Aderência ao roadmap

- Implementado: maior densidade e clareza da Visão Geral v0.3.
- Implementado: filtros globais continuam visíveis e persistentes.
- Implementado: comparativos permanecem explícitos e sem perda de contexto.
- Corrigido: indicador de SLA futuro deixou de competir com o BI da v0.3.

## Dívida técnica

- A topbar ainda não usa uma biblioteca de ícones consistente.
- A navegação móvel precisa de homologação de uso, além dos testes automatizados.
- A v0.3 permanece sem homologação operacional completa.

## Recomendações para a equipe

1. Evitar repetir no conteúdo informações já visíveis em filtros ou comparativos.
2. Manter na Visão Geral somente indicadores necessários para decisão imediata.
3. Homologar a densidade em notebooks usados na operação.

## Backlog proposto

### FOCO-073

Título: Padronizar ícones e ações utilitárias da barra superior.

Descrição: substituir caracteres de atualização e tela cheia por ícones da
biblioteca visual adotada, mantendo nomes acessíveis e tooltips.

Prioridade: Baixa.

Versão: v0.3.

Área: Frontend e UX/UI.

Arquivos envolvidos: barra superior, dependências visuais e testes Playwright.

Critério de aceite: ações possuem ícones consistentes, nome acessível, tooltip,
foco visível e não alteram a altura compacta da barra.
