import csv
import io
from datetime import datetime

CANONICAL_COLUMNS = {
    "id_origem",
    "abertura_em",
    "municipio",
    "tipo",
    "subtipo",
    "latitude",
    "longitude",
    "codigo_viatura",
    "tipo_viatura",
    "despacho_em",
    "saida_em",
    "chegada_em",
    "liberacao_em",
    "retorno_em",
    "disponibilidade_em",
}
COLUMN_ALIASES = {
    "source_id": "id_origem",
    "opened_at": "abertura_em",
    "municipality": "municipio",
    "type_name": "tipo",
    "subtype_name": "subtipo",
    "vehicle_code": "codigo_viatura",
    "vehicle_type": "tipo_viatura",
    "dispatched_at": "despacho_em",
    "departure_at": "saida_em",
    "arrival_at": "chegada_em",
    "released_at": "liberacao_em",
    "returned_at": "retorno_em",
    "available_at": "disponibilidade_em",
}
REQUIRED = {"id_origem", "abertura_em", "municipio", "tipo"}


def _canonical_header(header: str | None) -> str:
    normalized = (header or "").strip()
    return COLUMN_ALIASES.get(normalized, normalized)


def _canonical_row(row: dict[str | None, str]) -> dict[str, str]:
    canonical = {}
    for header, value in row.items():
        if header is None:
            continue
        canonical[_canonical_header(header)] = value
    return canonical


def preview_csv(content: bytes) -> dict:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []
    headers = {_canonical_header(header) for header in fieldnames}
    missing = sorted(REQUIRED - headers)
    rows = [_canonical_row(row) for row in reader]
    issues = []
    seen = set()
    valid = 0
    for idx, row in enumerate(rows, start=2):
        row_issues = []
        sid = (row.get("id_origem") or "").strip()
        if not sid:
            row_issues.append("id_origem ausente")
        elif sid in seen:
            row_issues.append("id_origem duplicado no arquivo")
        seen.add(sid)
        value = (row.get("abertura_em") or "").strip()
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            row_issues.append("abertura_em inválido")
        if not (row.get("municipio") or "").strip():
            row_issues.append("municipio ausente")
        if not (row.get("tipo") or "").strip():
            row_issues.append("tipo ausente")
        if row_issues:
            issues.append({"row": idx, "issues": row_issues})
        else:
            valid += 1
    return {
        "headers": fieldnames,
        "recognized_headers": sorted(headers & CANONICAL_COLUMNS),
        "missing_required_headers": missing,
        "total_rows": len(rows),
        "valid_rows": valid if not missing else 0,
        "invalid_rows": (len(rows) - valid) if not missing else len(rows),
        "issues": issues[:50],
        "can_commit": not missing and not issues,
    }
