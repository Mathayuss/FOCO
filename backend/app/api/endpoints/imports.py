from pathlib import PurePath

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.imports import CsvPreviewResponse, ImportCommitResponse
from app.services.import_service import commit_import, preview_import

router = APIRouter(prefix="/imports", tags=["importações"])

MAX_IMPORT_MEGABYTES = 512
MAX_IMPORT_BYTES = MAX_IMPORT_MEGABYTES * 1024 * 1024
MAX_CSV_MEGABYTES = MAX_IMPORT_MEGABYTES
MAX_CSV_BYTES = MAX_IMPORT_BYTES
ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
ALLOWED_IMPORT_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/excel",
    "application/x-excel",
    "application/x-msexcel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream",
}


def _validate_upload_metadata(file: UploadFile) -> str:
    filename = file.filename or ""
    if PurePath(filename).name != filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
    suffix = PurePath(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Envie um arquivo CSV, XLS ou XLSX")
    content_type = (file.content_type or "").split(";", 1)[0].lower()
    if content_type and content_type not in ALLOWED_IMPORT_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Tipo MIME inválido para importação")
    return filename


async def _read_upload(file: UploadFile) -> tuple[str, bytes]:
    filename = _validate_upload_metadata(file)
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail=f"Arquivo excede o limite de {MAX_IMPORT_MEGABYTES} MB")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Arquivo vazio")
    return filename, content


@router.post("/preview", response_model=CsvPreviewResponse)
async def import_preview(file: UploadFile = File(...)):
    filename, content = await _read_upload(file)
    try:
        return preview_import(content, filename)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV deve estar em UTF-8")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/csv/preview", response_model=CsvPreviewResponse)
async def csv_preview(file: UploadFile = File(...)):
    return await import_preview(file)


@router.post("", response_model=ImportCommitResponse)
async def create_import(file: UploadFile = File(...), db: Session = Depends(get_db)):
    filename, content = await _read_upload(file)
    try:
        return commit_import(db, content, filename)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV deve estar em UTF-8")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
