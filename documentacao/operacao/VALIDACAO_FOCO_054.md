# FOCO-054 - Confirmação concorrente segura

## Versão analisada

FOCO v0.3.1, incremento de confiabilidade da importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O banco já protegia ocorrências por uma constraint única em `sistema_origem` e
`id_origem`, mas duas confirmações em workers diferentes ainda poderiam disputar
a mesma transação e produzir erro interno. A confirmação agora adquire um
advisory lock PostgreSQL não bloqueante e devolve `503` quando estiver ocupada.

## Problemas críticos

Nenhum bloqueador conhecido após os testes.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- O lock é global para confirmações, adequado ao worker atual, mas limita
  confirmações paralelas de fontes independentes.
- Pré-visualizações continuam limitadas somente pelo semáforo de cada worker.

## Problemas baixos

- O TestClient mantém o aviso de depreciação do alias `BlockingPortal`.

## Segurança

- A segunda confirmação não espera indefinidamente por recursos do banco.
- A resposta não expõe SQL, constraint ou detalhes internos.
- A transação sem lock executa rollback antes da resposta `503`.
- A constraint única permanece ativa como proteção definitiva.

## Backend

- PostgreSQL usa `pg_try_advisory_xact_lock` no início da persistência.
- O lock é liberado automaticamente no commit ou rollback.
- SQLite ignora o mecanismo específico e preserva compatibilidade de testes.
- A API responde `Retry-After: 2` para permitir nova tentativa controlada.

## Frontend

Nenhuma alteração visual. A mensagem retornada pela API é compatível com o
tratamento de falhas já existente na tela de importações.

## Banco de dados

Nenhuma migration foi necessária. A constraint `uq_ocorrencia_origem` já cobre
`sistema_origem + id_origem`. O teste operacional preservou 38.933 ocorrências e
14 lotes.

## UX/UI

Uma disputa previsível deixa de aparecer como erro interno e passa a orientar o
operador a tentar novamente em instantes.

## Testes

- Backend no ambiente operacional: 90 aprovados, 0 falhos.
- Backend no PostgreSQL/PostGIS descartável: 90 aprovados, 0 falhos.
- Testes focados de concorrência e confirmação: 6 aprovados, 0 falhos.
- Duas sessões PostgreSQL reais: primeira adquiriu, segunda foi rejeitada e
  adquiriu após a liberação.
- API operacional durante lock: `503`, `Retry-After: 2` e nenhuma persistência.

## Aderência ao roadmap

- Confiabilidade da importação atual: implementada sem mudar regra de negócio.
- Funcionalidades de BI da v0.3: preservadas.
- Fila distribuída e processamento assíncrono: não antecipados.

## Dívida técnica

- Concorrência é controlada globalmente, não por fonte ou lote.
- Não há métrica persistida para quantidade de confirmações recusadas.

## Recomendações para a equipe

1. Manter uma única confirmação ativa até existir processamento por fila.
2. Monitorar respostas `503` antes de considerar locks separados por fonte.

## Backlog proposto

### FOCO-055

Título: Medir contenção nas confirmações de importação.

Descrição: Incluir contador estruturado de confirmações recusadas por lock, sem
registrar nome de arquivo ou conteúdo sensível.

Prioridade: Baixa.

Versão: v0.4.

Área: Backend e observabilidade.

Arquivos envolvidos: endpoint e configuração de logs da importação.

Critério de aceite: cada recusa por concorrência incrementa métrica identificável
sem expor dados do arquivo ou do operador.
