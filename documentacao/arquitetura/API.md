# FOCO — Diretrizes da API

## 1. Base
```text
/api/v1
```

## 2. Princípios
- REST quando aplicável;
- JSON;
- schemas Pydantic;
- versionamento;
- paginação;
- filtros explícitos;
- erros padronizados.

## 3. Health
```http
GET /api/v1/health
```

## 4. Ocorrências
```http
GET /api/v1/occurrences
GET /api/v1/occurrences/{id}
```

Filtros previstos:
```text
start_date
end_date
municipality_id
unit_id
type
subtype
shift
vehicle_id
source_id
```

## 5. Analytics
```http
GET /api/v1/analytics/dashboard
GET /api/v1/analytics/overview
GET /api/v1/analytics/monthly
GET /api/v1/analytics/types
GET /api/v1/analytics/cities
GET /api/v1/analytics/hours
GET /api/v1/analytics/units
GET /api/v1/analytics/shifts
GET /api/v1/analytics/filters
GET /api/v1/analytics/sla
```

Parâmetros v0.3 nos endpoints de BI:
```text
source=sejusp
fonte=sejusp  # alias compatível em português
period=all | ano-AAAA | AAAA-MM | AAAA-qN
type=<tipificação>
municipality=<município>
unit=<unidade>
subtype=<subtipo>
shift=<turno>
```


A fonte padrão e única `source=sejusp` lê as linhas importadas em `ocorrencia` com `sistema_origem=RELATORIO_SEJUSP`. Nessa fonte, `period`, `type`, `municipality`, `unit`, `subtype` e `shift` são filtros cruzados reais, calculados a partir do banco. O endpoint `/analytics/filters?source=sejusp` aceita os mesmos parâmetros de BI e retorna os valores disponíveis no recorte atual, mantendo o próprio campo selecionado aberto para troca.


O endpoint `/analytics/dashboard` retorna `filters`, `overview`, `monthly`, `types`, `cities`, `hours`, `units`, `shifts` e `sla` em uma chamada. Os filtros sao validados uma vez e os paineis SEJUSP reutilizam a mesma leitura de linhas durante a requisicao. Todos os endpoints individuais continuam disponiveis, com respostas equivalentes. O campo `sla` preserva o comportamento global de `/analytics/sla`; ele nao e um indicador calculado sobre os filtros desta chamada.

Quando `period=ano-AAAA`, `overview.comparison` e `monthly.comparison` usam os mesmos meses contínuos com cobertura no ano anterior. Meses adicionais do ano atual permanecem no total do período, mas não entram na variação sem base equivalente. `current_label`, `baseline_label` e `reason` informam explicitamente o intervalo comparado. Para mês, trimestre e demais recortes, permanece a comparação com o período imediatamente anterior de mesma duração.

O frontend cancela o carregamento anterior ao trocar filtros ou sair do painel, e ignora respostas substituidas. O cancelamento no navegador nao garante a interrupcao de um calculo ja iniciado no servidor.

## 6. Importações
```http
POST /api/v1/imports/preview
POST /api/v1/imports/csv/preview
POST /api/v1/imports
GET /api/v1/imports/lotes
GET /api/v1/imports/lotes/{id_lote_importacao}
GET /api/v1/imports/lotes/{id_lote_importacao}/rejeicoes
```

`GET /api/v1/imports/lotes` aceita `limite` e `deslocamento`. As respostas usam campos em português, como `id_lote_importacao`, `nome_arquivo`, `linhas_inseridas`, `linhas_invalidas` e `situacao`.

Prévia e confirmação informam `registration_periods` (`YYYY-MM`) e a quantidade
de linhas válidas sem data de registro. O histórico do lote expõe esses valores
como `periodos_registro` e `linhas_validas_sem_data_registro`. `periodos_registro`
é `null` para lotes antigos sem cobertura auditável, lista vazia quando o lote
novo não tem data de registro válida e lista de meses distintos nos demais.

O preview aceita arquivos CSV, XLS ou XLSX de até 512 MB. O limite pode ser reduzido por `LIMITE_IMPORTACAO_MB` e `VITE_LIMITE_IMPORTACAO_MB`, mas não pode exceder 512 MB e deve ser igual no backend e no frontend. A validação também cobre extensão, MIME e nome. CSV aceita UTF-8 ou Windows-1252 e rejeita conteúdo binário. Arquivos XLS podem ser planilhas HTML/TSV exportadas por sistemas legados ou XLS binário antigo quando a dependência `xlrd` estiver instalada. O parser detecta `;`, tabulação, vírgula e `|`, localiza a linha real de cabeçalho quando houver título acima da tabela e limpa marcações como `<br>` nos nomes das colunas.

O backend calcula tamanho e SHA-256 do upload em blocos de 1 MB sobre o arquivo temporário do multipart. O caminho CSV também valida integralmente UTF-8 e Windows-1252 e percorre as linhas incrementalmente, sem criar uma cópia integral adicional do conteúdo. Se ambas as codificações forem inválidas, prévia e confirmação retornam HTTP 400 com `CSV deve estar em UTF-8 ou Windows-1252`. A prévia conserva somente identificadores válidos, anos, contadores e até 50 rejeições; os registros normalizados completos são mantidos apenas durante a confirmação. XLS e XLSX ainda são materializados em memória pelo parser compatível; por isso somente uma prévia ou confirmação pesada é aceita simultaneamente por worker.

Quando o multipart informa o tamanho, arquivos acima do limite retornam `413` antes da leitura do conteúdo. Prévia e confirmação são executadas no thread pool e limitadas a uma operação pesada simultânea por worker; uma segunda tentativa recebe `503` e `Retry-After: 2`. Isso preserva a resposta das demais rotas, mas o arquivo aceito ainda é materializado em memória pelo parser atual.

Em XLS HTML com tags ASCII e conteúdo de células codificado com bytes NUL intercalados, o leitor normaliza somente o conteúdo textual antes de reconhecer o cabeçalho. Quando a primeira linha contém os campos obrigatórios, ela é usada diretamente como definição das colunas. Datas no formato `dd/mm/aaaa - hh:mm:ss` também são aceitas.

Pacotes XLSX passam por validação estrutural, limite de 1 GB descompactado e detecção de taxa de compactação suspeita. Cabeçalhos duplicados ou que apontem para o mesmo campo são bloqueados para impedir sobrescrita silenciosa. A prévia também valida datas, horários, tamanhos máximos dos campos, código IBGE, duplicidade do identificador e faixas geográficas; latitude deve estar entre -90 e 90 e longitude entre -180 e 180.

`validation_errors` contém bloqueios do arquivo. `issues` contém rejeições por linha. Quando não há bloqueio estrutural e existe ao menos uma linha válida, `can_commit=true` permite importar o subconjunto válido; linhas rejeitadas continuam auditadas. `registration_years` considera somente linhas válidas e prioriza a data de registro.

A prévia compara o SHA-256 do conteúdo com o histórico de lotes. Quando houver correspondência, `already_imported=true` e os campos `previous_import_batch_id`, `previous_import_status` e `previous_import_at` identificam o processamento mais recente. O aviso não altera `can_commit`: um reprocessamento intencional continua permitido e a deduplicação por ocorrência permanece ativa na confirmação.

A confirmação em `POST /api/v1/imports` usa um advisory lock transacional não bloqueante no PostgreSQL. Se outra confirmação estiver ativa em outro worker ou instância, a API responde `503 Service Unavailable` com `Retry-After: 2`; nenhuma linha ou lote parcial é gravado. A constraint única de `sistema_origem + id_origem` continua sendo a garantia final contra duplicidade.

Antes de criar unidades operacionais, a confirmação consulta quais identificadores de origem já existem. Somente unidades referenciadas por ocorrências realmente novas podem ser cadastradas; uma linha descartada como duplicada não altera `unidade_operacional`, mesmo quando o arquivo reprocessado informa outro nome de unidade.

Como arquivos diferentes podem representar as mesmas ocorrências, a prévia também consulta `sistema_origem + id_origem` em blocos. `existing_rows` informa quantas linhas válidas já estão consolidadas e `new_rows` quantas seriam inseridas. Essa verificação não grava lote nem ocorrência.
Cabeçalhos canônicos obrigatórios: `id_origem`, `abertura_em`, `municipio` e `tipo`.
Cabeçalhos opcionais reconhecidos para persistência normalizada: `grupo`, `subtipo`, `unidade_operacional`, `bairro`, `endereco`, `registro_em`, `codigo_ibge`, `segredo_de_justica`, `latitude`, `longitude`, `codigo_viatura`, `tipo_viatura`, `despacho_em`, `saida_em`, `chegada_em`, `liberacao_em`, `retorno_em` e `disponibilidade_em`.
Cabeçalhos auxiliares reconhecidos para auditoria/rastreabilidade no preview e preservados em `dados_origem`: `forca`, `movimentacao`, `autoria`, `motivacao`, `uf_origem`, `municipio_origem`, `dia_registro`, `periodo_registro`, `faixa_idade`, `local`, `uf`, `area_municipio`, `tempo_atendimento`, `despacho` e `especial`.

Relatórios SEJUSP são aceitos por equivalência automática de cabeçalhos. O leiaute oficial está documentado em `documentacao/dados/LEIAUTE_IMPORTACAO_SEJUSP.md`.


| SEJUSP | FOCO |
|---|---|
| `Nº/ANO` | `id_origem` |
| `DATA DO FATO` + `HORA DO FATO` | `abertura_em` |
| `DATA DO REGISTRO` + `HORA DO REGISTRO` | `registro_em` |
| `MUNICÍPIO` | `municipio` |
| `FATO` | `tipo` |
| `FATO AGRUPADO` | `grupo` |
| `CATEGORIA` | `subtipo` |
| `UNIDADE DE ORIGEM` | `unidade_operacional` |
| `CÓDIGO IBGE` | `codigo_ibge` |
| `SEGREDO DE JUSTIÇA` | `segredo_de_justica` |
| `BAIRRO` | `bairro` |
| `LOGRADOURO` + `REFERÊNCIA` | `endereco` |
| `LATITUDE` | `latitude` |
| `LONGITUDE` | `longitude` |

Aliases antigos em inglês são aceitos somente como compatibilidade de importação; o padrão FOCO permanece em português.
A importação grava `sistema_origem=RELATORIO_SEJUSP`, `situacao=importada` e preserva em `dados_origem` os valores textuais recebidos nas células CSV/XLSX. Os campos consolidados continuam normalizados, portanto espaços externos podem existir no payload original sem aparecer em `id_origem`, município, tipo ou unidade. XLS HTML legado normaliza espaços de apresentação durante a leitura da tabela. O arquivo binário original não é arquivado pelo backend; o lote conserva seu SHA-256 para rastreabilidade. Também é registrado um lote em `lote_importacao`; linhas inválidas são preservadas em `linha_importacao_rejeitada` com motivos e payload original.

## 7. Integrações
```http
GET /api/v1/integrations
POST /api/v1/integrations/{id}/sync
GET /api/v1/integrations/{id}/status
```

## 8. Erro padrão
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Dados inválidos.",
    "details": []
  },
  "request_id": "..."
}
```

## 9. Paginação
```json
{
  "items": [],
  "page": 1,
  "page_size": 50,
  "total": 0
}
```

## 10. OpenAPI
- `/docs`
- `/redoc`

Mudanças incompatíveis exigem nova versão da API.
