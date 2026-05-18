"""
Dashboard service — calculates KPIs, charts, and breakdowns
from raw transaction data.
"""

from datetime import datetime
from collections import defaultdict
from app.services import database as db
from app.models.schemas import (
    KPI, CategoryBreakdown, MonthlyComparison,
    Transaction, DashboardData,
    CategoryLine, ReportData, CollectionItem, CollectionsSummary,
)

_MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


def _format_ars(amount: float) -> str:
    """Format as Argentine pesos."""
    if abs(amount) >= 1_000_000:
        return "${:,.0f}".format(amount).replace(",", ".")
    return "${:,.0f}".format(amount).replace(",", ".")


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round((current - previous) / previous * 100, 1)


def _sparkline(transactions: list[dict], tx_type: str, days: int = 7) -> list[float]:
    """Generate a simple sparkline from recent daily totals."""
    now = datetime.utcnow()
    daily = defaultdict(float)
    for t in transactions:
        if t["type"] == tx_type:
            try:
                d = datetime.fromisoformat(t["date"]).date()
                daily[d] += t["amount"]
            except (ValueError, KeyError):
                continue

    values = []
    for i in range(days - 1, -1, -1):
        day = (now.date().__class__.fromordinal(now.date().toordinal() - i))
        values.append(daily.get(day, 0))

    # Normalize to 0-100 range
    max_val = max(values) if values and max(values) > 0 else 1
    return [round(v / max_val * 100, 1) for v in values]


def get_dashboard(tenant_id: str) -> DashboardData:
    raw = db.get_dashboard_data(tenant_id)

    current = raw["current_month"]
    previous = raw["previous_month"]

    # ── Calculate KPIs ──
    ingresos = sum(t["amount"] for t in current if t["type"] == "ingreso")
    gastos = sum(t["amount"] for t in current if t["type"] == "gasto")
    ingresos_prev = sum(t["amount"] for t in previous if t["type"] == "ingreso")
    gastos_prev = sum(t["amount"] for t in previous if t["type"] == "gasto")

    margen = (ingresos - gastos) / ingresos * 100 if ingresos > 0 else 0
    margen_prev = (ingresos_prev - gastos_prev) / ingresos_prev * 100 if ingresos_prev > 0 else 0

    saldo = ingresos - gastos

    ing_change = _pct_change(ingresos, ingresos_prev)
    gas_change = _pct_change(gastos, gastos_prev)
    mar_change = round(margen - margen_prev, 1)

    kpis = [
        KPI(
            label="Ingresos del mes",
            value=ingresos,
            formatted=_format_ars(ingresos),
            change_pct=ing_change,
            change_label="{}{}% vs mes anterior".format("+" if ing_change >= 0 else "", ing_change),
            trend="up" if ing_change >= 0 else "down",
            sparkline=_sparkline(current, "ingreso"),
        ),
        KPI(
            label="Gastos operativos",
            value=gastos,
            formatted=_format_ars(gastos),
            change_pct=gas_change,
            change_label="{}{}% vs mes anterior".format("+" if gas_change >= 0 else "", gas_change),
            trend="down" if gas_change > 0 else "up",  # For gastos, up is bad
            sparkline=_sparkline(current, "gasto"),
        ),
        KPI(
            label="Margen bruto",
            value=margen,
            formatted="{:.1f}%".format(margen),
            change_pct=mar_change,
            change_label="{}{}pp vs mes anterior".format("+" if mar_change >= 0 else "", mar_change),
            trend="up" if mar_change >= 0 else "down",
        ),
        KPI(
            label="Saldo neto",
            value=saldo,
            formatted=_format_ars(saldo),
            trend="up" if saldo > 0 else "down",
        ),
    ]

    # ── Monthly chart (last 7 months) ──
    monthly_data = defaultdict(lambda: {"ingresos": 0, "gastos": 0})
    for t in raw["chart_data"]:
        try:
            d = datetime.fromisoformat(t["date"])
            key = d.strftime("%b")
            if t["type"] == "ingreso":
                monthly_data[key]["ingresos"] += t["amount"]
            else:
                monthly_data[key]["gastos"] += t["amount"]
        except (ValueError, KeyError):
            continue

    monthly_chart = [
        MonthlyComparison(month=m, ingresos=v["ingresos"], gastos=v["gastos"])
        for m, v in monthly_data.items()
    ]

    # ── Category breakdown ──
    cat_totals = defaultdict(float)
    for t in current:
        if t["type"] == "ingreso":
            cat_totals[t.get("category", "Sin clasificar")] += t["amount"]

    total_cat = sum(cat_totals.values()) or 1
    colors = ["#16a34a", "#3b82f6", "#f59e0b", "#94a3b8", "#ef4444", "#8b5cf6"]
    category_breakdown = [
        CategoryBreakdown(
            category=cat,
            amount=amt,
            percentage=round(amt / total_cat * 100, 1),
            color=colors[i % len(colors)],
        )
        for i, (cat, amt) in enumerate(
            sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        )
    ]

    # ── Recent transactions ──
    recent_txs = [
        Transaction(
            id=t.get("id"),
            tenant_id=tenant_id,
            date=t["date"],
            amount=t["amount"],
            type=t["type"],
            category=t.get("category", ""),
            description=t.get("description", ""),
            status=t.get("status", "pendiente"),
            reference=t.get("reference"),
        )
        for t in raw["recent_transactions"][:10]
    ]

    return DashboardData(
        kpis=kpis,
        monthly_chart=monthly_chart,
        category_breakdown=category_breakdown,
        recent_transactions=recent_txs,
        last_sync=raw.get("last_sync"),
    )


def get_report(tenant_id: str, year: int, month: int) -> ReportData:
    raw = db.get_report_data(tenant_id, year, month)
    current = raw["current"]
    previous = raw["previous"]

    ingresos = sum(t["amount"] for t in current if t["type"] == "ingreso")
    gastos = sum(t["amount"] for t in current if t["type"] == "gasto")
    ingresos_prev = sum(t["amount"] for t in previous if t["type"] == "ingreso")
    gastos_prev = sum(t["amount"] for t in previous if t["type"] == "gasto")

    margen = (ingresos - gastos) / ingresos * 100 if ingresos > 0 else 0.0
    margen_prev = (ingresos_prev - gastos_prev) / ingresos_prev * 100 if ingresos_prev > 0 else 0.0

    gastos_cat: dict = defaultdict(float)
    ingresos_cat: dict = defaultdict(float)
    for t in current:
        cat = t.get("category") or "Sin clasificar"
        if t["type"] == "gasto":
            gastos_cat[cat] += t["amount"]
        else:
            ingresos_cat[cat] += t["amount"]

    total_g = sum(gastos_cat.values()) or 1
    total_i = sum(ingresos_cat.values()) or 1

    gastos_por_categoria = [
        CategoryLine(category=cat, amount=amt, percentage=round(amt / total_g * 100, 1))
        for cat, amt in sorted(gastos_cat.items(), key=lambda x: x[1], reverse=True)
    ]
    ingresos_por_categoria = [
        CategoryLine(category=cat, amount=amt, percentage=round(amt / total_i * 100, 1))
        for cat, amt in sorted(ingresos_cat.items(), key=lambda x: x[1], reverse=True)
    ]

    transactions = [
        Transaction(
            id=t.get("id"),
            tenant_id=tenant_id,
            date=t["date"],
            amount=t["amount"],
            type=t["type"],
            category=t.get("category") or "",
            description=t.get("description") or "",
            status=t.get("status") or "pendiente",
            reference=t.get("reference"),
        )
        for t in current
    ]

    return ReportData(
        year=year,
        month=month,
        month_label=f"{_MESES.get(month, str(month))} {year}",
        ingresos=ingresos,
        gastos=gastos,
        margen=round(margen, 1),
        saldo=ingresos - gastos,
        ingresos_prev=ingresos_prev,
        gastos_prev=gastos_prev,
        margen_prev=round(margen_prev, 1),
        ingresos_change=_pct_change(ingresos, ingresos_prev),
        gastos_change=_pct_change(gastos, gastos_prev),
        gastos_por_categoria=gastos_por_categoria,
        ingresos_por_categoria=ingresos_por_categoria,
        transacciones=transactions,
        formatted_ingresos=_format_ars(ingresos),
        formatted_gastos=_format_ars(gastos),
        formatted_saldo=_format_ars(ingresos - gastos),
    )


def get_collections_summary(tenant_id: str) -> CollectionsSummary:
    pending = db.get_pending_collections(tenant_id)
    now = datetime.utcnow()

    items = []
    for t in pending:
        try:
            raw_date = str(t["date"]).replace("Z", "").split("+")[0]
            tx_date = datetime.fromisoformat(raw_date)
            days = max(0, (now - tx_date).days)
        except Exception:
            days = 0

        if days <= 7:
            bucket = "al_dia"
        elif days <= 30:
            bucket = "por_vencer"
        else:
            bucket = "vencida"

        items.append(CollectionItem(
            id=t["id"],
            date=t["date"],
            amount=t["amount"],
            description=t.get("description") or "",
            category=t.get("category") or "",
            reference=t.get("reference"),
            days_pending=days,
            bucket=bucket,
            formatted_amount=_format_ars(t["amount"]),
        ))

    al_dia = [i for i in items if i.bucket == "al_dia"]
    por_vencer = [i for i in items if i.bucket == "por_vencer"]
    vencidas = sorted(
        [i for i in items if i.bucket == "vencida"],
        key=lambda x: x.days_pending,
        reverse=True,
    )
    total = sum(i.amount for i in items)

    return CollectionsSummary(
        total_pendiente=total,
        total_count=len(items),
        al_dia=al_dia,
        por_vencer=por_vencer,
        vencidas=vencidas,
        formatted_total=_format_ars(total),
    )
