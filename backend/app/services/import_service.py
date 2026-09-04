import csv, io
from datetime import datetime

CANONICAL_COLUMNS = {
    "source_id", "opened_at", "municipality", "type_name",
    "subtype_name", "latitude", "longitude", "vehicle_code", "vehicle_type",
    "dispatched_at", "departure_at", "arrival_at", "released_at", "returned_at", "available_at"
}
REQUIRED = {"source_id", "opened_at", "municipality", "type_name"}

def preview_csv(content: bytes) -> dict:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = set(reader.fieldnames or [])
    missing = sorted(REQUIRED - headers)
    rows = list(reader)
    issues = []
    seen = set()
    valid = 0
    for idx, row in enumerate(rows, start=2):
        row_issues = []
        sid = (row.get("source_id") or "").strip()
        if not sid: row_issues.append("source_id ausente")
        elif sid in seen: row_issues.append("source_id duplicado no arquivo")
        seen.add(sid)
        for field in ["opened_at"]:
            value = (row.get(field) or "").strip()
            try: datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception: row_issues.append(f"{field} inválido")
        if not (row.get("municipality") or "").strip(): row_issues.append("municipality ausente")
        if not (row.get("type_name") or "").strip(): row_issues.append("type_name ausente")
        if row_issues:
            issues.append({"row": idx, "issues": row_issues})
        else:
            valid += 1
    return {
        "headers": list(reader.fieldnames or []),
        "recognized_headers": sorted(headers & CANONICAL_COLUMNS),
        "missing_required_headers": missing,
        "total_rows": len(rows),
        "valid_rows": valid if not missing else 0,
        "invalid_rows": (len(rows)-valid) if not missing else len(rows),
        "issues": issues[:50],
        "can_commit": not missing and not issues,
    }
