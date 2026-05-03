"""
Supabase data layer — all DB operations go through here.
Multi-tenant isolation: every query filters by tenant_id.
"""

from datetime import datetime, timedelta
from typing import Optional
from supabase import create_client, Client
from app.config import get_settings

_client: Optional[Client] = None


def get_db() -> Client:
    global _client
    if _client is None:
        s = get_settings()
        _client = create_client(s.supabase_url, s.supabase_service_key)
    return _client


# ── Transactions ──

def get_transactions(tenant_id: str, limit: int = 50, offset: int = 0) -> dict:
    db = get_db()
    result = (
        db.table("transactions")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("date", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    count_result = (
        db.table("transactions")
        .select("id", count="exact")
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return {"data": result.data, "total": count_result.count or 0}


def upsert_transactions(tenant_id: str, rows: list[dict]) -> dict:
    db = get_db()
    for row in rows:
        row["tenant_id"] = tenant_id
    result = db.table("transactions").upsert(rows, on_conflict="tenant_id,date,description").execute()
    return {"upserted": len(result.data)}


# ── KPI Calculations ──

def get_dashboard_data(tenant_id: str) -> dict:
    db = get_db()
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Current month transactions
    current = (
        db.table("transactions")
        .select("*")
        .eq("tenant_id", tenant_id)
        .gte("date", month_start.isoformat())
        .execute()
    )

    # Previous month transactions
    previous = (
        db.table("transactions")
        .select("*")
        .eq("tenant_id", tenant_id)
        .gte("date", prev_month_start.isoformat())
        .lt("date", month_start.isoformat())
        .execute()
    )

    # Last 7 months for chart
    seven_months_ago = month_start - timedelta(days=210)
    chart_data = (
        db.table("transactions")
        .select("*")
        .eq("tenant_id", tenant_id)
        .gte("date", seven_months_ago.isoformat())
        .order("date")
        .execute()
    )

    # Recent transactions for the table
    recent = (
        db.table("transactions")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("date", desc=True)
        .limit(10)
        .execute()
    )

    # Last sync timestamp
    sync = (
        db.table("sync_log")
        .select("completed_at")
        .eq("tenant_id", tenant_id)
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    last_sync = sync.data[0]["completed_at"] if sync.data else None

    return {
        "current_month": current.data,
        "previous_month": previous.data,
        "chart_data": chart_data.data,
        "recent_transactions": recent.data,
        "last_sync": last_sync,
    }


# ── Alerts ──

def get_alerts(tenant_id: str, status: Optional[str] = None) -> list[dict]:
    db = get_db()
    query = db.table("alerts").select("*").eq("tenant_id", tenant_id)
    if status:
        query = query.eq("status", status)
    result = query.order("created_at", desc=True).execute()
    return result.data


def create_alert(alert: dict) -> dict:
    db = get_db()
    result = db.table("alerts").insert(alert).execute()
    return result.data[0] if result.data else {}


def resolve_alert(alert_id: str, tenant_id: str) -> dict:
    db = get_db()
    result = (
        db.table("alerts")
        .update({"status": "resuelta", "resolved_at": datetime.utcnow().isoformat()})
        .eq("id", alert_id)
        .eq("tenant_id", tenant_id)
        .execute()
    )
    return result.data[0] if result.data else {}


# ── Chat Sessions ──

def save_chat_message(tenant_id: str, session_id: str, role: str, content: str) -> None:
    db = get_db()
    db.table("chat_messages").insert({
        "tenant_id": tenant_id,
        "session_id": session_id,
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
    }).execute()


def get_chat_history(tenant_id: str, session_id: str, limit: int = 20) -> list[dict]:
    db = get_db()
    result = (
        db.table("chat_messages")
        .select("role, content, created_at")
        .eq("tenant_id", tenant_id)
        .eq("session_id", session_id)
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return result.data


# ── Sync Log ──

def log_sync(tenant_id: str, rows_processed: int, rows_new: int, rows_updated: int, errors: list[str]) -> None:
    db = get_db()
    db.table("sync_log").insert({
        "tenant_id": tenant_id,
        "rows_processed": rows_processed,
        "rows_new": rows_new,
        "rows_updated": rows_updated,
        "errors": errors,
        "completed_at": datetime.utcnow().isoformat(),
    }).execute()


# ── Tenant ──

def get_tenant(tenant_id: str) -> Optional[dict]:
    db = get_db()
    result = db.table("tenants").select("*").eq("id", tenant_id).limit(1).execute()
    return result.data[0] if result.data else None


# ── Last Sync ──

def get_last_sync(tenant_id: str) -> Optional[str]:
    db = get_db()
    result = (
        db.table("sync_log")
        .select("completed_at")
        .eq("tenant_id", tenant_id)
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0]["completed_at"] if result.data else None


# ── Transactions (write) ──

def create_transaction(tenant_id: str, data: dict) -> dict:
    db = get_db()
    data["tenant_id"] = tenant_id
    result = db.table("transactions").insert(data).execute()
    return result.data[0] if result.data else {}


# ── Products ──

def create_product(tenant_id: str, data: dict) -> dict:
    db = get_db()
    data["tenant_id"] = tenant_id
    result = db.table("products").insert(data).execute()
    return result.data[0] if result.data else {}


def get_products(tenant_id: str) -> list[dict]:
    """Returns all products with current_stock via the product_stock view (D4)."""
    db = get_db()
    result = (
        db.table("product_stock")
        .select("*")
        .eq("tenant_id", tenant_id)
        .order("name")
        .execute()
    )
    return result.data


def get_product_by_sku(tenant_id: str, sku: str) -> Optional[dict]:
    db = get_db()
    result = (
        db.table("product_stock")
        .select("*")
        .eq("tenant_id", tenant_id)
        .eq("sku", sku)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Stock Movements ──

def create_stock_movement(tenant_id: str, data: dict) -> dict:
    db = get_db()
    data["tenant_id"] = tenant_id
    result = db.table("stock_movements").insert(data).execute()
    return result.data[0] if result.data else {}


# ── create_sale RPC (D2 — atomic Transaction + StockMovement) ──

def create_sale(tenant_id: str, product_id: str, quantity: int, amount: float,
                category: str, description: str, date: str,
                status: str = "pendiente", reference: str = "") -> dict:
    db = get_db()
    result = db.rpc("create_sale", {
        "p_tenant_id": tenant_id,
        "p_product_id": product_id,
        "p_quantity": quantity,
        "p_amount": amount,
        "p_category": category,
        "p_description": description,
        "p_date": date,
        "p_status": status,
        "p_reference": reference,
    }).execute()
    return result.data if result.data else {}
