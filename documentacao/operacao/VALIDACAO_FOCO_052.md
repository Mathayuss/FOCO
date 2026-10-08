# FOCO-052 - Leitura incremental de CSV

## Versão analisada

FOCO v0.3.1, incremento autorizado de confiabilidade da importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O backend deixou de copiar integralmente o upload para validar tamanho e calcular
o hash. CSV agora é percorrido como fluxo a partir do arquivo temporário do
multipart, preservando cabeçalhos, validações, rejeições e deduplicação já
existentes. A prévia não retém os registros normalizados completos. XLS e XLSX
continuam compatíveis, mas o conteúdo bruto desses formatos ainda é lido em memória.

## Problemas críticos

Nenhum bloqueador conhecido após os testes.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- XLS e XLSX ainda são materializados integralmente em memória pelo parser.
- Os registros normalizados permanecem em memória até a confirmação da transação.
- Somente a primeira planilha de um XLS/XLSX é processada.

## Problemas baixos

- O TestClient emite aviso de depreciação do alias `BlockingPortal`.

## Segurança

- Nome, extensão, MIME e limite de 512 MB continuam validados.
- Tamanho conhecido acima do limite é rejeitado antes da abertura do arquivo.
- Tamanho desconhecido é contado em blocos e interrompido ao ultrapassar o limite.
- SHA-256 é calculado sem criar uma cópia integral adicional do upload.
- CSV com byte NUL, aspas inválidas ou estrutura malformada é rejeitado.
- Apenas uma importação pesada é executada por worker.

## Backend

- `_prepare_upload` percorre o arquivo temporário em blocos de 1 MB e reposiciona
  o cursor antes do parser.
- CSV usa decodificador incremental para UTF-8 ou fallback Windows-1252.
- Cabeçalho é localizado nas primeiras 50 linhas e as linhas seguintes são
  consumidas por iterador.
- Prévia mantém somente IDs válidos, anos, contadores e as primeiras 50 rejeições.
- Confirmação mantém os registros completos para preservar a transação atômica.
- Prévia e confirmação usam o mesmo resultado normalizado.
- A API mantém contratos, códigos HTTP e compatibilidade CSV/XLS/XLSX.

## Frontend

Nenhuma alteração funcional neste incremento. O contrato e o limite exibido de
512 MB foram preservados; o build TypeScript/Vite foi aprovado.

## Banco de dados

Nenhuma migration foi necessária. Prévia operacional preservou 38.933
ocorrências e 14 lotes. Tabelas e colunas continuam em português.

## UX/UI

Sem mudança visual. Mensagens de arquivo vazio, limite excedido, concorrência e
falha estrutural permanecem específicas e acionáveis.

## Testes

- Backend no PostgreSQL/PostGIS operacional: 87 aprovados, 0 falhos.
- Backend em PostgreSQL/PostGIS descartável, criado por migrations: 87 aprovados, 0 falhos.
- Casos focados do fluxo incremental: 8 aprovados, 0 falhos.
- Infraestrutura: 22 testes e 26 subtestes aprovados.
- Build TypeScript/Vite: aprovado.
- Medição sintética com 20 mil linhas: pico rastreado de 28,34 MiB no modo
  completo e 3,67 MiB na prévia leve, redução aproximada de 87%.
- Planilha `documentacao/importados/relatorio(2).xls`, somente prévia: 413 linhas
  válidas, 0 inválidas, ano 2026, 1 linha sigilosa e 9 sem coordenadas completas.
- As 413 ocorrências da planilha já existiam; a prévia não criou lote nem ocorrência.

## Aderência ao roadmap

- Visão Geral e integração com dados SEJUSP da v0.3: preservadas.
- Confiabilidade da importação: melhoria arquitetural necessária e incremental.
- Importação CSV incremental: implementada.
- Importação XLS/XLSX incremental: não implementada; planejada para v0.4.
- Processamento assíncrono em fila: não implementado e não antecipado.

## Dívida técnica

- Materialização dos registros normalizados durante o processamento.
- Leitura integral do conteúdo XLS/XLSX.
- Ausência de seleção explícita da aba.

## Recomendações para a equipe

1. Medir pico de memória com CSV próximo ao limite antes de homologar 512 MB.
2. Na v0.4, processar XLSX em modo somente leitura e lotes transacionais.
3. Definir regra de seleção de aba antes de aceitar planilhas com múltiplas abas.

## Backlog proposto

### FOCO-053

Título: Processar XLSX em modo incremental.

Descrição: Ler células em modo somente leitura e persistir por lotes controlados,
sem perder a atomicidade e a auditoria da importação.

Prioridade: Média.

Versão: v0.4.

Área: Backend e dados.

Arquivos envolvidos: `backend/app/services/import_service.py` e testes de importação.

Critério de aceite: uma planilha XLSX grande respeita o limite configurado, mantém
o pico de memória documentado e produz os mesmos resultados do parser atual.
