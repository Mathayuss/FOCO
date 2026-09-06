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
GET /api/v1/analytics/overview
GET /api/v1/analytics/monthly
GET /api/v1/analytics/types
GET /api/v1/analytics/cities
GET /api/v1/analytics/hours
GET /api/v1/analytics/units
GET /api/v1/analytics/filters
GET /api/v1/analytics/sla
```

Parâmetros v0.3 nos endpoints de BI:
```text
source=historico | sejusp
fonte=historico | sejusp  # alias compatível em português
period=all | jan | fev | mar | abr | mai | jun | jul | q1 | q2 | last3
type=<tipificação>
municipality=<município>
unit=<unidade>
subtype=<subtipo>
shift=<turno>
```

A fonte padrão é `source=historico`, baseada no consolidado estático do MVP. Nessa fonte, somente `period` e `type` são filtráveis nos endpoints `overview`, `monthly` e `types`. Endpoints consolidados como `cities`, `hours` e `units` retornam metadados em `unavailable_filters` quando recebem filtros que ainda não podem ser aplicados sem agregações cruzadas.

A fonte `source=sejusp` lê as linhas importadas em `ocorrencia` com `sistema_origem=RELATORIO_SEJUSP`. Nessa fonte, `period`, `type`, `municipality`, `unit`, `subtype` e `shift` são filtros cruzados reais, calculados a partir do banco. O endpoint `/analytics/filters?source=sejusp` retorna os valores disponíveis conforme os dados importados.

Quando uma tipificação não aparece no top mensal histórico, a API retorna `null` naquele mês e marca `coverage.partial_type_series=true`. A ausência de granularidade não deve ser interpretada como zero.

## 6. Importações
```http
POST /api/v1/imports/preview
POST /api/v1/imports/csv/preview
POST /api/v1/imports
GET /api/v1/imports/{id}
```

O preview aceita arquivos CSV, XLS ou XLSX de até 512 MB, com validação de extensão, MIME, nome de arquivo e conteúdo UTF-8 quando CSV. Arquivos XLS podem ser planilhas HTML/TSV exportadas por sistemas legados ou XLS binário antigo quando a dependência `xlrd` estiver instalada. O parser detecta `;`, tabulação, vírgula e `|`, localiza a linha real de cabeçalho quando houver título acima da tabela e limpa marcações como `<br>` nos nomes das colunas.
Cabeçalhos canônicos obrigatórios: `id_origem`, `abertura_em`, `municipio` e `tipo`.
Cabeçalhos opcionais reconhecidos para persistência normalizada: `grupo`, `subtipo`, `unidade_operacional`, `bairro`, `endereco`, `registro_em`, `codigo_ibge`, `segredo_de_justica`, `latitude`, `longitude`, `codigo_viatura`, `tipo_viatura`, `despacho_em`, `saida_em`, `chegada_em`, `liberacao_em`, `retorno_em` e `disponibilidade_em`.
Cabeçalhos auxiliares reconhecidos para auditoria/rastreabilidade no preview e preservados em `dados_origem`: `forca`, `movimentacao`, `autoria`, `motivacao`, `uf_origem`, `municipio_origem`, `dia_registro`, `periodo_registro`, `faixa_idade`, `local`, `uf` e `area_municipio`.

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
A importação grava `sistema_origem=RELATORIO_SEJUSP`, `situacao=importada` e preserva a linha original em `dados_origem`.

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
