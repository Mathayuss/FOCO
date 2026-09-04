# AGENTES.md — FOCO

## Marcador

```text
[FOCO-PADRAO:v2]
```

## Idioma obrigatório

Todo identificador criado pela equipe deve estar em português.

Exemplos:

```text
ARQUITETURA.md
ocorrencia
unidade_operacional
buscar_ocorrencias()
ServicoImportacao
municipioSelecionado
```

Evitar:

```text
ARCHITECTURE.md
occurrence
operational_unit
get_occurrences()
ImportService
selectedMunicipality
```

## Exceções

Somente quando exigidas por ferramenta ou padrão externo:

```text
Dockerfile
package.json
FastAPI
React
PostgreSQL
PostGIS
HTTP
JSON
OIDC
LDAP
```

## Antes de alterar o projeto

Ler:

- `documentacao/arquitetura/ARQUITETURA.md`
- `documentacao/produto/ROTEIRO_DE_VERSOES.md`
- `documentacao/dados/MODELO_DE_DADOS.md`
- `documentacao/arquitetura/INTERFACE_API.md`
- `documentacao/seguranca/SEGURANCA.md`
- `documentacao/ux-ui/EXPERIENCIA_INTERFACE.md`
- `documentacao/ux-ui/IDENTIDADE_VISUAL.md`
- `documentacao/produto/AREAS_OPERACIONAIS.md`
- `documentacao/produto/PADRAO_NOMENCLATURA.md`

## Regra territorial

Áreas operacionais são normativas e versionadas.

Nunca inferir limite apenas pela proximidade.

## Regra de dados

Nunca misturar:

- REAL;
- HISTORICO_AGREGADO;
- DEMONSTRATIVO.

## Dúvida

Usar:

```text
DECISAO_PENDENTE_HOMOLOGACAO
```
