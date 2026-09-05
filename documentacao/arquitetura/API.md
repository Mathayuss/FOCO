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
period=all | q1 | q2 | last3
type=<tipificação>
municipality=<município>
unit=<unidade>
subtype=<subtipo>
shift=<turno>
```

Na fonte histórica atual, somente `period` e `type` são filtráveis nos endpoints `overview`, `monthly` e `types`. Endpoints consolidados como `cities`, `hours` e `units` retornam metadados em `unavailable_filters` quando recebem filtros que ainda não podem ser aplicados sem agregações cruzadas.

Quando uma tipificação não aparece no top mensal, a API retorna `null` naquele mês e marca `coverage.partial_type_series=true`. A ausência de granularidade não deve ser interpretada como zero.

## 6. Importações
```http
POST /api/v1/imports/csv/preview
POST /api/v1/imports
GET /api/v1/imports/{id}
```

O preview CSV aceita arquivos de até 512 MB, com validação de extensão, MIME, nome de arquivo e conteúdo UTF-8.
Cabeçalhos canônicos obrigatórios: `id_origem`, `abertura_em`, `municipio` e `tipo`.
Cabeçalhos opcionais reconhecidos: `subtipo`, `latitude`, `longitude`, `codigo_viatura`, `tipo_viatura`, `despacho_em`, `saida_em`, `chegada_em`, `liberacao_em`, `retorno_em` e `disponibilidade_em`.
Aliases antigos em inglês são aceitos somente como compatibilidade de importação; o padrão FOCO permanece em português.

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
