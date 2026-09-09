from pydantic import BaseModel, Field

class CsvIssue(BaseModel):
    row: int
    issues: list[str]

class ColumnMapping(BaseModel):
    source_header: str
    target_field: str | None = None
    required: bool = False
    status: str

class CsvPreviewResponse(BaseModel):
    headers: list[str]
    recognized_headers: list[str]
    missing_required_headers: list[str]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    issues: list[CsvIssue]
    can_commit: bool
    source_format: str = "csv"
    source_profile: str = "FOCO"
    registration_years: list[int] = Field(default_factory=list)
    column_mappings: list[ColumnMapping] = Field(default_factory=list)
    unmapped_headers: list[str] = Field(default_factory=list)
    sensitive_rows: int = 0
    invalid_coordinate_rows: int = 0
    missing_coordinate_rows: int = 0
    warnings: list[str] = Field(default_factory=list)

class ImportCommitResponse(BaseModel):
    id_lote_importacao: int
    source_format: str
    source_profile: str
    source_scope: str
    registration_years: list[int] = Field(default_factory=list)
    total_rows: int
    inserted_rows: int
    skipped_duplicate_rows: int
    invalid_rows: int
    sensitive_rows: int
    invalid_coordinate_rows: int
    missing_coordinate_rows: int
    issues: list[CsvIssue]
    warnings: list[str]
    can_commit: bool


class ImportBatchResponse(BaseModel):
    id_lote_importacao: int
    nome_arquivo: str
    hash_arquivo: str
    formato_arquivo: str
    perfil_origem: str
    sistema_origem: str
    total_linhas: int
    linhas_validas: int
    linhas_invalidas: int
    linhas_inseridas: int
    linhas_duplicadas: int
    linhas_sensiveis: int
    linhas_coordenada_invalida: int
    linhas_sem_coordenada: int
    situacao: str
    avisos: list[str] = Field(default_factory=list)
    erro: str | None = None
    iniciado_em: str
    concluido_em: str | None = None


class ImportBatchListResponse(BaseModel):
    items: list[ImportBatchResponse]
    total: int
    limite: int
    deslocamento: int


class RejectedImportLineResponse(BaseModel):
    id_linha_importacao_rejeitada: int
    id_lote_importacao: int
    numero_linha: int
    motivos: list[str]
    dados_origem: dict[str, str] | None = None


class RejectedImportLineListResponse(BaseModel):
    items: list[RejectedImportLineResponse]
    total: int
    limite: int
    deslocamento: int
