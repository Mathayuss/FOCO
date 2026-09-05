from pathlib import PurePath

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.imports import CsvPreviewResponse
from app.services.import_service import preview_csv

router = APIRouter(prefix="/imports", tags=["imports"])

MAX_CSV_MEGABYTES = 512
MAX_CSV_BYTES = MAX_CSV_MEGABYTES * 1024 * 1024
ALLOWED_CSV_MIME_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel"}

def _validate_upload_metadata(file: UploadFile) -> None:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo CSV")
    if PurePath(filename).name != filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    if content_type not in ALLOWED_CSV_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Tipo MIME inválido para CSV")

@router.post("/csv/preview", response_model=CsvPreviewResponse)
async def csv_preview(file: UploadFile = File(...)):
    _validate_upload_metadata(file)
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(status_code=413, detail=f"CSV excede o limite de {MAX_CSV_MEGABYTES} MB")
    if not content.strip():
        raise HTTPException(status_code=400, detail="CSV vazio")
    try:
        return preview_csv(content)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV deve estar em UTF-8")
