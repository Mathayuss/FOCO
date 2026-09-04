-- FOCO — Estrutura inicial em português
-- Banco recomendado: foco_ocorrencias

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS ingestao;
CREATE SCHEMA IF NOT EXISTS referencia;
CREATE SCHEMA IF NOT EXISTS operacional;
CREATE SCHEMA IF NOT EXISTS historico;
CREATE SCHEMA IF NOT EXISTS analitico;
CREATE SCHEMA IF NOT EXISTS auditoria;

CREATE TABLE IF NOT EXISTS ingestao.sistema_origem (
    id_sistema_origem BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(80) NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    tipo_origem VARCHAR(40) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    descricao TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingestao.lote_importacao (
    id_lote_importacao BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_sistema_origem BIGINT NOT NULL
        REFERENCES ingestao.sistema_origem(id_sistema_origem),
    referencia_origem TEXT,
    nome_arquivo TEXT,
    hash_sha256 VARCHAR(64),
    situacao VARCHAR(30) NOT NULL,
    versao_transformacao VARCHAR(50),
    iniciado_em TIMESTAMPTZ,
    finalizado_em TIMESTAMPTZ,
    total_linhas BIGINT,
    linhas_validas BIGINT,
    linhas_invalidas BIGINT,
    linhas_duplicadas BIGINT,
    metadados JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS referencia.municipio (
    id_municipio BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_ibge VARCHAR(7) UNIQUE,
    nome VARCHAR(150) NOT NULL UNIQUE,
    centroide GEOGRAPHY(POINT,4326),
    limite GEOMETRY(MULTIPOLYGON,4326),
    populacao INTEGER,
    ano_referencia_populacao SMALLINT,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referencia.comando (
    id_comando BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE,
    nome VARCHAR(150) NOT NULL UNIQUE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referencia.unidade_operacional (
    id_unidade_operacional BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(80),
    nome VARCHAR(200) NOT NULL UNIQUE,
    id_comando BIGINT REFERENCES referencia.comando(id_comando),
    id_unidade_superior BIGINT
        REFERENCES referencia.unidade_operacional(id_unidade_operacional),
    id_municipio BIGINT REFERENCES referencia.municipio(id_municipio),
    localizacao GEOGRAPHY(POINT,4326),
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referencia.grupo_ocorrencia (
    id_grupo_ocorrencia BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE,
    nome VARCHAR(200) NOT NULL UNIQUE,
    ordem_exibicao INTEGER,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referencia.tipo_viatura (
    id_tipo_viatura BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL,
    categoria VARCHAR(100),
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referencia.viatura (
    id_viatura BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prefixo VARCHAR(80) NOT NULL UNIQUE,
    id_tipo_viatura BIGINT REFERENCES referencia.tipo_viatura(id_tipo_viatura),
    id_unidade_operacional BIGINT
        REFERENCES referencia.unidade_operacional(id_unidade_operacional),
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS referencia.documento_normativo (
    id_documento_normativo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(120) NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    tipo_documento VARCHAR(40),
    data_emissao DATE,
    vigencia_inicio DATE,
    vigencia_fim DATE,
    referencia_arquivo TEXT
);

CREATE TABLE IF NOT EXISTS referencia.area_operacional (
    id_area_operacional BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(120) NOT NULL,
    nome VARCHAR(200) NOT NULL,
    tipo_escopo VARCHAR(30) NOT NULL,
    id_municipio BIGINT REFERENCES referencia.municipio(id_municipio),
    limite GEOMETRY(MULTIPOLYGON,4326),
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE,
    id_documento_normativo BIGINT
        REFERENCES referencia.documento_normativo(id_documento_normativo),
    situacao VARCHAR(20) NOT NULL DEFAULT 'ATIVA',
    CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio),
    UNIQUE (codigo, vigencia_inicio)
);

CREATE TABLE IF NOT EXISTS referencia.area_operacional_unidade (
    id_area_operacional BIGINT NOT NULL
        REFERENCES referencia.area_operacional(id_area_operacional) ON DELETE CASCADE,
    id_unidade_operacional BIGINT NOT NULL
        REFERENCES referencia.unidade_operacional(id_unidade_operacional),
    tipo_responsabilidade VARCHAR(20) NOT NULL DEFAULT 'PRIMARIA',
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE,
    PRIMARY KEY (
        id_area_operacional,
        id_unidade_operacional,
        vigencia_inicio
    )
);

CREATE TABLE IF NOT EXISTS operacional.ocorrencia (
    id_ocorrencia BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_canonico UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    id_sistema_origem BIGINT NOT NULL
        REFERENCES ingestao.sistema_origem(id_sistema_origem),
    id_lote_importacao BIGINT
        REFERENCES ingestao.lote_importacao(id_lote_importacao),
    id_registro_origem VARCHAR(200),
    numero_ocorrencia VARCHAR(150),
    data_hora_abertura TIMESTAMPTZ,
    data_hora_despacho TIMESTAMPTZ,
    data_hora_encerramento TIMESTAMPTZ,
    id_grupo_ocorrencia BIGINT
        REFERENCES referencia.grupo_ocorrencia(id_grupo_ocorrencia),
    id_municipio BIGINT REFERENCES referencia.municipio(id_municipio),
    id_unidade_operacional BIGINT
        REFERENCES referencia.unidade_operacional(id_unidade_operacional),
    localizacao GEOGRAPHY(POINT,4326),
    tipo_origem_dado VARCHAR(30) NOT NULL DEFAULT 'REAL',
    situacao_dado VARCHAR(20) NOT NULL DEFAULT 'VALIDO',
    dados_brutos JSONB,
    recebido_em TIMESTAMPTZ,
    atualizado_na_origem_em TIMESTAMPTZ,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS operacional.ocorrencia_viatura (
    id_ocorrencia_viatura BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_ocorrencia BIGINT NOT NULL
        REFERENCES operacional.ocorrencia(id_ocorrencia) ON DELETE CASCADE,
    id_viatura BIGINT NOT NULL
        REFERENCES referencia.viatura(id_viatura),
    id_unidade_operacional BIGINT
        REFERENCES referencia.unidade_operacional(id_unidade_operacional),
    data_hora_despacho TIMESTAMPTZ,
    data_hora_saida TIMESTAMPTZ,
    data_hora_chegada TIMESTAMPTZ,
    data_hora_liberacao TIMESTAMPTZ,
    data_hora_retorno TIMESTAMPTZ,
    data_hora_disponibilidade TIMESTAMPTZ,
    situacao VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS auditoria.evento (
    id_evento BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ocorrido_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    referencia_ator VARCHAR(200),
    acao VARCHAR(100) NOT NULL,
    tipo_entidade VARCHAR(120),
    id_entidade VARCHAR(120),
    id_requisicao VARCHAR(120),
    detalhes JSONB NOT NULL DEFAULT '{}'::jsonb
);
