# FOCO-086 - Cobertura temporal dos lotes importados

## Objetivo

Registrar os meses efetivamente presentes em linhas válidas de cada lote,
usando exclusivamente a data de registro reconhecida na planilha. A cobertura
não é inferida pelo nome do arquivo, intervalo entre datas, data do fato ou
meses ausentes.

## Comportamento

- Prévia e confirmação retornam anos e meses distintos `YYYY-MM` das datas de
  registro válidas.
- Linhas válidas sem data de registro são contadas e não entram na cobertura.
- O filtro de anos pós-importação usa somente o ano de registro; data do fato
  não funciona como fallback.
- Histórico do lote persiste `periodos_registro` e
  `linhas_validas_sem_data_registro`.
- Lotes anteriores à migration retornam cobertura `null`, preservando a
  distinção entre desconhecida e cobertura vazia conhecida.
- Tela de importação mostra cobertura na prévia, resultado e lista de lotes.

## Validação

Testes isolados cobrem derivação por data de registro, arquivo cujo nome e data
do fato indicam outro ano, ausência da data de registro, serialização do lote e
compatibilidade da cadeia de migrations. A API continua sem receber inferências
de mês a partir de totais agregados ou do nome do arquivo.

## Limite conhecido

A cobertura da migration é declarada para novos lotes. Lotes históricos não são
reconstruídos automaticamente porque ocorrências podem ter sido consolidadas,
reprocessadas ou originadas de fontes cuja abrangência original não está
disponível. Uma futura rotina explícita de auditoria poderá propor cobertura
derivada das ocorrências vinculadas, identificando-a como estimada, nunca como
declaração original do arquivo.
