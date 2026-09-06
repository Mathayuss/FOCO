# FOCO - Leiaute de Importação SEJUSP

## Escopo

Este é o leiaute-alvo aceito para importação de relatórios SEJUSP no FOCO.

O arquivo pode chegar como CSV, XLS ou XLSX. Para arquivos textuais, o importador aceita separação por ponto e vírgula, tabulação, vírgula ou barra vertical (`|`). O cabeçalho pode conter espaços extras e marcações HTML simples, como `<br>`.

## Cabeçalho Oficial

```text
Nº/ANO | FORÇA | MOVIMENTAÇÃO | SEGREDO DE JUSTIÇA | FATO | FATO AGRUPADO | CATEGORIA | AUTORIA CONHECIDA / DESCONHECIDA | MOTIVAÇÃO | UNIDADE DE ORIGEM | UF DE ORIGEM | MUNICÍPIO DE ORIGEM | DATA DO REGISTRO | HORA DO REGISTRO | DIA DO REGISTRO | PERÍODO DO REGISTRO | DATA DO FATO | HORA DO FATO | FAIXA IDADE | LOCAL | UF | MUNICÍPIO | CÓDIGO IBGE | BAIRRO | REFERÊNCIA | ÁREA DO MUNICÍPIO | LOGRADOURO | LATITUDE | LONGITUDE
```

## Campos Obrigatórios

| Coluna do relatório | Campo FOCO | Regra |
|---|---|---|
| `Nº/ANO` | `id_origem` | Identificador único da ocorrência na origem. |
| `DATA DO FATO` + `HORA DO FATO` | `abertura_em` | Data/hora operacional principal da ocorrência. |
| `FATO` | `tipo` | Tipificação principal. |
| `MUNICÍPIO` | `municipio` | Município do fato. |

## Equivalência de Colunas

| Coluna do relatório | Campo FOCO | Persistência |
|---|---|---|
| `Nº/ANO` | `id_origem` | Coluna normalizada em `ocorrencia`. |
| `FORÇA` | `forca` | Campo auxiliar preservado em `dados_origem`. |
| `MOVIMENTAÇÃO` | `movimentacao` | Campo auxiliar preservado em `dados_origem`. |
| `SEGREDO DE JUSTIÇA` | `segredo_de_justica` | Coluna normalizada em `ocorrencia`. |
| `FATO` | `tipo` | Coluna normalizada em `ocorrencia`. |
| `FATO AGRUPADO` | `grupo` | Coluna normalizada em `ocorrencia`. |
| `CATEGORIA` | `subtipo` | Coluna normalizada em `ocorrencia`. |
| `AUTORIA CONHECIDA / DESCONHECIDA` | `autoria` | Campo auxiliar preservado em `dados_origem`. |
| `MOTIVAÇÃO` | `motivacao` | Campo auxiliar preservado em `dados_origem`. |
| `UNIDADE DE ORIGEM` | `unidade_operacional` | Cria/associa registro em `unidade_operacional`. |
| `UF DE ORIGEM` | `uf_origem` | Campo auxiliar preservado em `dados_origem`. |
| `MUNICÍPIO DE ORIGEM` | `municipio_origem` | Campo auxiliar preservado em `dados_origem`. |
| `DATA DO REGISTRO` + `HORA DO REGISTRO` | `registro_em` | Coluna normalizada em `ocorrencia`. |
| `DIA DO REGISTRO` | `dia_registro` | Campo auxiliar preservado em `dados_origem`. |
| `PERÍODO DO REGISTRO` | `periodo_registro` | Campo auxiliar preservado em `dados_origem`. |
| `DATA DO FATO` + `HORA DO FATO` | `abertura_em` | Coluna normalizada em `ocorrencia`. |
| `FAIXA IDADE` | `faixa_idade` | Campo auxiliar preservado em `dados_origem`. |
| `LOCAL` | `local` | Campo auxiliar preservado em `dados_origem`. |
| `UF` | `uf` | Campo auxiliar preservado em `dados_origem`. |
| `MUNICÍPIO` | `municipio` | Coluna normalizada em `ocorrencia`. |
| `CÓDIGO IBGE` | `codigo_ibge` | Coluna normalizada em `ocorrencia`. |
| `BAIRRO` | `bairro` | Coluna normalizada em `ocorrencia`. |
| `REFERÊNCIA` | `referencia` | Usado para compor `endereco` e preservado em `dados_origem`. |
| `ÁREA DO MUNICÍPIO` | `area_municipio` | Campo auxiliar preservado em `dados_origem`. |
| `LOGRADOURO` | `logradouro` | Usado para compor `endereco` e preservado em `dados_origem`. |
| `LATITUDE` | `latitude` | Coluna normalizada em `ocorrencia`. |
| `LONGITUDE` | `longitude` | Coluna normalizada em `ocorrencia`. |

## Regras de Importação

- `sistema_origem` recebe `RELATORIO_SEJUSP`.
- `situacao` recebe `importada`.
- Duplicidade é verificada por `sistema_origem` + `id_origem`.
- A linha original completa é preservada em `dados_origem`.
- Registros sem campos obrigatórios são rejeitados e retornados em `issues`.
- Coordenadas ausentes não bloqueiam importação; coordenadas inválidas reduzem `pontuacao_qualidade`.
- Linhas com `SEGREDO DE JUSTIÇA=Sim` recebem `segredo_de_justica=true` e prioridade `sigilo_judicial`.
