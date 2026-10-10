# FOCO-070 - Filtros comparativos e mapa interativo

## Versão analisada

FOCO v0.3.1, incremento do BI funcional previsto na v0.3.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

Os filtros temporais agora permitem períodos rápidos ou intervalo exato e usam
sempre o mesmo recorte do ano anterior como base. A interface identifica os dois
períodos, o mapa ganhou interação territorial e os textos operacionais principais
foram ampliados. Os critérios centrais de comparação da v0.3 estão funcionais.

## Problemas críticos

Nenhum bloqueador conhecido após a implementação.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- A cobertura da fonte é conhecida por mês. Em um intervalo parcial, a API não
  consegue distinguir dia sem ocorrência de dia ainda não importado.

## Problemas baixos

- O mapa usa pontos representativos dos municípios, sem limites territoriais.
  Polígonos e operações espaciais completas pertencem ao escopo GIS da v0.5.

## Segurança

- Intervalos usam formato estrito e validação de datas no backend.
- Data final anterior à inicial é bloqueada no frontend e rejeitada pela API.
- O mapa recebe apenas agregados por município; não expõe coordenadas de ocorrências.
- Não houve alteração em credenciais, permissões, CORS ou uploads.

## Backend

- Meses e trimestres passaram de comparação sequencial para comparação anual.
- Intervalos personalizados aplicam limites diários inclusivos no ano atual e anterior.
- O dia 29 de fevereiro é ajustado para 28 de fevereiro no ano-base não bissexto.
- A comparação anual mantém o uso de meses equivalentes quando a cobertura diverge.

## Frontend

- Filtro compartilhado de período evita regras diferentes entre os dashboards.
- Datas inicial e final ficam visíveis e persistem junto aos filtros globais.
- Os rótulos dos gráficos e cartões mostram os períodos comparados.
- Fontes de navegação, filtros, cartões, tabelas e cabeçalhos foram ampliadas.

## Banco de dados

Nenhuma migration ou escrita operacional. A validação consultou somente dados
SEJUSP já importados.

## UX/UI

- O usuário pode escolher ano, trimestre, mês ou datas exatas no mesmo controle.
- O mapa enquadra os pontos disponíveis, informa valores no hover e filtra no clique.
- O município selecionado recebe destaque e pode ser limpo em `Ver todos`.
- O layout foi validado em desktop, notebook e celular sem overflow horizontal.

## Testes

- Backend SQLite: 97 aprovados, 0 falhos.
- Backend PostgreSQL/PostGIS descartável: 97 aprovados, 0 falhos.
- Playwright: 132 aprovados, 0 falhos.
- Viewports: 1920x1080, 1366x768 e 390x844.
- Tipagem TypeScript: aprovada.
- Build TypeScript/Vite: aprovado.
- API operacional: saudável após reinício.
- CI remoto e cobertura percentual: não verificados.

## Aderência ao roadmap

- Implementado: filtro por período e comparação explícita com o ano anterior.
- Implementado: evolução, tipificação, temporal e mapa respondendo aos filtros globais.
- Implementado: identificação do município, unidade e filtros ativos.
- Parcial: filtros cruzados existem em gráficos, tabelas e mapa, mas ainda precisam
  de homologação funcional completa com usuários.
- Não antecipado: polígonos, hotspots e operações PostGIS do escopo v0.5.

## Dívida técnica

- O serviço analítico ainda processa agregações em memória; crescimento da base
  exigirá consultas agregadas, índices e medição antes da v0.11.
- Falta calendário institucional de cobertura diária por fonte e lote.
- A homologação integral dos critérios de aceite da v0.3 permanece pendente.

## Recomendações para a equipe

1. Homologar os filtros e comparativos com casos reais conhecidos pela operação.
2. Registrar cobertura diária da fonte na etapa de importação da v0.4.
3. Preservar rótulos explícitos de período em todo novo indicador comparativo.

## Backlog proposto

### FOCO-071

Título: Registrar cobertura temporal diária por fonte e lote.

Descrição: distinguir ausência real de ocorrências de ausência de dados importados,
sem criar ou inferir registros operacionais.

Prioridade: Média.

Versão: v0.4.

Área: Dados, importação e backend.

Arquivos envolvidos: modelo e migration de lotes, serviço de importação, serviço
analítico, schemas da API e testes.

Critério de aceite: a API informa a cobertura diária dos dois períodos comparados
e sinaliza claramente qualquer dia sem confirmação de carga institucional.
