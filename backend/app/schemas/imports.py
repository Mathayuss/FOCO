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
    column_mappings: list[ColumnMapping] = Field(default_factory=list)
    unmapped_headers: list[str] = Field(default_factory=list)
    sensitive_rows: int = 0
    invalid_coordinate_rows: int = 0
    missing_coordinate_rows: int = 0
    warnings: list[str] = Field(default_factory=list)

class ImportCommitResponse(BaseModel):
    source_format: str
    source_profile: str
    source_scope: str
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
