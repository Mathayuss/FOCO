# Desempenho do dashboard - FOCO-042

## Escopo

FOCO v0.3, pacote v0.3.1. Incremento aprovado com ressalvas; nao equivale
a homologacao completa ou aprovacao para producao institucional.

O servico reutiliza as definicoes de periodo, os recortes e os metadados
durante uma unica requisicao. A serie mensal agrupa as linhas em uma passagem,
preservando a ordem dos meses e das tipificacoes. Os endpoints e regras de
negocio permanecem iguais, inclusive o SLA global existente.

## Medicao reproduzivel

Na raiz, com os servicos Docker ativos:

```bash
docker compose exec -T servidor python -m scripts.medir_dashboard --repeticoes 7
docker compose exec -T servidor python -m scripts.medir_dashboard --repeticoes 7 --periodo 2025-02
```

Filtros opcionais: `--tipo`, `--municipio`, `--unidade`, `--subtipo`, `--turno`.
Os valores devem existir na base. O numero de repeticoes aceita de 1 a 50.
O comando tambem pode ser executado a partir de `backend/` com
`.venv/bin/python -m scripts.medir_dashboard`, usando o ambiente local.

O medidor abre uma transacao somente leitura no PostgreSQL; no SQLite ativa
`query_only`. Nao importa, atualiza ou apaga registros. Aquece o cache de linhas
antes da medicao, valida os filtros e monta a resposta consolidada. A contagem
de chamadas Python usa uma execucao separada, fora das amostras de tempo.
O processo descarta suas conexoes ao terminar.

## Resultados observados

Base: 38.520 ocorrencias SEJUSP, PostgreSQL/PostGIS local, sete repeticoes por
recorte e cache de linhas aquecido. Mesma base, container e host antes/depois.
Esses tempos sao do servico: nao incluem rede, serializacao HTTP ou renderizacao.

| Recorte | Total | Mediana antes | Mediana depois | Reducao observada |
| --- | ---: | ---: | ---: | ---: |
| Todos os periodos | 38.520 | 500,90 ms | 138,68 ms | 72,3% |
| Fevereiro/2025 | 5.796 | 415,74 ms | 118,24 ms | 71,6% |

| Trabalho por execucao | Todos antes/depois | Fevereiro antes/depois |
| --- | --- | --- |
| Definicoes de periodo | 40 / 1 | 42 / 1 |
| Filtragens completas | 21 / 1 | 23 / 2 |
| Consultas SQL | 3 / 3 | 3 / 3 |
| Montagens de metadados | 7 / 1 | 7 / 1 |

Os hashes SHA-256 do JSON completo retornado pelo servico, com chaves ordenadas,
foram iguais antes e depois. A ordem das listas faz parte dessa verificacao:

- Todos: `173ca60aa5baeadfcf4cbb6e9fc57b2b1165ceb47da6bfd56ecd99cd9408e80a`.
- Fevereiro: `55ccd08fab2076c7bc48ff65bd5cd81991021df05807a8e424dbc2502c3e233e`.

A resposta HTTP foi validada separadamente contra o contrato Pydantic existente.
Esse contrato converte alguns zeros do SLA de inteiro para float (`0.0`);
por isso o hash HTTP nao e o mesmo do JSON interno. Isso nao foi alterado.

## Garantias verificadas

- Dashboard equivalente aos endpoints individuais com os seis filtros.
- Recortes combinados calculados uma vez por chave durante a requisicao.
- Filtros ausentes, vazios e `all` compartilham recortes sem alterar metadados.
- Metadados retornados sao copias independentes, sem contaminacao entre paineis.
- Contextos aninhados preservam o contexto externo; sessoes sao independentes.
- Contexto liberado apos erros e apos sucesso; nova requisicao ve novos registros.
- Base vazia, comparacoes e filtros invalidos continuam cobertos por testes.

## Limites e divida tecnica

As linhas e agregacoes continuam em memoria. Os recortes guardam referencias,
nao copias completas das ocorrencias, e sao descartados ao fim da requisicao.
Ha custo adicional de listas para cada combinacao distinta de filtros.
Nao foi realizado teste de carga concorrente, medicao de memoria maxima ou
ensaio com bases maiores. Os numeros locais nao garantem a mesma latencia
em outro host ou sob carga. O cache de linhas existente continua sendo separado
do cache temporario da requisicao; nao foi substituido neste incremento.

Sem mudanca de schema ou nova migration. A automatizacao frontend usa API
simulada e nao substitui a validacao dos endpoints no banco real. Consulte
[o relatorio incremental](VALIDACAO_V0_3_1.md) para testes e backlog.
