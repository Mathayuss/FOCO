# FOCO-060 - Diagnóstico consistente de codificação

## Versão analisada

FOCO v0.3.1, incremento de confiabilidade da importação CSV.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O detector incremental selecionava Windows-1252 após uma falha de UTF-8 sem
validar todo o conteúdo na codificação alternativa. Bytes reservados podiam gerar
uma exceção tardia e uma mensagem incorreta sobre suporte exclusivo a UTF-8. Agora
as duas codificações são validadas durante a mesma passagem e os endpoints de
prévia e confirmação apresentam o mesmo diagnóstico.

## Problemas críticos

Nenhum bloqueador conhecido após a correção.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- A seleção de codificação é automática e limitada a UTF-8 e Windows-1252.
- O formato XLS textual legado mantém sua regra própria de UTF-8 ou Latin-1.

## Problemas baixos

- O TestClient mantém o aviso de depreciação do alias `BlockingPortal`.

## Segurança

- Conteúdo com bytes inválidos é rejeitado antes da normalização e da persistência.
- A resposta não expõe traceback, conteúdo da linha nem detalhes internos do parser.
- As validações existentes de extensão, MIME, tamanho e bytes NUL foram preservadas.

## Backend

- O leitor incremental valida UTF-8 e Windows-1252 na mesma passagem pelo arquivo.
- A codificação é escolhida somente depois da finalização bem-sucedida do decoder.
- Serviço e endpoints usam a mesma mensagem de erro para evitar diagnósticos divergentes.

## Frontend

Nenhuma alteração necessária. A interface já apresenta o campo `detail` devolvido
pela API e passa a exibir o diagnóstico correto.

## Banco de dados

Nenhuma migration foi necessária e o teste HTTP inválido não persistiu dados. Após
a validação permaneceram 38.933 ocorrências, 14 lotes e 50 unidades operacionais.

## UX/UI

A mensagem identifica diretamente as duas codificações aceitas e permite corrigir
o arquivo sem sugerir incorretamente que apenas UTF-8 é suportado.

## Testes

- Regressão falhou antes da correção com a mensagem antiga de UTF-8.
- UTF-8 válido, Windows-1252 válido e byte inválido nas duas codificações aprovados.
- Prévia e confirmação inválidas retornaram HTTP 400 com a mesma mensagem.
- Backend no ambiente operacional: 93 aprovados, 0 falhos.
- Backend no PostgreSQL/PostGIS descartável: 93 aprovados, 0 falhos.
- Sonda na API ativa confirmou HTTP 400 e preservação das contagens do banco.

## Aderência ao roadmap

- Confiabilidade da importação atual: melhorada sem ampliar o escopo funcional.
- Contratos de BI e filtros da v0.3: preservados.
- Evolução ampla do pipeline de dados permanece planejada para a v0.4.

## Dívida técnica

- A prévia ainda não informa qual codificação válida foi detectada.
- Não há telemetria agregada sobre falhas de codificação por lote rejeitado.

## Recomendações para a equipe

1. Manter UTF-8 como formato preferencial para novas exportações.
2. Só adicionar seleção manual de codificação diante de uma fonte institucional não coberta.

## Backlog proposto

### FOCO-061

Título: Expor a codificação detectada na prévia da importação.

Descrição: Acrescentar ao contrato da prévia a codificação efetivamente usada para
ler arquivos CSV, facilitando suporte e auditoria sem registrar seu conteúdo.

Prioridade: Baixa.

Versão: v0.4.

Área: Dados e importação.

Arquivos envolvidos: serviço de importação, schema da prévia, endpoint e interface.

Critério de aceite: a prévia de CSV informa `utf-8` ou `windows-1252`, o campo é
testado e arquivos XLS/XLSX mantêm comportamento compatível.
