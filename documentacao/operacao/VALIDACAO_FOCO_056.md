# FOCO-056 - Reprocessamento sem unidades órfãs

## Versão analisada

FOCO v0.3.1, incremento de integridade da importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O reprocessamento consultava ocorrências duplicadas, mas criava todas as unidades
do arquivo antes de ignorar essas linhas. Um `id_origem` existente com unidade
divergente podia, portanto, cadastrar uma unidade sem ocorrência. Agora somente
linhas realmente novas participam da criação de unidades.

## Problemas críticos

Nenhum bloqueador conhecido após a correção.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- Unidades órfãs eventualmente criadas por versões anteriores não podem ser
  removidas automaticamente sem distinguir cadastro institucional legítimo.

## Problemas baixos

- O TestClient mantém o aviso de depreciação do alias `BlockingPortal`.

## Segurança

Sem alteração de autenticação ou exposição de dados. A correção reduz escrita
desnecessária e mantém a transação, o advisory lock e a constraint de origem.

## Backend

- Identificadores existentes são consultados antes da criação de unidades.
- Nomes de unidade são derivados apenas das linhas realmente inseríveis.
- Linhas duplicadas continuam contabilizadas no lote.
- A ocorrência existente não é atualizada silenciosamente pelo reprocessamento.

## Frontend

Nenhuma alteração necessária. Contagens de inseridas e duplicadas permanecem com
o mesmo contrato.

## Banco de dados

Nenhuma migration foi necessária. A validação operacional preservou 38.933
ocorrências, 14 lotes e 50 unidades operacionais. Uma consulta somente leitura
identificou 1 unidade sem ocorrências e sem viaturas; nenhum registro foi alterado.

## UX/UI

Sem mudança visual. O resultado do reprocessamento continua informando as linhas
ignoradas como duplicadas.

## Testes

- Regressão falhou antes da correção ao encontrar a unidade órfã.
- Regressão aprovada após restringir as unidades às ocorrências novas.
- Backend no ambiente operacional: 91 aprovados, 0 falhos.
- Backend no PostgreSQL/PostGIS descartável: 91 aprovados, 0 falhos.
- Prévia da planilha operacional: 413 linhas válidas, 413 existentes e 0 novas.
- Prévia não alterou ocorrências, lotes ou unidades.

## Aderência ao roadmap

- Integridade da importação atual: corrigida.
- Contratos de BI e filtros da v0.3: preservados.
- Administração completa de unidades da v0.6: não antecipada.

## Dívida técnica

- Não existe relatório específico para unidades sem ocorrências ou viaturas.
- A unidade atualmente sem vínculos requer classificação institucional antes de
  qualquer inativação ou exclusão.

## Recomendações para a equipe

1. Não excluir unidades existentes apenas por ausência de ocorrência.
2. Auditar origem, vínculo e atividade das unidades na versão v0.6.

## Backlog proposto

### FOCO-057

Título: Auditar unidades operacionais sem vínculos.

Descrição: Gerar relatório somente leitura com unidades sem ocorrências e sem
viaturas, incluindo origem e data de criação quando esses campos existirem.

Prioridade: Baixa.

Versão: v0.6.

Área: Banco de dados e unidades.

Arquivos envolvidos: serviço de unidades, modelos e relatório administrativo.

Critério de aceite: a equipe consegue revisar unidades sem vínculos antes de
qualquer decisão manual de inativação ou exclusão.
