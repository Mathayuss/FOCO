# FOCO-068 - Acessibilidade do fluxo de importação

## Versão analisada

FOCO v0.3.1, incremento de acessibilidade e segurança de interação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

A seleção de planilhas dependia do mouse e o foco podia escapar do diálogo de
importação. O fluxo agora pode ser iniciado por teclado, mantém o foco dentro do
modal e impede fechamento acidental enquanto a API está processando o arquivo.

## Problemas críticos

Nenhum bloqueador conhecido após a implementação.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- Ainda não existe auditoria automatizada completa baseada em WCAG para todas as telas.

## Problemas baixos

- O comportamento de leitores de tela deve ser homologado com usuários e tecnologias assistivas reais.

## Segurança

- `Esc` não cancela nem oculta uma operação de upload ou consolidação em andamento.
- A alteração não modifica validação, conteúdo enviado ou permissões da API.
- A confirmação da importação continua explícita.

## Backend

Nenhuma alteração. Contratos e processamento de importação foram preservados.

## Frontend

- O seletor de arquivo possui semântica de botão, foco visível e ativação por Enter ou Espaço.
- O diálogo captura Tab e Shift+Tab para manter o foco nas ações disponíveis.
- Sem ações disponíveis, o foco permanece no próprio diálogo.
- Estados finais podem ser fechados com `Esc`; processamento ativo permanece protegido.
- O foco anterior é restaurado ao desmontar o diálogo.

## Banco de dados

Nenhuma migration ou escrita operacional. A prévia real executada não confirmou importação.

## UX/UI

- Usuários de teclado alcançam a mesma seleção e confirmação disponíveis por mouse.
- O indicador de foco usa a cor funcional já adotada pela identidade FOCO.
- O fluxo foi validado em desktop, notebook e celular sem alteração de layout.

## Testes

- Build TypeScript/Vite: aprovado.
- Tipagem da aplicação e dos testes: aprovada.
- Playwright: 120 aprovados, 0 falhos.
- Cenários executados em 1920x1080, 1366x768 e 390x844.
- Regressões reproduzidas antes da correção para seleção por teclado e contenção de foco.
- Prévia operacional somente leitura: 413 válidas, 0 novas, 413 existentes, ano 2026.
- Backend e banco não foram reexecutados; CI remoto e cobertura percentual não verificados.

## Aderência ao roadmap

- Melhoria incremental do fluxo existente, sem antecipar funcionalidades futuras.
- Reforça clareza e confiabilidade operacional da interface na v0.3.
- Não altera regras de negócio nem escopo de importação da v0.4.

## Dívida técnica

- Não há verificação automatizada ampla de contraste, nomes e landmarks em toda a aplicação.
- Homologação com leitor de tela permanece pendente.

## Recomendações para a equipe

1. Preservar a contenção de foco em novos diálogos.
2. Não permitir fechamento de modais durante operações não canceláveis.
3. Incluir auditoria acessível automatizada de forma gradual, começando pelos fluxos críticos.

## Backlog proposto

### FOCO-069

Título: Adicionar auditoria automatizada de acessibilidade aos fluxos críticos.

Descrição: integrar verificações de acessibilidade ao Playwright para dashboard,
filtros e importação, sem substituir homologação manual com tecnologia assistiva.

Prioridade: Média.

Versão: v0.3.

Área: Frontend e qualidade.

Arquivos envolvidos: configuração Playwright, testes de interface e workflow de CI.

Critério de aceite: os fluxos críticos não apresentam violações automáticas de
impacto crítico ou sério, com exceções justificadas e documentadas.
