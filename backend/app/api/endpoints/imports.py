from pathlib import PurePath

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.imports import (
    CsvPreviewResponse,
    ImportBatchListResponse,
    ImportBatchResponse,
    ImportCommitResponse,
    RejectedImportLineListResponse,
)
from app.services import import_audit_service
from app.services.import_service import commit_import, preview_import


router = APIRouter(prefix="/imports", tags=["importações"])
settings = get_settings()

MAX_IMPORT_MEGABYTES = settings.limite_importacao_mb
MAX_IMPORT_BYTES = MAX_IMPORT_MEGABYTES * 1024 * 1024

# Compatibilidade temporária com referências existentes.
MAX_CSV_MEGABYTES = MAX_IMPORT_MEGABYTES
MAX_CSV_BYTES = MAX_IMPORT_BYTES

ALLOWED_EXTENSIONS = {".csv", ".xls", ".xlsx"}
ALLOWED_IMPORT_MIME_TYPES = {
    "text/csv",
    "text/html",
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
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {MAX_IMPORT_MEGABYTES} MB",
        )

    if not content.strip():
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    return filename, content


@router.get("/lotes", response_model=ImportBatchListResponse)
def list_import_batches(
    limite: int = Query(default=20, ge=1, le=100),
    deslocamento: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return import_audit_service.list_batches(db, limite=limite, deslocamento=deslocamento)


@router.get("/lotes/{id_lote_importacao}", response_model=ImportBatchResponse)
def get_import_batch(id_lote_importacao: int, db: Session = Depends(get_db)):
    batch = import_audit_service.get_batch(db, id_lote_importacao)
    if batch is None:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
    return batch


@router.get("/lotes/{id_lote_importacao}/rejeicoes", response_model=RejectedImportLineListResponse)
def list_import_batch_rejections(
    id_lote_importacao: int,
    limite: int = Query(default=50, ge=1, le=200),
    deslocamento: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    result = import_audit_service.list_rejected_lines(
        db,
        id_lote_importacao,
        limite=limite,
        deslocamento=deslocamento,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Lote de importação não encontrado")
    return result


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
