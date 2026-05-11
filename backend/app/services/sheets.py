"""
Google Sheets sync service.
Reads structured data from a client's Google Sheet and normalizes it
into the universal transaction format.

Expected Sheet structure (columns):
  Fecha | Monto | Tipo | Categoría | Descripción | Estado | Referencia
"""

import logging
from datetime import datetime
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials
from app.config import get_settings

logger = logging.getLogger("argos.sheets")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Column mapping: expected header → internal field name
COLUMN_MAP = {
    "fecha": "date",
    "monto": "amount",
    "tipo": "type",
    "categoría": "category",
    "categoria": "category",
    "descripción": "description",
    "descripcion": "description",
    "estado": "status",
    "referencia": "reference",
}

# Status normalization
STATUS_MAP = {
    "cobrado": "cobrado",
    "pagado": "pagado",
    "pendiente": "pendiente",
    "cobrada": "cobrado",
    "pagada": "pagado",
    "por cobrar": "pendiente",
    "impago": "pendiente",
}

# Type normalization
TYPE_MAP = {
    "ingreso": "ingreso",
    "gasto": "gasto",
    "venta": "ingreso",
    "compra": "gasto",
    "costo": "gasto",
    "pago": "gasto",
    "cobro": "ingreso",
}


def _get_client() -> gspread.Client:
    s = get_settings()
    creds = Credentials.from_service_account_file(
        s.google_service_account_json, scopes=SCOPES
    )
    return gspread.authorize(creds)


def _normalize_header(header: str) -> Optional[str]:
    """Map a Spanish column header to internal field name."""
    clean = header.strip().lower().replace(" ", "")
    return COLUMN_MAP.get(clean)


def _parse_amount(raw: str) -> float:
    """Parse Argentine-style amounts: 1.234.567,89 or $1,234,567.89"""
    if not raw:
        return 0.0
    cleaned = str(raw).replace("$", "").replace(" ", "").strip()
    # Detect Argentine format (dots as thousands, comma as decimal)
    if "," in cleaned and "." in cleaned:
        if cleaned.rindex(",") > cleaned.rindex("."):
            # Argentine: 1.234.567,89
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # US: 1,234,567.89
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        logger.warning("Could not parse amount: %s", raw)
        return 0.0


def _parse_date(raw: str) -> Optional[str]:
    """Try common date formats."""
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d",
        "%d/%m/%y", "%d-%m-%y",
        "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(str(raw).strip(), fmt).isoformat()
        except ValueError:
            continue
    logger.warning("Could not parse date: %s", raw)
    return None


def fetch_and_normalize(spreadsheet_id: str, sheet_index: int = 0) -> dict:
    """
    Fetch all rows from a Google Sheet and normalize them into
    the universal transaction format.

    Returns: {"rows": [...], "errors": [...], "raw_count": int}
    """
    client = _get_client()
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.get_worksheet(sheet_index)

    all_records = worksheet.get_all_values()
    if len(all_records) < 2:
        return {"rows": [], "errors": ["Sheet vacío o sin datos"], "raw_count": 0}

    # Map headers
    raw_headers = all_records[0]
    col_map = {}
    for i, h in enumerate(raw_headers):
        field = _normalize_header(h)
        if field:
            col_map[field] = i

    required = {"date", "amount", "type", "description"}
    missing = required - set(col_map.keys())
    if missing:
        return {
            "rows": [],
            "errors": [
                "Columnas faltantes: {}. Esperadas: Fecha, Monto, Tipo, Descripción".format(
                    ", ".join(missing)
                )
            ],
            "raw_count": 0,
        }

    rows = []
    errors = []

    for row_num, raw_row in enumerate(all_records[1:], start=2):
        try:
            date_val = _parse_date(raw_row[col_map["date"]])
            if not date_val:
                errors.append("Fila {}: fecha inválida '{}'".format(row_num, raw_row[col_map["date"]]))
                continue

            amount = _parse_amount(raw_row[col_map["amount"]])
            raw_type = raw_row[col_map["type"]].strip().lower()
            tx_type = TYPE_MAP.get(raw_type, "ingreso")
            description = raw_row[col_map["description"]].strip()

            category = ""
            if "category" in col_map:
                category = raw_row[col_map["category"]].strip()

            status = "pendiente"
            if "status" in col_map:
                raw_status = raw_row[col_map["status"]].strip().lower()
                status = STATUS_MAP.get(raw_status, "pendiente")

            reference = ""
            if "reference" in col_map:
                reference = raw_row[col_map["reference"]].strip()

            # Make amounts negative for gastos (stored as absolute in the DB)
            if tx_type == "gasto":
                amount = abs(amount)

            rows.append({
                "date": date_val,
                "amount": amount,
                "type": tx_type,
                "category": category or "Sin clasificar",
                "description": description,
                "status": status,
                "reference": reference,
            })

        except Exception as e:
            errors.append("Fila {}: {}".format(row_num, str(e)))
            continue

    return {"rows": rows, "errors": errors, "raw_count": len(all_records) - 1}
