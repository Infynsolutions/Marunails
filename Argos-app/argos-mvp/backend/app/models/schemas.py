from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


# ── Enums ──

class TransactionType(str, Enum):
    ingreso = "ingreso"
    gasto = "gasto"


class TransactionStatus(str, Enum):
    cobrado = "cobrado"
    pagado = "pagado"
    pendiente = "pendiente"


class AlertSeverity(str, Enum):
    critica = "critica"
    advertencia = "advertencia"
    info = "info"


class AlertStatus(str, Enum):
    activa = "activa"
    resuelta = "resuelta"


# ── Transactions ──

class Transaction(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    date: datetime
    amount: float
    type: TransactionType
    category: str
    description: str
    status: TransactionStatus
    reference: Optional[str] = None
    product_id: Optional[str] = None
    created_at: Optional[datetime] = None


class TransactionCreate(BaseModel):
    date: datetime
    amount: float
    type: TransactionType
    category: str
    description: str
    status: TransactionStatus = TransactionStatus.pendiente
    reference: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[int] = None


class TransactionList(BaseModel):
    transactions: list[Transaction]
    total: int
    last_sync: Optional[datetime] = None


# ── KPIs / Dashboard ──

class KPI(BaseModel):
    label: str
    value: float
    formatted: str
    change_pct: Optional[float] = None
    change_label: Optional[str] = None
    trend: Optional[str] = None  # "up" | "down" | "flat"
    sparkline: Optional[list[float]] = None


class CategoryBreakdown(BaseModel):
    category: str
    amount: float
    percentage: float
    color: Optional[str] = None


class MonthlyComparison(BaseModel):
    month: str
    ingresos: float
    gastos: float


class DashboardData(BaseModel):
    kpis: list[KPI]
    monthly_chart: list[MonthlyComparison]
    category_breakdown: list[CategoryBreakdown]
    recent_transactions: list[Transaction]
    last_sync: Optional[datetime] = None


# ── Chat ──

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_used: Optional[list[str]] = None


# ── Alerts ──

class Alert(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    severity: AlertSeverity
    title: str
    body: str
    status: AlertStatus = AlertStatus.activa
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class AlertList(BaseModel):
    alerts: list[Alert]
    counts: dict  # {"critica": 2, "advertencia": 3, "resuelta": 8}


# ── Sync ──

class SyncRequest(BaseModel):
    spreadsheet_id: Optional[str] = None
    force: bool = False


class SyncResponse(BaseModel):
    success: bool
    rows_processed: int
    rows_new: int
    rows_updated: int
    errors: list[str] = []
    timestamp: datetime


# ── Tenant ──

class Tenant(BaseModel):
    id: str
    name: str
    plan: str = "starter"
    currency: str = "ARS"
    timezone: str = "America/Argentina/Buenos_Aires"
    spreadsheet_ids: list[str] = []
    created_at: Optional[datetime] = None


# ── Products ──

class ProductCreate(BaseModel):
    name: str
    sku: str
    unit_price: float
    min_threshold: int = 3


class Product(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    name: str
    sku: str
    unit_price: float
    min_threshold: int = 3
    created_at: Optional[datetime] = None


class ProductResponse(Product):
    current_stock: int = 0


# ── Stock Movements ──

class StockMovementCreate(BaseModel):
    product_id: str
    type: Literal["entrada", "salida", "venta", "ajuste"]
    quantity: int
    note: Optional[str] = None
    date: Optional[datetime] = None


class StockMovement(BaseModel):
    id: Optional[str] = None
    tenant_id: str
    product_id: str
    type: str
    quantity: int
    note: Optional[str] = None
    date: datetime
    created_at: Optional[datetime] = None


class StockSummary(BaseModel):
    products: list[ProductResponse]
    low_stock_count: int


# ── Report ──

class CategoryLine(BaseModel):
    category: str
    amount: float
    percentage: float


class ReportData(BaseModel):
    year: int
    month: int
    month_label: str
    ingresos: float
    gastos: float
    margen: float
    saldo: float
    ingresos_prev: float
    gastos_prev: float
    margen_prev: float
    ingresos_change: float
    gastos_change: float
    gastos_por_categoria: list[CategoryLine]
    ingresos_por_categoria: list[CategoryLine]
    transacciones: list[Transaction]
    formatted_ingresos: str
    formatted_gastos: str
    formatted_saldo: str


# ── Collections ──

class CollectionItem(BaseModel):
    id: str
    date: datetime
    amount: float
    description: str
    category: str
    reference: Optional[str] = None
    days_pending: int
    bucket: str  # "al_dia" | "por_vencer" | "vencida"
    formatted_amount: str


class CollectionsSummary(BaseModel):
    total_pendiente: float
    total_count: int
    al_dia: list[CollectionItem]
    por_vencer: list[CollectionItem]
    vencidas: list[CollectionItem]
    formatted_total: str
