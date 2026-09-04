from pydantic import BaseModel

class CsvIssue(BaseModel):
    row: int
    issues: list[str]

class CsvPreviewResponse(BaseModel):
    headers: list[str]
    recognized_headers: list[str]
    missing_required_headers: list[str]
    total_rows: int
    valid_rows: int
    invalid_rows: int
    issues: list[CsvIssue]
    can_commit: bool
