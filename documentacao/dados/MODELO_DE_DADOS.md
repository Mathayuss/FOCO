# FOCO — Modelo de Dados

## Entidade central

```text
Ocorrencia
- id_ocorrencia
- id_canonico
- id_sistema_origem
- id_registro_origem
- numero_ocorrencia
- data_hora_abertura
- data_hora_despacho
- data_hora_encerramento
- id_grupo_ocorrencia
- id_municipio
- id_regiao_urbana
- id_tipo_local
- id_unidade_operacional
- localizacao
- tipo_origem_dado
- situacao_dado
```

## Relação ocorrência × viatura

```text
OcorrenciaViatura
- id_ocorrencia_viatura
- id_ocorrencia
- id_viatura
- id_unidade_operacional
- data_hora_despacho
- data_hora_saida
- data_hora_chegada
- data_hora_liberacao
- data_hora_retorno
- data_hora_disponibilidade
```

## Tipos de origem

- REAL
- HISTORICO_AGREGADO
- DEMONSTRATIVO

## Áreas operacionais

```text
DocumentoNormativo
AreaOperacional
AreaOperacionalUnidade
AreaOperacionalMunicipio
AreaOperacionalRegiaoUrbana
```

As áreas devem ser versionadas por vigência.

## Rastreabilidade de importação

```text
LoteImportacao
- id_lote_importacao
- nome_arquivo
- hash_arquivo
- formato_arquivo
- perfil_origem
- sistema_origem
- total_linhas
- linhas_validas
- linhas_invalidas
- linhas_inseridas
- linhas_duplicadas
- linhas_sensiveis
- linhas_coordenada_invalida
- linhas_sem_coordenada
- situacao
- avisos
- erro
- iniciado_em
- concluido_em

LinhaImportacaoRejeitada
- id_linha_importacao_rejeitada
- id_lote_importacao
- numero_linha
- motivos
- dados_origem
```

Cada ocorrência importada pode apontar para `id_lote_importacao`. Linhas rejeitadas
devem preservar o payload original e os motivos de rejeição para auditoria.
