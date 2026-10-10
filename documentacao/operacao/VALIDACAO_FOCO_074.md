# FOCO-074 - Ciclo de vida confiável do mapa

## Versão analisada

FOCO v0.3.1, correção incremental do mapa interativo da v0.3.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O smoke da aplicação ativa detectou erro intermitente do Leaflet ao sair do mapa
durante um reenquadramento. O mapa agora atualiza posição sem animação pendente e
pode ser desmontado imediatamente após uma seleção municipal.

## Problemas críticos

Nenhum bloqueador conhecido após a correção.

## Problemas altos

Nenhum problema alto aberto.

## Problemas médios

- A navegação por mapa ainda requer homologação operacional com uso prolongado.

## Problemas baixos

- Tiles externos dependem da disponibilidade do OpenStreetMap.

## Segurança

Nenhuma alteração em dados, permissões, autenticação ou chamadas da API.

## Backend

Não alterado.

## Frontend

- `flyTo` animado substituído por `setView` sem animação.
- `fitBounds` e enquadramento de ponto único executados com `animate: false`.
- Filtros, tooltip, destaque e limpeza do município foram preservados.

## Banco de dados

Não alterado.

## UX/UI

O reenquadramento passa a ser imediato. A pequena perda de animação evita erro de
console e mantém a interação previsível durante navegação rápida.

## Testes

- Playwright: 138 aprovados, 0 falhos.
- Cenários do mapa: 6 aprovados nos três viewports.
- Tipagem TypeScript: aprovada.
- Build TypeScript/Vite: aprovado.
- Backend não reexecutado por não ter sido alterado.

## Aderência ao roadmap

Correção de confiabilidade do mapa já existente na v0.3, sem antecipar GIS da v0.5.

## Dívida técnica

- Tiles continuam externos e sem cache institucional.
- Testes end-to-end não substituem homologação prolongada em sala de operação.

## Recomendações para a equipe

1. Manter transições do mapa canceláveis ou imediatas durante trocas de módulo.
2. Preservar o teste de desmontagem em qualquer atualização do Leaflet.

## Backlog proposto

### FOCO-075

Título: Definir estratégia institucional de tiles para produção.

Descrição: avaliar disponibilidade, cache e atribuição do provedor cartográfico.

Prioridade: Baixa.

Versão: v0.5.

Área: GIS e infraestrutura.

Arquivos envolvidos: configuração do mapa, proxy e documentação de implantação.

Critério de aceite: indisponibilidade do provedor externo não quebra a navegação
e a política de uso e atribuição fica documentada.
