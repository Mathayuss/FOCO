import csv
import io
import json
from html import unescape
from html.parser import HTMLParser
import re
import unicodedata
import zipfile
from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from xml.etree import ElementTree as ET

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.occurrence import Occurrence
from app.models.unit import Unit

LOCAL_TZ = ZoneInfo("America/Campo_Grande")
EXCEL_EPOCH = datetime(1899, 12, 30, tzinfo=LOCAL_TZ)
SISTEMA_ORIGEM_SEJUSP = "RELATORIO_SEJUSP"
SISTEMA_ORIGEM_FOCO = "FOCO_IMPORTACAO"

CANONICAL_COLUMNS = {
    "id_origem",
    "abertura_em",
    "registro_em",
    "municipio",
    "tipo",
    "grupo",
    "subtipo",
    "unidade_operacional",
    "bairro",
    "endereco",
    "latitude",
    "longitude",
    "codigo_ibge",
    "segredo_de_justica",
    "codigo_viatura",
    "tipo_viatura",
    "despacho_em",
    "saida_em",
    "chegada_em",
    "liberacao_em",
    "retorno_em",
    "disponibilidade_em",
}
AUXILIARY_COLUMNS = {
    "area_municipio",
    "autoria",
    "dia_registro",
    "faixa_idade",
    "forca",
    "local",
    "motivacao",
    "movimentacao",
    "municipio_origem",
    "periodo_registro",
    "uf",
    "uf_origem",
}
REQUIRED = {"id_origem", "abertura_em", "municipio", "tipo"}

HEADER_ALIASES_RAW = {
    "source_id": "id_origem",
    "opened_at": "abertura_em",
    "municipality": "municipio",
    "type_name": "tipo",
    "group_name": "grupo",
    "subtype_name": "subtipo",
    "vehicle_code": "codigo_viatura",
    "vehicle_type": "tipo_viatura",
    "dispatched_at": "despacho_em",
    "departure_at": "saida_em",
    "arrival_at": "chegada_em",
    "released_at": "liberacao_em",
    "returned_at": "retorno_em",
    "available_at": "disponibilidade_em",
    "Nº/ANO": "id_origem",
    "N/ANO": "id_origem",
    "FATO": "tipo",
    "FATO AGRUPADO": "grupo",
    "CATEGORIA": "subtipo",
    "AUTORIA CONHECIDA / DESCONHECIDA": "autoria",
    "MOTIVAÇÃO": "motivacao",
    "MOTIVACAO": "motivacao",
    "UNIDADE DE ORIGEM": "unidade_operacional",
    "DATA DO FATO": "data_fato",
    "HORA DO FATO": "hora_fato",
    "DATA DO REGISTRO": "data_registro",
    "HORA DO REGISTRO": "hora_registro",
    "DIA DO REGISTRO": "dia_registro",
    "MUNICÍPIO": "municipio",
    "MUNICIPIO": "municipio",
    "MUNICÍPIO DE ORIGEM": "municipio_origem",
    "BAIRRO": "bairro",
    "LOGRADOURO": "logradouro",
    "REFERÊNCIA": "referencia",
    "REFERENCIA": "referencia",
    "LATITUDE": "latitude",
    "LONGITUDE": "longitude",
    "CÓDIGO IBGE": "codigo_ibge",
    "CODIGO IBGE": "codigo_ibge",
    "SEGREDO DE JUSTIÇA": "segredo_de_justica",
    "SEGREDO DE JUSTICA": "segredo_de_justica",
    "PERÍODO DO REGISTRO": "periodo_registro",
    "PERIODO DO REGISTRO": "periodo_registro",
    "FAIXA IDADE": "faixa_idade",
    "LOCAL": "local",
    "ÁREA DO MUNICÍPIO": "area_municipio",
    "AREA DO MUNICIPIO": "area_municipio",
    "FORÇA": "forca",
    "FORCA": "forca",
    "MOVIMENTAÇÃO": "movimentacao",
    "MOVIMENTACAO": "movimentacao",
    "UF": "uf",
    "UF DE ORIGEM": "uf_origem",
}
DERIVED_TARGETS = {
    "data_fato": "abertura_em",
    "hora_fato": "abertura_em",
    "data_registro": "registro_em",
    "hora_registro": "registro_em",
    "logradouro": "endereco",
    "referencia": "endereco",
}
SEJUSP_KEYS = {
    "Nº/ANO",
    "FATO",
    "DATA DO FATO",
    "HORA DO FATO",
    "UNIDADE DE ORIGEM",
    "MUNICÍPIO",
}
NULL_VALUES = {"", "-", "--", "N/A", "NA", "NULL", "NULO", "NÃO INFORMADO", "NAO INFORMADO"}
XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
HEADER_ALIASES = {}


def _header_key(header: str | None) -> str:
    text = unescape(str(header or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\ufeff", "").replace("\xa0", " ")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper().strip()
    return re.sub(r"\s+", " ", text)


for _header, _target in HEADER_ALIASES_RAW.items():
    HEADER_ALIASES[_header_key(_header)] = _target


def _clean(value: object) -> str:
    return str(value or "").strip()


def _clean_optional(value: object) -> str:
    text = _clean(value)
    return "" if _header_key(text) in NULL_VALUES else text


def _target_for_header(header: str | None) -> str | None:
    normalized = _clean(header)
    if normalized in CANONICAL_COLUMNS:
        return normalized
    return HEADER_ALIASES.get(_header_key(normalized))


def _public_target(target: str | None) -> str | None:
    if not target:
        return None
    public = DERIVED_TARGETS.get(target, target)
    return public if public in CANONICAL_COLUMNS or public in AUXILIARY_COLUMNS else None


def _source_profile(headers: list[str]) -> str:
    header_keys = {_header_key(header) for header in headers}
    if any(_header_key(header) in header_keys for header in SEJUSP_KEYS):
        return "RELATORIO_SEJUSP"
    if any(header in headers for header in ("source_id", "opened_at", "municipality", "type_name")):
        return "LEGADO_INGLES"
    return "FOCO"


def _source_format(filename: str) -> str:
    lowered = filename.lower()
    if lowered.endswith(".xlsx"):
        return "xlsx"
    if lowered.endswith(".xls"):
        return "xls"
    return "csv"


def _col_index(ref: str) -> int:
    match = re.match(r"([A-Z]+)", ref)
    if not match:
        return 0
    index = 0
    for char in match.group(1):
        index = index * 26 + ord(char) - 64
    return index


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("main:si", XLSX_NS):
        strings.append("".join(text.text or "" for text in item.findall(".//main:t", XLSX_NS)).strip())
    return strings


def _cell_text(cell: ET.Element, shared: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//main:t", XLSX_NS)).strip()
    value = cell.find("main:v", XLSX_NS)
    if value is None or value.text is None:
        return ""
    if cell_type == "s":
        try:
            return shared[int(value.text)].strip()
        except Exception:
            return value.text.strip()
    return value.text.strip()


def _first_sheet_path(zf: zipfile.ZipFile) -> str:
    if "xl/workbook.xml" not in zf.namelist():
        return "xl/worksheets/sheet1.xml"
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_by_id = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels.findall("pkgrel:Relationship", XLSX_NS)}
    sheet = workbook.find("main:sheets/main:sheet", XLSX_NS)
    if sheet is None:
        return "xl/worksheets/sheet1.xml"
    relationship_id = sheet.attrib[f"{{{XLSX_NS['rel']}}}id"]
    target = rel_by_id[relationship_id]
    return target if target.startswith("xl/") else "xl/" + target.lstrip("/")


def _read_xlsx(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if not zipfile.is_zipfile(io.BytesIO(content)):
        raise ValueError("Arquivo XLSX inválido")
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        sheet_path = _first_sheet_path(zf)
        shared = _shared_strings(zf)
        rows = []
        for event, row in ET.iterparse(zf.open(sheet_path), events=("end",)):
            if not row.tag.endswith("row"):
                continue
            values: dict[int, str] = defaultdict(str)
            max_col = 0
            for cell in row:
                if not cell.tag.endswith("c"):
                    continue
                index = _col_index(cell.attrib.get("r", ""))
                if not index:
                    continue
                max_col = max(max_col, index)
                values[index] = _cell_text(cell, shared)
            rows.append([values[index] for index in range(1, max_col + 1)])
            row.clear()
    return _rows_to_dicts(rows)


class _HtmlTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._in_table = False

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag == "table" and not self._in_table:
            self._in_table = True
        if not self._in_table:
            return
        if tag == "tr":
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str):
        if self._cell is not None:
            self._cell.append(data)

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if not self._in_table:
            return
        if tag in {"td", "th"} and self._row is not None and self._cell is not None:
            self._row.append(re.sub(r"\s+", " ", "".join(self._cell)).strip())
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if any(cell for cell in self._row):
                self.rows.append(self._row)
            self._row = None
        elif tag == "table":
            self._in_table = False


def _recognized_targets(row: list[str]) -> set[str]:
    return {
        target
        for value in row
        if (target := _public_target(_target_for_header(str(value or ""))))
    }


def _header_row_index(rows: list[list[str]]) -> int:
    best_index = 0
    best_score = -1
    for index, row in enumerate(rows[:50]):
        targets = _recognized_targets(row)
        required_count = len(targets & REQUIRED)
        score = required_count * 100 + len(targets)
        if score > best_score:
            best_index = index
            best_score = score
        if required_count == len(REQUIRED):
            return index
    return best_index if best_score > 0 else 0


def _is_separator_row(row: list[str]) -> bool:
    non_empty = [cell for cell in row if cell]
    return bool(non_empty) and all(re.fullmatch(r":?-{2,}:?", cell.strip()) for cell in non_empty)


def _rows_to_dicts(rows: list[list[str]]) -> tuple[list[str], list[dict[str, str]]]:
    if not rows:
        return [], []
    header_index = _header_row_index(rows)
    headers = [str(value or "").strip() for value in rows[header_index]]
    data_rows = []
    for row in rows[header_index + 1:]:
        padded = [str(value or "").strip() for value in row] + [""] * (len(headers) - len(row))
        if not any(padded) or _is_separator_row(padded):
            continue
        data_rows.append({header: padded[index] if index < len(padded) else "" for index, header in enumerate(headers)})
    return headers, data_rows


def _decode_xls_text(content: bytes) -> str:
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Arquivo XLS textual deve estar em UTF-8 ou Latin-1")


def _read_xls_html(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    parser = _HtmlTableParser()
    parser.feed(_decode_xls_text(content))
    return _rows_to_dicts(parser.rows)


def _detect_delimiter(sample: str) -> str | None:
    lines = [line for line in sample.splitlines() if line.strip()][:8]
    scores = {delimiter: sum(line.count(delimiter) for line in lines) for delimiter in (";", "\t", ",", "|")}
    delimiter, count = max(scores.items(), key=lambda item: item[1])
    return delimiter if count else None


def _read_delimited_text(text: str) -> tuple[list[str], list[dict[str, str]]]:
    sample = text[:4096]
    delimiter = _detect_delimiter(sample)
    if delimiter:
        rows = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]
    else:
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t;,|")
        except csv.Error:
            dialect = csv.excel
        rows = [row for row in csv.reader(io.StringIO(text), dialect=dialect)]
    return _rows_to_dicts(rows)


def _read_xls_delimited(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    return _read_delimited_text(_decode_xls_text(content))


def _read_xls_binary(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    try:
        import xlrd
    except ModuleNotFoundError as exc:
        raise ValueError("Arquivo XLS binário requer a dependência xlrd instalada no backend") from exc
    workbook = xlrd.open_workbook(file_contents=content)
    if not workbook.nsheets:
        return [], []
    sheet = workbook.sheet_by_index(0)
    rows = []
    for row_index in range(sheet.nrows):
        row = []
        for col_index in range(sheet.ncols):
            cell = sheet.cell(row_index, col_index)
            if cell.ctype == xlrd.XL_CELL_DATE:
                parsed = xlrd.xldate_as_datetime(cell.value, workbook.datemode)
                row.append(parsed.strftime("%d/%m/%Y %H:%M:%S" if parsed.time().isoformat() != "00:00:00" else "%d/%m/%Y"))
            elif cell.ctype == xlrd.XL_CELL_NUMBER:
                value = int(cell.value) if float(cell.value).is_integer() else cell.value
                row.append(str(value))
            else:
                row.append(str(cell.value or "").strip())
        rows.append(row)
    return _rows_to_dicts(rows)


def _read_xls(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return _read_xls_binary(content)
    text_prefix = content[:2048].lstrip().lower()
    if b"<html" in text_prefix or b"<table" in text_prefix:
        return _read_xls_html(content)
    return _read_xls_delimited(content)


def _read_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    return _read_delimited_text(content.decode("utf-8-sig"))


def read_import_rows(content: bytes, filename: str) -> tuple[str, list[str], list[dict[str, str]]]:
    source_format = "xlsx" if zipfile.is_zipfile(io.BytesIO(content)) else _source_format(filename)
    if source_format == "xlsx":
        headers, rows = _read_xlsx(content)
    elif source_format == "xls":
        headers, rows = _read_xls(content)
    else:
        headers, rows = _read_csv(content)
    return source_format, headers, rows


def _is_number(value: str) -> bool:
    try:
        float(value.replace(",", "."))
        return True
    except Exception:
        return False


def _parse_time_fraction(value: str | None) -> float:
    text = _clean_optional(value)
    if not text:
        return 0.0
    if _is_number(text):
        return float(text.replace(",", "."))
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
            return (parsed.hour * 3600 + parsed.minute * 60 + parsed.second) / 86400
        except ValueError:
            pass
    return 0.0


def _parse_datetime(date_value: object, time_value: object | None = None) -> datetime | None:
    date_text = _clean_optional(date_value)
    if not date_text:
        return None
    if _is_number(date_text):
        days = float(date_text.replace(",", ".")) + _parse_time_fraction(_clean(time_value))
        return EXCEL_EPOCH + timedelta(days=days)
    combined = date_text
    time_text = _clean_optional(time_value)
    if time_text:
        if _is_number(time_text):
            time_delta = timedelta(days=float(time_text.replace(",", ".")))
            base = _parse_datetime(date_text)
            return base + time_delta if base else None
        combined = f"{date_text} {time_text}"
    for value in (combined, date_text):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=LOCAL_TZ)
        except ValueError:
            pass
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(combined, fmt)
            return parsed.replace(tzinfo=LOCAL_TZ)
        except ValueError:
            pass
    return None


def _parse_float(value: object) -> tuple[float | None, bool]:
    text = _clean_optional(value)
    if not text:
        return None, False
    try:
        parsed = float(text.replace(",", "."))
    except ValueError:
        return None, True
    if not -180 <= parsed <= 180:
        return None, True
    return parsed, False


def _parse_bool(value: object) -> bool:
    text = _header_key(_clean(value))
    return text in {"SIM", "TRUE", "1", "S"}


def _row_by_target(source_row: dict[str, str]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for header, value in source_row.items():
        target = _target_for_header(header)
        if not target:
            continue
        mapped[target] = _clean(value)
    return mapped


def _join_address(mapped: dict[str, str]) -> str:
    direct = _clean_optional(mapped.get("endereco"))
    if direct:
        return direct
    parts = [_clean_optional(mapped.get("logradouro")), _clean_optional(mapped.get("referencia"))]
    return " - ".join(part for part in parts if part)


def _normalize_record(source_row: dict[str, str]) -> dict:
    mapped = _row_by_target(source_row)
    abertura = _parse_datetime(mapped.get("abertura_em")) or _parse_datetime(mapped.get("data_fato"), mapped.get("hora_fato"))
    registro = _parse_datetime(mapped.get("registro_em")) or _parse_datetime(mapped.get("data_registro"), mapped.get("hora_registro"))
    latitude_raw = _clean_optional(mapped.get("latitude"))
    longitude_raw = _clean_optional(mapped.get("longitude"))
    latitude, latitude_invalid = _parse_float(latitude_raw)
    longitude, longitude_invalid = _parse_float(longitude_raw)
    coordinate_invalid = latitude_invalid or longitude_invalid
    coordinate_missing = not latitude_raw or not longitude_raw
    return {
        "id_origem": _clean_optional(mapped.get("id_origem")),
        "abertura_em": abertura.isoformat() if abertura else "",
        "_abertura_datetime": abertura,
        "registro_em": registro.isoformat() if registro else "",
        "_registro_datetime": registro,
        "municipio": _clean_optional(mapped.get("municipio")),
        "tipo": _clean_optional(mapped.get("tipo")),
        "grupo": _clean_optional(mapped.get("grupo")),
        "subtipo": _clean_optional(mapped.get("subtipo")),
        "unidade_operacional": _clean_optional(mapped.get("unidade_operacional")),
        "bairro": _clean_optional(mapped.get("bairro")),
        "endereco": _join_address(mapped),
        "latitude": latitude,
        "longitude": longitude,
        "codigo_ibge": _clean_optional(mapped.get("codigo_ibge")),
        "segredo_de_justica": _parse_bool(mapped.get("segredo_de_justica")),
        "periodo_registro": _clean_optional(mapped.get("periodo_registro")),
        "_coordenada_invalida": coordinate_invalid,
        "_coordenada_ausente": coordinate_missing,
        "dados_origem": json.dumps(source_row, ensure_ascii=False, separators=(",", ":")),
    }


def _validate_record(record: dict, seen: set[str]) -> list[str]:
    issues = []
    source_id = record["id_origem"]
    if not source_id:
        issues.append("id_origem ausente")
    elif source_id in seen:
        issues.append("id_origem duplicado no arquivo")
    seen.add(source_id)
    if not record["_abertura_datetime"]:
        issues.append("abertura_em inválido")
    if not record["municipio"]:
        issues.append("municipio ausente")
    if not record["tipo"]:
        issues.append("tipo ausente")
    return issues


def _column_mappings(headers: list[str]) -> list[dict]:
    mappings = []
    for header in headers:
        target = _public_target(_target_for_header(header))
        mappings.append({
            "source_header": header,
            "target_field": target,
            "required": target in REQUIRED,
            "status": "reconhecida" if target else "ignorada",
        })
    return mappings


def _parsed_import(content: bytes, filename: str) -> dict:
    source_format, headers, source_rows = read_import_rows(content, filename)
    mappings = _column_mappings(headers)
    recognized = sorted({item["target_field"] for item in mappings if item["target_field"]})
    missing = sorted(REQUIRED - set(recognized))
    profile = _source_profile(headers)
    issues = []
    records = []
    seen: set[str] = set()
    valid = 0
    sensitive_rows = 0
    invalid_coordinate_rows = 0
    missing_coordinate_rows = 0
    for index, source_row in enumerate(source_rows, start=2):
        record = _normalize_record(source_row)
        row_issues = _validate_record(record, seen)
        if record["segredo_de_justica"]:
            sensitive_rows += 1
        if record["_coordenada_invalida"]:
            invalid_coordinate_rows += 1
        if record["_coordenada_ausente"]:
            missing_coordinate_rows += 1
        valid_row = not row_issues and not missing
        if valid_row:
            valid += 1
        else:
            issues.append({"row": index, "issues": row_issues or ["cabeçalhos obrigatórios ausentes"]})
        records.append({"row": index, "record": record, "issues": row_issues})
    warnings = []
    if sensitive_rows:
        warnings.append(f"{sensitive_rows} linha(s) com segredo de justiça identificadas")
    if invalid_coordinate_rows:
        warnings.append(f"{invalid_coordinate_rows} linha(s) com coordenadas inválidas ou não numéricas")
    if missing_coordinate_rows:
        warnings.append(f"{missing_coordinate_rows} linha(s) sem coordenadas completas")
    return {
        "headers": headers,
        "recognized_headers": recognized,
        "missing_required_headers": missing,
        "total_rows": len(source_rows),
        "valid_rows": valid,
        "invalid_rows": (len(source_rows) - valid) if not missing else len(source_rows),
        "issues": issues[:50],
        "can_commit": not missing and not issues,
        "source_format": source_format,
        "source_profile": profile,
        "column_mappings": mappings,
        "unmapped_headers": [item["source_header"] for item in mappings if not item["target_field"]],
        "sensitive_rows": sensitive_rows,
        "invalid_coordinate_rows": invalid_coordinate_rows,
        "missing_coordinate_rows": missing_coordinate_rows,
        "warnings": warnings,
        "_records": records,
    }


def preview_import(content: bytes, filename: str = "arquivo.csv") -> dict:
    parsed = _parsed_import(content, filename)
    return {key: value for key, value in parsed.items() if not key.startswith("_")}


def preview_csv(content: bytes) -> dict:
    return preview_import(content, "arquivo.csv")


def _chunks(values: list[str], size: int = 500):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _existing_source_ids(db: Session, sistema_origem: str, source_ids: list[str]) -> set[str]:
    existing: set[str] = set()
    for chunk in _chunks(source_ids):
        rows = db.scalars(
            select(Occurrence.source_id).where(
                Occurrence.source == sistema_origem,
                Occurrence.source_id.in_(chunk),
            )
        ).all()
        existing.update(rows)
    return existing


def _units_by_name(db: Session, unit_names: list[str]) -> dict[str, Unit]:
    units: dict[str, Unit] = {}
    for chunk in _chunks(unit_names):
        rows = db.scalars(select(Unit).where(Unit.name.in_(chunk))).all()
        units.update({unit.name: unit for unit in rows})
    for name in unit_names:
        if name in units:
            continue
        unit = Unit(name=name, active=True)
        db.add(unit)
        db.flush()
        units[name] = unit
    return units


def commit_import(db: Session, content: bytes, filename: str) -> dict:
    parsed = _parsed_import(content, filename)
    if parsed["missing_required_headers"]:
        return {
            "source_format": parsed["source_format"],
            "source_profile": parsed["source_profile"],
            "source_scope": SISTEMA_ORIGEM_SEJUSP if parsed["source_profile"] == "RELATORIO_SEJUSP" else SISTEMA_ORIGEM_FOCO,
            "total_rows": parsed["total_rows"],
            "inserted_rows": 0,
            "skipped_duplicate_rows": 0,
            "invalid_rows": parsed["invalid_rows"],
            "sensitive_rows": parsed["sensitive_rows"],
            "invalid_coordinate_rows": parsed["invalid_coordinate_rows"],
            "missing_coordinate_rows": parsed["missing_coordinate_rows"],
            "issues": parsed["issues"],
            "warnings": parsed["warnings"],
            "can_commit": False,
        }

    sistema_origem = SISTEMA_ORIGEM_SEJUSP if parsed["source_profile"] == "RELATORIO_SEJUSP" else SISTEMA_ORIGEM_FOCO
    valid_records = [item for item in parsed["_records"] if not item["issues"]]
    source_ids = [item["record"]["id_origem"] for item in valid_records]
    existing = _existing_source_ids(db, sistema_origem, source_ids)
    unit_names = sorted({item["record"]["unidade_operacional"] for item in valid_records if item["record"]["unidade_operacional"]})
    units = _units_by_name(db, unit_names)
    inserted = 0
    skipped = 0
    seen_inserted: set[str] = set()
    for item in valid_records:
        record = item["record"]
        source_id = record["id_origem"]
        if source_id in existing or source_id in seen_inserted:
            skipped += 1
            continue
        unit = units.get(record["unidade_operacional"])
        occurrence = Occurrence(
            source=sistema_origem,
            source_id=source_id,
            external_number=source_id,
            opened_at=record["_abertura_datetime"],
            registered_at=record["_registro_datetime"],
            group_name=record["grupo"] or None,
            type_name=record["tipo"],
            subtype_name=record["subtipo"] or None,
            priority="sigilo_judicial" if record["segredo_de_justica"] else None,
            municipality=record["municipio"],
            neighborhood=record["bairro"] or None,
            address=record["endereco"] or None,
            latitude=record["latitude"],
            longitude=record["longitude"],
            unit_id=unit.id if unit else None,
            status="importada",
            quality_score=0.9 if record["_coordenada_invalida"] else 1.0,
            ibge_code=record["codigo_ibge"] or None,
            judicial_secret=record["segredo_de_justica"],
            source_payload=record["dados_origem"],
        )
        db.add(occurrence)
        inserted += 1
        seen_inserted.add(source_id)
    db.commit()
    invalid_rows = parsed["total_rows"] - len(valid_records)
    return {
        "source_format": parsed["source_format"],
        "source_profile": parsed["source_profile"],
        "source_scope": sistema_origem,
        "total_rows": parsed["total_rows"],
        "inserted_rows": inserted,
        "skipped_duplicate_rows": skipped,
        "invalid_rows": invalid_rows,
        "sensitive_rows": parsed["sensitive_rows"],
        "invalid_coordinate_rows": parsed["invalid_coordinate_rows"],
        "missing_coordinate_rows": parsed["missing_coordinate_rows"],
        "issues": parsed["issues"],
        "warnings": parsed["warnings"],
        "can_commit": parsed["can_commit"],
    }
