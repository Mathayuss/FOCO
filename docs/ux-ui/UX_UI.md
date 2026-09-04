# FOCO — Diretrizes de UX/UI

## 1. Objetivo
A interface deve transmitir clareza, controle, confiabilidade e inteligência operacional.

## 2. Direção visual
- dashboard dark;
- aparência institucional;
- alta densidade de informação;
- baixo ruído visual;
- cards modulares;
- sidebar fixa;
- filtros globais.

## 3. Layout
```text
Sidebar
   +
Topbar
   +
Filtros
   +
Conteúdo
```

## 4. Sidebar
Módulos:
- Visão Geral;
- Evolução;
- Tipificação;
- Temporal;
- Território;
- SLA;
- Viaturas;
- Unidades;
- Importações;
- Integrações;
- Qualidade;
- Configurações.

Deve poder recolher.

## 5. Filtros
- período;
- município;
- unidade;
- tipo;
- subtipo;
- turno;
- viatura;
- fonte.

Filtros ativos devem permanecer visíveis.

## 6. Cards
Priorizar:
- valor;
- contexto;
- tendência;
- unidade de medida.

Gauge apenas quando houver meta/faixa.

## 7. Gráficos
Apache ECharts.

Padrões:
- linha: evolução;
- barras: ranking;
- donut: composição;
- heatmap: hora × dia;
- gauge: SLA;
- mapa: território.

Devem tratar:
- tooltip;
- responsividade;
- vazio;
- loading;
- erro.

## 8. Interação
Gráficos podem atuar como filtro.

Clique em uma categoria deve atualizar gráficos compatíveis.

## 9. Drill-down
```text
Indicador
  ↓
Tipo
  ↓
Subtipo
  ↓
Município
  ↓
Região
  ↓
Ocorrência
```

## 10. Mapa
Modos:
- Heatmap;
- Municípios;
- Pontos;
- SLA.

Abrir no recorte territorial da corporação.

## 11. Cores
- fundo grafite;
- cinza escuro;
- vermelho institucional;
- amarelo/dourado para atenção;
- verde para sucesso;
- azul para informação;
- vermelho forte para erro.

Cor deve ter significado funcional.

## 12. Acessibilidade
- contraste;
- labels;
- teclado;
- foco;
- não depender apenas de cor;
- legibilidade.

## 13. Resoluções
Priorizar:
- 1920x1080;
- notebooks;
- monitores operacionais.

## 14. Sala de Situação
- sem sidebar;
- fontes maiores;
- menos controles;
- atualização automática;
- carrossel;
- tela cheia.

## 15. Estados
Toda página deve tratar:
- carregando;
- vazio;
- erro;
- parcial;
- DEMO;
- real.
