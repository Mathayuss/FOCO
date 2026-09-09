import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.import_batch import ImportBatch, RejectedImportLine


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return [value]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def _json_dict(value: str | None) -> dict[str, str] | None:
    if not value:
        return None
    try:
        parsed: Any = json.loads(value)
    except json.JSONDecodeError:
        return {"conteudo": value}
    if isinstance(parsed, dict):
        return {str(key): str(item) for key, item in parsed.items()}
    return {"conteudo": str(parsed)}


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _batch_item(batch: ImportBatch) -> dict:
    return {
        "id_lote_importacao": batch.id,
        "nome_arquivo": batch.filename,
        "hash_arquivo": batch.file_hash,
        "formato_arquivo": batch.file_format,
        "perfil_origem": batch.source_profile,
        "sistema_origem": batch.source_system,
        "total_linhas": batch.total_rows,
        "linhas_validas": batch.valid_rows,
        "linhas_invalidas": batch.invalid_rows,
        "linhas_inseridas": batch.inserted_rows,
        "linhas_duplicadas": batch.duplicate_rows,
        "linhas_sensiveis": batch.sensitive_rows,
        "linhas_coordenada_invalida": batch.invalid_coordinate_rows,
        "linhas_sem_coordenada": batch.missing_coordinate_rows,
        "situacao": batch.status,
        "avisos": _json_list(batch.warnings),
        "erro": batch.error,
        "iniciado_em": _iso(batch.started_at),
        "concluido_em": _iso(batch.finished_at),
    }


def list_batches(db: Session, limite: int = 20, deslocamento: int = 0) -> dict:
    total = db.scalar(select(func.count(ImportBatch.id))) or 0
    rows = db.scalars(
        select(ImportBatch)
        .order_by(ImportBatch.started_at.desc(), ImportBatch.id.desc())
        .limit(limite)
        .offset(deslocamento)
    ).all()
    return {"items": [_batch_item(row) for row in rows], "total": total, "limite": limite, "deslocamento": deslocamento}


def get_batch(db: Session, batch_id: int) -> dict | None:
    batch = db.get(ImportBatch, batch_id)
    return _batch_item(batch) if batch else None


def _rejected_item(row: RejectedImportLine) -> dict:
    return {
        "id_linha_importacao_rejeitada": row.id,
        "id_lote_importacao": row.import_batch_id,
        "numero_linha": row.row_number,
        "motivos": _json_list(row.reasons),
        "dados_origem": _json_dict(row.source_payload),
    }


def list_rejected_lines(db: Session, batch_id: int, limite: int = 50, deslocamento: int = 0) -> dict | None:
    if db.get(ImportBatch, batch_id) is None:
        return None
    total = db.scalar(
        select(func.count(RejectedImportLine.id)).where(RejectedImportLine.import_batch_id == batch_id)
    ) or 0
    rows = db.scalars(
        select(RejectedImportLine)
        .where(RejectedImportLine.import_batch_id == batch_id)
        .order_by(RejectedImportLine.row_number.asc(), RejectedImportLine.id.asc())
        .limit(limite)
        .offset(deslocamento)
    ).all()
    return {"items": [_rejected_item(row) for row in rows], "total": total, "limite": limite, "deslocamento": deslocamento}
