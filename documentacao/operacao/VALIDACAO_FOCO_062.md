# FOCO-062 - Progresso visual da importação

## Versão analisada

FOCO v0.3.1, incremento de UX e confiabilidade percebida da importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

A seleção e a confirmação de planilhas não ofereciam resposta visual suficiente
durante operações demoradas. A interface agora mantém um diálogo modal visível
durante todo o envio e processamento, identifica a etapa atual e só libera a
tela quando a API responde ou apresenta erro.

## Problemas críticos

Nenhum bloqueador conhecido após a implementação.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- A API não publica progresso interno por linha; após o envio, a barra é
  corretamente apresentada como indeterminada.

## Problemas baixos

- Ainda não existe ação para cancelar voluntariamente um upload em andamento.

## Segurança

- O modal exibe somente nome e tamanho do arquivo, sem conteúdo das ocorrências.
- O contrato, CORS e as validações do backend permanecem inalterados.
- A tela bloqueada impede disparos concorrentes acidentais pelo mesmo usuário.

## Backend

Nenhuma alteração. Prévia e confirmação mantêm os contratos existentes.

## Frontend

- O cliente HTTP usa `XMLHttpRequest` apenas nos uploads para obter progresso real.
- Erros HTTP continuam convertidos para `ApiError`; falhas de rede recebem mensagem em português.
- Prévia diferencia envio e análise; confirmação diferencia envio, consolidação e histórico.
- O diálogo gerencia foco, bloqueio de rolagem e restauração ao concluir.

## Banco de dados

Nenhuma migration ou operação de escrita foi realizada durante a validação visual.

## UX/UI

- Modal institucional e compacto, alinhado ao dashboard dark do FOCO.
- Percentual exibido somente durante o envio mensurável.
- Processamento do servidor usa indicador indeterminado, sem inventar prazo.
- Layout inspecionado em desktop e celular, sem corte ou overflow.

## Testes

- Build TypeScript/Vite: aprovado.
- Tipagem da aplicação e dos testes: aprovada.
- Playwright: 108 aprovados, 0 falhos.
- Modal exercitado em 1920x1080, 1366x768 e 390x844.
- Cobertos prévia pendente, confirmação pendente, bloqueio e restauração da rolagem.
- Verificada permanência integral do diálogo dentro de cada viewport.

## Aderência ao roadmap

- Melhora a usabilidade do fluxo atual sem alterar regras de importação.
- Mantém o foco operacional da v0.3 e prepara a confiabilidade da v0.4.
- Não antecipa integrações automáticas nem processamento assíncrono distribuído.

## Dívida técnica

- O backend ainda não fornece telemetria de progresso do processamento interno.
- O upload não pode ser cancelado pela interface após iniciado.

## Recomendações para a equipe

1. Manter o estado indeterminado enquanto não houver progresso confiável no backend.
2. Não estimar tempo restante com base apenas no tamanho do arquivo.

## Backlog proposto

### FOCO-063

Título: Permitir cancelamento seguro durante o envio da planilha.

Descrição: Disponibilizar cancelamento enquanto os bytes ainda estão sendo enviados,
abortando a requisição no navegador sem criar lote ou persistir linhas.

Prioridade: Baixa.

Versão: v0.4.

Área: Frontend e importação.

Arquivos envolvidos: cliente HTTP, diálogo de progresso e testes Playwright.

Critério de aceite: o botão de cancelamento aparece somente durante o envio,
aborta a requisição, restaura a tela e não cria registros no banco de dados.
