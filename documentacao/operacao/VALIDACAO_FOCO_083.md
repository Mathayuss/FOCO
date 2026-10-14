# FOCO-083 - Criterios de aceite automatizados da v0.3

## Objetivo

Transformar as perguntas de aceite da v0.3 em verificacoes repetiveis, evitando
que um painel aplique um recorte diferente dos demais ou que a interface mostre
filtros e comparacoes inconsistentes com a API.

## Cenario controlado

O teste de backend cria somente dados descartaveis e inclui:

- ocorrencias que atendem aos seis filtros globais;
- base equivalente no mesmo mes do ano anterior;
- um registro de controle para cada dimensao divergente;
- um registro com fonte nao SEJUSP, que deve ficar fora do BI;
- uma ocorrencia cuja abertura e registro possuem anos diferentes, comprovando
  que o periodo analitico usa a data de registro.

## Matriz de aceite

| Pergunta | Evidencia automatizada |
| --- | --- |
| Quantas ocorrencias existem? | `overview.total` e somas dos paineis retornam o mesmo total. |
| Como o volume evoluiu? | Serie mensal usa somente o periodo filtrado. |
| Quais sao os principais tipos? | Tipificacao e topo usam o mesmo conjunto. |
| Quando ocorrem? | Horas e turnos somam o total filtrado. |
| Qual municipio e unidade? | Filtros aplicados e agregacoes preservam ambos. |
| Quais filtros estao ativos? | Os seis filtros aparecem na metadata e nos chips da interface. |
| Qual periodo esta sendo comparado? | Mes atual e mesmo mes do ano anterior aparecem com totais e variacao. |
| Os graficos respondem aos filtros? | Todos os paineis recebem a mesma metadata e a jornada navega entre as telas. |

## Camadas validadas

Backend real:

```bash
cd backend
.venv/bin/python -m pytest tests/test_aceite_v03.py -q
```

Frontend isolado:

```bash
cd frontend
pnpm exec playwright test tests/dashboard.spec.ts -g "envia os seis filtros"
```

O Playwright bloqueia chamadas externas e executa a jornada em desktop,
notebook e celular. O backend usa banco descartavel configurado pelo `pytest` e
nunca acessa a base operacional.

## Limite da evidência

Os testes das duas camadas compartilham o mesmo contrato, mas nao constituem um
ensaio com navegador conectado ao PostgreSQL operacional. Antes de homologar a
v0.3, ainda deve ser executado um smoke test somente leitura sobre uma release
implantada com dados institucionais autorizados.
