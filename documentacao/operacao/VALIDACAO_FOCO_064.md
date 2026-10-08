# FOCO-064 - Comparação anual por meses equivalentes

## Versão analisada

FOCO v0.3.1, correção da comparação entre períodos anuais.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O período de 2026 possui dados de janeiro a agosto, enquanto 2025 possui dados
de janeiro a junho. A regra genérica procurava os oito meses imediatamente
anteriores, maio a dezembro de 2025, e declarava a comparação indisponível.
Períodos anuais agora usam os mesmos meses contínuos com cobertura nos dois anos.

## Problemas críticos

Nenhum bloqueador conhecido após a correção.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- O lote ainda não possui período de cobertura declarado pela fonte.

## Problemas baixos

- A cobertura mensal é inferida pela presença de registros naquele mês.

## Segurança

Nenhuma alteração em autenticação, upload, permissões ou exposição de dados.

## Backend

- `ano-AAAA` usa meses equivalentes do ano anterior, iniciando pelo primeiro mês do recorte.
- A comparação interrompe no primeiro mês sem cobertura anterior.
- O total comparável é recalculado sem alterar o total completo do filtro anual.
- Mês, trimestre e período genérico mantêm a regra de período imediatamente anterior.

## Frontend

- O primeiro cartão da faixa usa `Recorte comparável` quando seu total difere do total anual.
- Intervalos e motivo de cobertura são apresentados sem ocultar meses adicionais do ano atual.

## Banco de dados

Nenhuma migration ou escrita foi necessária. A conferência usa `DATA DO REGISTRO`
no fuso `America/Campo_Grande`, conforme a regra analítica atual.

## UX/UI

O usuário passa a ver simultaneamente o total anual completo, o intervalo usado
na comparação, a base anterior e a razão da limitação de cobertura.

## Testes

- Regressão falhou antes da correção com comparação indisponível.
- Backend SQLite: 94 aprovados, 0 falhos.
- Backend PostgreSQL/PostGIS descartável: 94 aprovados, 0 falhos, 1 aviso de depreciação.
- Frontend Playwright: 111 aprovados, 0 falhos, em três viewports.
- Build TypeScript/Vite: aprovado.

## Aderência ao roadmap

- Comparação entre períodos da v0.3: implementada para anos com cobertura desigual.
- Filtros e gráficos cruzados existentes: preservados.
- Metadados formais de cobertura pertencem à evolução de importação da v0.4.

## Dívida técnica

- Ausência de datas inicial e final declaradas no lote de importação.
- Ausência de indicador formal de período completo ou parcial fornecido pela fonte.

## Recomendações para a equipe

1. Exibir sempre os rótulos dos meses comparados junto à variação.
2. Não interpretar presença de registros como garantia institucional de mês completo.

## Backlog proposto

### FOCO-065

Título: Registrar período de cobertura declarado pelo lote.

Descrição: Permitir que cada importação informe datas inicial e final de referência
e se o relatório representa período completo ou parcial.

Prioridade: Média.

Versão: v0.4.

Área: Dados e importação.

Arquivos envolvidos: modelo e migration de lote, serviço de importação, schemas e interface.

Critério de aceite: comparações usam a cobertura declarada do lote e sinalizam
explicitamente períodos parciais sem inferir completude apenas pelos registros.
