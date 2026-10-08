# FOCO-058 - Rastreabilidade dos valores importados

## Versão analisada

FOCO v0.3.1, incremento de rastreabilidade da importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O leitor removia espaços externos de todas as células antes da normalização e da
criação de `dados_origem`. Os campos consolidados ficavam corretos, mas o payload
auditável não preservava o texto recebido. Agora cabeçalhos e campos operacionais
são normalizados separadamente dos valores textuais armazenados como origem.

## Problemas críticos

Nenhum bloqueador conhecido após a correção.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- O arquivo original não é arquivado byte a byte; o lote mantém somente SHA-256,
  metadados e payloads das linhas processadas.
- XLS HTML legado normaliza espaços de apresentação ao extrair texto das células.

## Problemas baixos

- O TestClient mantém o aviso de depreciação do alias `BlockingPortal`.

## Segurança

- Nenhum valor de origem passou a ser registrado em logs.
- O payload original permanece restrito às tabelas de ocorrência e rejeição.
- Uma política futura de arquivo bruto deve definir retenção, acesso e descarte de
  conteúdo sensível antes da implementação.

## Backend

- Cabeçalhos são limpos antes do mapeamento de equivalências.
- Valores brutos são transportados separadamente até `dados_origem`.
- Normalização de identificador, datas, município, tipo e unidade foi preservada.
- Linhas vazias e separadores continuam reconhecidos por conteúdo normalizado.

## Frontend

Nenhuma alteração necessária. O contrato da prévia e da confirmação permanece
inalterado.

## Banco de dados

Nenhuma migration foi necessária. O campo `dados_origem` já suporta o JSON textual.
A prévia operacional preservou 38.933 ocorrências, 14 lotes e 50 unidades.

## UX/UI

Sem alteração visual. A melhoria atende auditoria e diagnóstico de dados no backend.

## Testes

- Regressão falhou antes da correção ao encontrar valores já aparados no payload.
- Após a correção, campos consolidados ficaram normalizados e `dados_origem`
  preservou os espaços recebidos.
- Cabeçalhos Markdown, linha física, colunas extras e parser incremental aprovados.
- Backend no ambiente operacional: 92 aprovados, 0 falhos.
- Backend no PostgreSQL/PostGIS descartável: 92 aprovados, 0 falhos.
- Prévia operacional: 413 linhas válidas, 413 existentes e nenhuma persistência.

## Aderência ao roadmap

- Rastreabilidade da importação atual: melhorada sem mudar regra de negócio.
- Contratos de BI e filtros da v0.3: preservados.
- Política completa de retenção de arquivos: decisão de dados da v0.4.

## Dívida técnica

- Ausência de armazenamento controlado do arquivo bruto.
- Ausência de política institucional de retenção para arquivos com sigilo.

## Recomendações para a equipe

1. Não arquivar arquivos brutos antes de definir acesso, criptografia e descarte.
2. Usar o hash do lote para verificar identidade enquanto a política está pendente.

## Backlog proposto

### FOCO-059

Título: Definir retenção institucional do arquivo original.

Descrição: Documentar se o arquivo importado deve ser armazenado e estabelecer
prazo, criptografia, controle de acesso, auditoria e descarte seguro.

Prioridade: Média.

Versão: v0.4.

Área: Dados e segurança.

Arquivos envolvidos: ADR, serviço de importação e infraestrutura de armazenamento.

Critério de aceite: decisão arquitetural aprovada define retenção ou descarte e,
caso haja armazenamento, impede acesso não autorizado a arquivos sensíveis.
