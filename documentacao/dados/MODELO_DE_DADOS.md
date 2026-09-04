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
