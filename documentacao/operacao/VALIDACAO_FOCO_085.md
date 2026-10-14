# FOCO-085 - Comparacao anual com cobertura parcial

## Objetivo

Ampliar o smoke somente leitura do BI para validar o recorte anual. A verificacao
garante que a API compare apenas meses equivalentes, associe cada mes ao mesmo
mes do ano anterior e explique quando a cobertura comparativa e menor que a
serie do ano selecionado.

## Validacoes

- periodo anual com pelo menos um mes em comum com o ano anterior;
- rotulos de comparacao com os mesmos meses em anos consecutivos;
- meses comparativos unicos, presentes na serie atual e pareados por nome;
- totais comparados iguais a soma dos pontos mensais equivalentes;
- justificativa de cobertura parcial quando ha meses atuais sem base anterior.

O smoke continua somente com requisicoes HTTP `GET`. A saida apresenta o
periodo mensal e os rotulos anuais verificados, sem imprimir totais, categorias,
localidades, unidades ou registros.

Os testes isolados cobrem uma comparacao parcial valida, um mes pareado com o
mes errado e divergencia entre totais agregados e soma dos meses.

## Resultado operacional

Validado contra a API local em 14/10/2026. A comparacao anual foi reconhecida
como parcial e limitada aos meses equivalentes disponiveis nos dois anos; os
meses restantes do ano atual permanecem fora da comparacao, sem serem tratados
como zero ou removidos do periodo anual selecionado.

## Escopo e backlog

Esta melhoria verifica o contrato ja existente e nao altera importacoes nem
registros operacionais. A ausencia de fonte para meses de 2025 nao deve ser
corrigida com dados sinteticos. A cobertura institucional continua sendo uma
decisao de dados/importacao da v0.4.
