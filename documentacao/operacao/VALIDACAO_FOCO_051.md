# FOCO-051 - Importação confiável de planilhas

## Versão analisada

FOCO v0.3.1, incremento autorizado do fluxo de importação.

## Status

APROVADO COM RESSALVAS.

## Resumo executivo

O fluxo CSV/XLS/XLSX passou a separar bloqueios estruturais, rejeições por linha
e avisos de qualidade. A confirmação aceita somente arquivos sem bloqueio e com
ao menos uma linha válida. O lote preserva as rejeições e a linha original.

## Problemas críticos

Nenhum bloqueador conhecido após os testes.

## Problemas altos

Nenhum problema alto aberto neste incremento.

## Problemas médios

- Um arquivo aceito ainda é carregado integralmente em memória pelo parser.
- Somente a primeira planilha de um XLS/XLSX é processada.
- A suíte Playwright não iniciou no host por ausência de `libnss3.so`.

## Problemas baixos

- O TestClient emite aviso de depreciação do alias `BlockingPortal`.

## Segurança

- Extensão, MIME, nome e tamanho continuam validados.
- XLSX corrompido, excessivamente expandido ou com compactação suspeita é rejeitado.
- CSV binário ou estruturalmente malformado é rejeitado.
- Cabeçalhos duplicados/ambíguos são bloqueados antes de qualquer insert.
- Arquivo acima do limite é rejeitado antes da leitura quando o tamanho é conhecido.
- Apenas uma prévia ou confirmação pesada é processada por worker.
- Falhas inesperadas na confirmação executam rollback explícito.

## Backend

- CSV UTF-8 e Windows-1252.
- Diagnóstico amigável para XLS/XLSX corrompido.
- Datas e horários inválidos não são mais ignorados.
- Limites de colunas e campos compatíveis com o banco.
- Código IBGE normalizado e validado com sete dígitos.
- Hash SHA-256 comparado com o histórico durante a prévia.
- Lote, situação e data da importação anterior retornados quando o arquivo já foi processado.
- Exportações equivalentes detectadas por `sistema_origem + id_origem`, com contagem de linhas existentes e novas.
- Latitude validada em -90..90 e longitude em -180..180.
- Pares geográficos incompletos ou inválidos são persistidos como ausentes.
- Anos calculados somente a partir de linhas válidas, priorizando o registro.
- Rotas pesadas executadas no thread pool, sem bloquear o event loop.
- Concorrência de importação limitada por worker, com resposta `503` e `Retry-After`.

## Frontend
- Arquivo repetido recebe aviso visual e referência ao lote anterior.
- Quando todas as ocorrências já existem, a ação é apresentada como registro de reprocessamento.

- Limite padrão exibido em 512 MB.
- Configuração acima de 512 MB é rejeitada; CI verifica igualdade entre API e interface.
- Botão de confirmação respeita `can_commit`.
- Bloqueios estruturais aparecem separados dos problemas por linha.
- Importação parcial válida é identificada como pronta com ressalvas.

## Banco de dados

Nenhuma migration foi necessária. Os nomes de tabelas e colunas permanecem em
português. A suíte PostgreSQL/PostGIS descartável confirmou as restrições reais.

## UX/UI

O operador recebe uma distinção clara entre bloqueio do arquivo, linha rejeitada
e aviso que não impede a importação. Arquivos já processados são destacados sem
retirar a opção de reprocessamento intencional.

## Testes

- Backend SQLite isolado: 83 aprovados, 0 falhos.
- Backend PostgreSQL/PostGIS descartável: 83 aprovados, 0 falhos.
- Infraestrutura e consistência do Compose: 22 aprovados, 0 falhos.
- Testes focados de importação: 22 aprovados, 0 falhos.
- Testes específicos de XLS HTML híbrido: 2 aprovados, 0 falhos.
- TypeScript e build Vite: aprovados.
- Playwright: 102 não iniciados por dependência `libnss3.so` ausente no host.
- Planilha de referência, somente preview: 38.539 linhas; 38.520 válidas;
  19 rejeitadas por município ausente; ano 2025; nenhum bloqueio estrutural.
- Duas prévias reais simultâneas da planilha de referência: uma respondeu `200`
  e a concorrente `503`; ocorrências e lotes permaneceram inalterados.
- `documentacao/importados/relatorio(2).xls`, somente preview: primeira linha
  reconhecida; 413 linhas válidas; 0 inválidas; ano 2026; nenhuma coluna ignorada;
  413 ocorrências já existentes e 0 novas; nenhum lote criado pela prévia.

## Aderência ao roadmap

- Importação CSV/XLS/XLSX: implementada.
- Validação e normalização: implementadas para o leiaute atual.
- Auditoria de lotes e rejeições: implementada.
- Processamento assíncrono/streaming: não implementado; pertence à evolução v0.4.

## Dívida técnica

- Leitura integral do upload e materialização de todas as linhas em memória.
- Ausência de escolha explícita da aba da planilha.
- Ausência de teste visual específico da página de importações.

## Recomendações para a equipe

1. Priorizar processamento em arquivo temporário e lotes para arquivos grandes.
2. Tornar a aba importada explícita quando houver mais de uma.
