from contextlib import contextmanager
import hashlib
from pathlib import PurePath
from threading import BoundedSemaphore
from typing import BinaryIO

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
from app.services.import_service import (
    CSV_ENCODING_ERROR,
    ImportInProgressError,
    commit_import_stream,
    preview_import_stream_with_database,
)


router = APIRouter(prefix="/imports", tags=["importações"])
settings = get_settings()

UPLOAD_READ_CHUNK_BYTES = 1024 * 1024
MAX_IMPORT_MEGABYTES = settings.limite_importacao_mb
MAX_IMPORT_BYTES = MAX_IMPORT_MEGABYTES * 1024 * 1024
_IMPORT_PROCESSING_SEMAPHORE = BoundedSemaphore(value=1)

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


@contextmanager
def _import_processing_slot():
    if not _IMPORT_PROCESSING_SEMAPHORE.acquire(blocking=False):
        raise HTTPException(
            status_code=503,
            detail="Outra importação está em processamento; tente novamente em instantes",
            headers={"Retry-After": "2"},
        )
    try:
        yield
    finally:
        _IMPORT_PROCESSING_SEMAPHORE.release()


def _validate_upload_metadata(file: UploadFile) -> str:
    filename = file.filename or ""
    if not filename or len(filename) > 255 or any(ord(character) < 32 for character in filename):
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
    if PurePath(filename).name != filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

    suffix = PurePath(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Envie um arquivo CSV, XLS ou XLSX")

    content_type = (file.content_type or "").split(";", 1)[0].lower()
    if content_type and content_type not in ALLOWED_IMPORT_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Tipo MIME inválido para importação")

    return filename


def _prepare_upload(file: UploadFile) -> tuple[str, BinaryIO, str]:
    filename = _validate_upload_metadata(file)
    if file.size is not None and file.size > MAX_IMPORT_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {MAX_IMPORT_MEGABYTES} MB",
        )

    digest = hashlib.sha256()
    total_bytes = 0
    has_content = False
    file.file.seek(0)
    while True:
        chunk = file.file.read(UPLOAD_READ_CHUNK_BYTES)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > MAX_IMPORT_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo excede o limite de {MAX_IMPORT_MEGABYTES} MB",
            )
        digest.update(chunk)
        has_content = has_content or bool(chunk.strip())

    if not has_content:
        raise HTTPException(status_code=400, detail="Arquivo vazio")

    file.file.seek(0)
    return filename, file.file, digest.hexdigest()


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


def _preview_with_history(file: UploadFile, db: Session) -> dict:
    filename, source, file_hash = _prepare_upload(file)
    result = preview_import_stream_with_database(db, source, filename)
    previous = import_audit_service.find_latest_batch_by_hash(db, file_hash)
    result["already_imported"] = previous is not None
    result["previous_import_batch_id"] = previous["id_lote_importacao"] if previous else None
    result["previous_import_status"] = previous["situacao"] if previous else None
    result["previous_import_at"] = previous["iniciado_em"] if previous else None
    if previous:
        result["warnings"] = [
            *result.get("warnings", []),
            (
                f"Este arquivo já foi processado no lote "
                f"#{previous['id_lote_importacao']} ({previous['situacao']})"
            ),
        ]
    return result


def _preview_response(file: UploadFile, db: Session) -> dict:
    try:
        with _import_processing_slot():
            return _preview_with_history(file, db)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail=CSV_ENCODING_ERROR)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/preview", response_model=CsvPreviewResponse)
def import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return _preview_response(file, db)


@router.post("/csv/preview", response_model=CsvPreviewResponse)
def csv_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return _preview_response(file, db)


@router.post("", response_model=ImportCommitResponse)
def create_import(file: UploadFile = File(...), db: Session = Depends(get_db)):
    with _import_processing_slot():
        filename, source, file_hash = _prepare_upload(file)
        try:
            return commit_import_stream(db, source, filename, file_hash)
        except ImportInProgressError as exc:
            raise HTTPException(
                status_code=503,
                detail=str(exc),
                headers={"Retry-After": "2"},
            )
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail=CSV_ENCODING_ERROR)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500, detail="Não foi possível concluir a importação; nenhuma linha foi gravada"
            ) from exc
