# FOCO-066 - Confirmação e resultado no diálogo de importação

## Versão analisada

FOCO v0.3.1, incremento de UX e confiabilidade percebida da importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O diálogo anterior informava apenas o processamento e desaparecia ao fim da
prévia. Agora ele acompanha o ciclo completo: análise, decisão explícita do
usuário, confirmação e resultado. Sucesso, duplicidade e erro são apresentados
no mesmo contexto, com contadores retornados pela API.

## Problemas críticos

Nenhum bloqueador conhecido após a implementação.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- A confirmação continua síncrona. Fechar a aba ou perder a conexão durante uma
  importação longa não permite recuperar o estado da operação pela interface.

## Problemas baixos

- O cancelamento voluntário do upload permanece no backlog FOCO-063.

## Segurança

- A prévia continua sem persistir ocorrências e exige confirmação explícita.
- O diálogo mostra nome, tamanho e contadores, sem expor conteúdo das linhas.
- Botões de confirmação não ficam disponíveis durante uma requisição ativa.
- Validação de arquivo, MIME, limite, normalização e deduplicação permanecem no backend.

## Backend

Nenhuma alteração. Os contratos de prévia e confirmação foram preservados.

## Frontend

- O diálogo permanece aberto após a prévia e oferece `Importar agora`.
- Duplicidade total é diferenciada antes e depois do reprocessamento.
- Erros de análise e confirmação exibem a mensagem retornada pela API.
- Resultado concluído detalha linhas inseridas, duplicadas e inválidas.
- Lotes SEJUSP aceitos oferecem acesso direto ao dashboard correspondente.

## Banco de dados

Nenhuma migration ou alteração de modelo. Os testes usam respostas simuladas e
não escrevem dados operacionais.

## UX/UI

- Estados possuem sinais visuais distintos para pronto, sucesso, duplicidade e erro.
- Ações permanecem dentro do diálogo em desktop, notebook e celular.
- Rolagem da página é restaurada ao fechar o diálogo.
- O resultado não desaparece automaticamente, permitindo leitura e decisão do usuário.

## Testes

- Build TypeScript/Vite: aprovado.
- Tipagem da aplicação e dos testes: aprovada.
- Playwright: 117 aprovados, 0 falhos.
- Casos novos exercitados em 1920x1080, 1366x768 e 390x844.
- Cobertos análise concluída, confirmação, sucesso, duplicidade total e erro da API.
- Backend e banco não foram alterados nem reexecutados neste incremento.
- CI remoto e cobertura percentual não verificados.

## Aderência ao roadmap

- Incremento aderente à confiabilidade do fluxo existente e à preparação da v0.4.
- Não antecipa integrações automáticas, filas distribuídas ou módulos futuros.
- Não altera regras de negócio da consolidação de ocorrências.

## Dívida técnica

- Operações longas ainda não possuem identificador consultável nem recuperação de estado.
- O frontend ainda mantém, por compatibilidade, uma segunda ação de importação na página.

## Recomendações para a equipe

1. Manter a confirmação explícita após toda prévia, inclusive para reprocessamentos.
2. Tratar processamento assíncrono recuperável somente no escopo de dados e importação.
3. Avaliar a remoção futura da ação duplicada da página após homologação do novo diálogo.

## Backlog proposto

### FOCO-067

Título: Recuperar o estado de importações longas.

Descrição: fornecer identificador de operação consultável para que a interface
recupere resultado ou falha após perda de conexão ou reabertura da tela.

Prioridade: Média.

Versão: v0.4.

Área: Backend, frontend e importação.

Arquivos envolvidos: endpoints de importação, serviço de lotes, cliente HTTP,
diálogo de importação e testes de integração.

Critério de aceite: uma confirmação iniciada pode ser consultada por identificador
até apresentar estado concluído ou falho, sem repetir inserções.
