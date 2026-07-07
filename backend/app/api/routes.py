"""
API v1 Routers — all endpoints for the Argos MVP.
Each endpoint validates tenant_id for multi-tenant isolation.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    DashboardData, TransactionList, TransactionCreate, Transaction,
    ChatRequest, ChatResponse,
    SyncRequest, SyncResponse, AlertList,
    ProductCreate, ProductResponse, StockMovementCreate, StockMovement, StockSummary,
)
from app.services import database as db
from app.services import dashboard as dash_service
from app.services import chat as chat_service
from app.services import sheets as sheets_service

logger = logging.getLogger("argos.api")

router = APIRouter(prefix="/api/v1")


# ── Health ──

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "argos-api", "version": "0.1.0"}


# ── Dashboard ──

@router.get("/dashboard/{tenant_id}", response_model=DashboardData)
async def get_dashboard(tenant_id: str):
    """Get full dashboard data: KPIs, charts, breakdown, recent transactions."""
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    try:
        return dash_service.get_dashboard(tenant_id)
    except Exception as e:
        logger.error("Dashboard error for %s: %s", tenant_id, e)
        raise HTTPException(status_code=500, detail="Error cargando el dashboard")


# ── Transactions ──

@router.get("/transactions/{tenant_id}", response_model=TransactionList)
async def get_transactions(tenant_id: str, limit: int = 50, offset: int = 0):
    """Get paginated transactions for a tenant."""
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    result = db.get_transactions(tenant_id, limit=limit, offset=offset)
    last_sync = db.get_last_sync(tenant_id)
    return TransactionList(
        transactions=result["data"],
        total=result["total"],
        last_sync=last_sync,
    )


# ── Chat ──

@router.post("/chat/{tenant_id}", response_model=ChatResponse)
async def chat_with_argos(tenant_id: str, req: ChatRequest):
    """Send a message to Argos and get an AI response with business context."""
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Mensaje vacío")

    try:
        result = await chat_service.chat(
            tenant_id=tenant_id,
            user_message=req.message,
            session_id=req.session_id,
        )
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
        )
    except Exception as e:
        logger.error("Chat error for %s: %s", tenant_id, e)
        raise HTTPException(
            status_code=500,
            detail="Error procesando tu consulta. Intentá de nuevo.",
        )


# ── Sync ──

@router.post("/sync/{tenant_id}", response_model=SyncResponse)
async def sync_sheets(tenant_id: str, req: SyncRequest):
    """Sync data from Google Sheets into the database."""
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    # D3: new tenants use web-first data entry, not Sheets sync
    if not (tenant.get("config") or {}).get("sheets_enabled", False):
        raise HTTPException(
            status_code=403,
            detail="Sincronización con Sheets no disponible. Cargá tus datos desde la app.",
        )

    spreadsheet_ids = tenant.get("spreadsheet_ids", [])
    if req.spreadsheet_id:
        spreadsheet_ids = [req.spreadsheet_id]

    if not spreadsheet_ids:
        raise HTTPException(
            status_code=400,
            detail="No hay hojas de cálculo configuradas para esta empresa",
        )

    total_processed = 0
    total_new = 0
    total_updated = 0
    all_errors = []

    for sid in spreadsheet_ids:
        try:
            result = sheets_service.fetch_and_normalize(sid)
            rows = result["rows"]
            all_errors.extend(result["errors"])
            total_processed += result["raw_count"]

            if rows:
                upsert_result = db.upsert_transactions(tenant_id, rows)
                total_new += upsert_result.get("upserted", 0)

        except Exception as e:
            logger.error("Sync error for sheet %s: %s", sid, e)
            all_errors.append("Error sincronizando hoja {}: {}".format(sid[:8], str(e)))

    # Log the sync
    db.log_sync(tenant_id, total_processed, total_new, total_updated, all_errors)

    return SyncResponse(
        success=len(all_errors) == 0,
        rows_processed=total_processed,
        rows_new=total_new,
        rows_updated=total_updated,
        errors=all_errors,
        timestamp=datetime.utcnow(),
    )


# ── Alerts ──

@router.get("/alerts/{tenant_id}", response_model=AlertList)
async def get_alerts(tenant_id: str):
    """Get all alerts for a tenant with severity counts."""
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    alerts = db.get_alerts(tenant_id)

    counts = {"critica": 0, "advertencia": 0, "resuelta": 0}
    for a in alerts:
        if a["status"] == "resuelta":
            counts["resuelta"] += 1
        else:
            counts[a.get("severity", "info")] = counts.get(a.get("severity", "info"), 0) + 1

    return AlertList(alerts=alerts, counts=counts)


@router.post("/alerts/{tenant_id}/{alert_id}/resolve")
async def resolve_alert(tenant_id: str, alert_id: str):
    """Mark an alert as resolved."""
    result = db.resolve_alert(alert_id, tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"status": "resolved", "alert_id": alert_id}


# ── Transactions (write) ──

@router.post("/transactions/{tenant_id}", response_model=dict)
async def create_transaction(tenant_id: str, req: TransactionCreate):
    """Register a new sale (ingreso) or expense (gasto).
    When type=ingreso and product_id+quantity provided, atomically creates a StockMovement via RPC.
    """
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")

    if req.type.value == "ingreso" and req.product_id and req.quantity:
        try:
            return db.create_sale(
                tenant_id=tenant_id,
                product_id=req.product_id,
                quantity=req.quantity,
                amount=req.amount,
                category=req.category,
                description=req.description,
                date=req.date.isoformat(),
                status=req.status.value,
                reference=req.reference or "",
            )
        except Exception as e:
            logger.error("create_sale error for %s: %s", tenant_id, e)
            raise HTTPException(status_code=500, detail="Error registrando la venta")

    try:
        data = req.model_dump(exclude_none=True)
        data["type"] = req.type.value
        data["status"] = req.status.value
        data["date"] = req.date.isoformat()
        result = db.create_transaction(tenant_id, data)
        return result
    except Exception as e:
        logger.error("create_transaction error for %s: %s", tenant_id, e)
        raise HTTPException(status_code=500, detail="Error registrando la transacción")


# ── Products ──

@router.post("/products/{tenant_id}", response_model=dict)
async def create_product(tenant_id: str, req: ProductCreate):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    try:
        return db.create_product(tenant_id, req.model_dump())
    except Exception as e:
        logger.error("create_product error for %s: %s", tenant_id, e)
        raise HTTPException(status_code=500, detail="Error creando el producto")


@router.get("/products/{tenant_id}", response_model=list[ProductResponse])
async def list_products(tenant_id: str):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db.get_products(tenant_id)


@router.get("/products/{tenant_id}/{sku}", response_model=ProductResponse)
async def get_product(tenant_id: str, sku: str):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    product = db.get_product_by_sku(tenant_id, sku)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


# ── Stock ──

@router.post("/stock-movement/{tenant_id}", response_model=dict)
async def add_stock_movement(tenant_id: str, req: StockMovementCreate):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    try:
        data = req.model_dump(exclude_none=True)
        data["date"] = (req.date or datetime.utcnow()).isoformat()
        return db.create_stock_movement(tenant_id, data)
    except Exception as e:
        logger.error("stock_movement error for %s: %s", tenant_id, e)
        raise HTTPException(status_code=500, detail="Error registrando movimiento de stock")


@router.get("/stock/{tenant_id}", response_model=StockSummary)
async def get_stock(tenant_id: str):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    products = db.get_products(tenant_id)
    low_stock = sum(1 for p in products if p.get("current_stock", 0) <= p.get("min_threshold", 3))
    return StockSummary(products=products, low_stock_count=low_stock)


@router.get("/stock-movements/{tenant_id}")
async def get_stock_movements(tenant_id: str, limit: int = 100):
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return db.get_stock_movements(tenant_id, limit=limit)
