"""
Argos AI Chat Service — powered by Claude API.
Injects tenant financial context into the system prompt
and handles conversational queries about the business.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional
import anthropic
from app.config import get_settings
from app.services import database as db

logger = logging.getLogger("argos.chat")

OWNER_PROMPT_TEMPLATE = """Sos Argos, el asistente financiero IA de {empresa}.
Tenés acceso a los datos financieros actualizados de la empresa.

DATOS ACTUALES DEL NEGOCIO:
{contexto_financiero}

REGLAS:
- Respondé siempre en español rioplatense, de forma clara y orientada a la acción.
- Usá números concretos de los datos cuando respondas.
- Si detectás algo preocupante, mencionalo proactivamente.
- Formateá montos con punto como separador de miles (ej: $1.234.567).
- Sé conciso pero completo. Priorizá la información más relevante.
- Cuando hables de tendencias, compará siempre con el período anterior.
- No inventes datos que no tenés. Basate estrictamente en la información proporcionada.
"""

EMPLOYEE_PROMPT_TEMPLATE = """Sos Argos, el asistente operativo de {empresa}.
Ayudás al equipo con consultas de stock y ventas del día.

DATOS OPERATIVOS HOY:
{contexto_operativo}

REGLAS:
- Respondé siempre en español rioplatense, de forma práctica y directa.
- Solo tenés acceso a stock y ventas del día — no tenés datos de márgenes, P&L ni totales financieros.
- Si te preguntan algo financiero (ganancias, costos totales, rentabilidad), decí que esa información
  la ve el dueño y no está disponible para empleados.
- No inventes datos que no tenés.
"""


def _build_financial_context(tenant_id: str) -> str:
    """Build a text summary of the tenant's financial data for the system prompt."""
    data = db.get_dashboard_data(tenant_id)

    current = data["current_month"]
    previous = data["previous_month"]

    # Calculate KPIs
    ingresos_actual = sum(t["amount"] for t in current if t["type"] == "ingreso")
    gastos_actual = sum(t["amount"] for t in current if t["type"] == "gasto")
    ingresos_prev = sum(t["amount"] for t in previous if t["type"] == "ingreso")
    gastos_prev = sum(t["amount"] for t in previous if t["type"] == "gasto")

    margen_actual = ((ingresos_actual - gastos_actual) / ingresos_actual * 100) if ingresos_actual > 0 else 0
    margen_prev = ((ingresos_prev - gastos_prev) / ingresos_prev * 100) if ingresos_prev > 0 else 0

    # Pending invoices
    pendientes = [t for t in current if t["status"] == "pendiente" and t["type"] == "ingreso"]
    total_pendiente = sum(t["amount"] for t in pendientes)

    # Category breakdown
    categorias = {}
    for t in current:
        cat = t.get("category", "Sin clasificar")
        if cat not in categorias:
            categorias[cat] = {"ingresos": 0, "gastos": 0}
        if t["type"] == "ingreso":
            categorias[cat]["ingresos"] += t["amount"]
        else:
            categorias[cat]["gastos"] += t["amount"]

    now = datetime.utcnow()
    mes_actual = now.strftime("%B %Y")

    lines = [
        "Período: {} (datos al {})".format(mes_actual, now.strftime("%d/%m/%Y")),
        "",
        "RESUMEN MES ACTUAL:",
        "- Ingresos: ${:,.0f}".format(ingresos_actual),
        "- Gastos: ${:,.0f}".format(gastos_actual),
        "- Margen bruto: {:.1f}%".format(margen_actual),
        "- Saldo neto del mes: ${:,.0f}".format(ingresos_actual - gastos_actual),
        "",
        "COMPARATIVA MES ANTERIOR:",
        "- Ingresos mes anterior: ${:,.0f}".format(ingresos_prev),
        "- Gastos mes anterior: ${:,.0f}".format(gastos_prev),
        "- Margen mes anterior: {:.1f}%".format(margen_prev),
        "",
        "CUENTAS POR COBRAR:",
        "- Facturas pendientes: {}".format(len(pendientes)),
        "- Total pendiente: ${:,.0f}".format(total_pendiente),
    ]

    if pendientes:
        lines.append("- Detalle:")
        for p in pendientes[:10]:
            lines.append("  · {} — ${:,.0f} ({})".format(
                p["description"], p["amount"], p["date"][:10]
            ))

    lines.append("")
    lines.append("DISTRIBUCIÓN POR CATEGORÍA (mes actual):")
    for cat, vals in sorted(categorias.items(), key=lambda x: x[1]["ingresos"] + x[1]["gastos"], reverse=True):
        lines.append("- {}: ingresos ${:,.0f} / gastos ${:,.0f}".format(
            cat, vals["ingresos"], vals["gastos"]
        ))

    # Recent transactions
    recent = data["recent_transactions"][:5]
    if recent:
        lines.append("")
        lines.append("ÚLTIMAS 5 TRANSACCIONES:")
        for t in recent:
            signo = "+" if t["type"] == "ingreso" else "-"
            lines.append("- {} | {}{:,.0f} | {} | {} | {}".format(
                t["date"][:10], signo, t["amount"], t["category"], t["status"], t["description"]
            ))

    return "\n".join(lines)


def _build_employee_context(tenant_id: str) -> str:
    """Scoped context for employees — stock + today's sales only, no financials."""
    data = db.get_dashboard_data(tenant_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    today_sales = [
        t for t in data["recent_transactions"]
        if t["type"] == "ingreso" and t["date"][:10] == today
    ]
    total_today = sum(t["amount"] for t in today_sales)

    lines = [
        "Ventas de hoy ({} transacciones): ${:,.0f}".format(len(today_sales), total_today),
    ]
    for t in today_sales[:10]:
        lines.append("  · {} — ${:,.0f} ({})".format(t["description"], t["amount"], t["status"]))

    return "\n".join(lines)


async def chat(
    tenant_id: str,
    user_message: str,
    session_id: Optional[str] = None,
    role: str = "owner",
) -> dict:
    """Process a chat message. Role determines financial context depth."""
    settings = get_settings()

    if not session_id:
        session_id = str(uuid.uuid4())

    tenant = db.get_tenant(tenant_id)
    if not tenant:
        return {
            "response": "No encontré datos para esta empresa. Verificá la configuración.",
            "session_id": session_id,
        }

    empresa_name = tenant.get("name", "tu empresa")

    try:
        if role == "employee":
            contexto = _build_employee_context(tenant_id)
            system_prompt = EMPLOYEE_PROMPT_TEMPLATE.format(
                empresa=empresa_name,
                contexto_operativo=contexto,
            )
        else:
            contexto = _build_financial_context(tenant_id)
            system_prompt = OWNER_PROMPT_TEMPLATE.format(
                empresa=empresa_name,
                contexto_financiero=contexto,
            )
    except Exception as e:
        logger.error("Error building context for tenant %s: %s", tenant_id, e)
        system_prompt = "Sos Argos, el asistente de {empresa}. Los datos no están disponibles en este momento.".format(empresa=empresa_name)

    history = db.get_chat_history(tenant_id, session_id, limit=10)
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in history]
    messages.append({"role": "user", "content": user_message})

    db.save_chat_message(tenant_id, session_id, "user", user_message)

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        ai_response = response.content[0].text

        # Track token usage for billing limits (M3)
        usage = response.usage
        if usage:
            _track_token_usage(tenant_id, usage.input_tokens + usage.output_tokens, settings)

    except anthropic.APITimeoutError:
        logger.error("Claude API timeout for tenant %s", tenant_id)
        ai_response = "Disculpá, tardé demasiado en procesar tu consulta. ¿Podés intentar de nuevo?"
    except Exception as e:
        logger.error("Claude API error for tenant %s: %s", tenant_id, e)
        ai_response = "Hubo un error al procesar tu consulta. Por favor intentá de nuevo en unos segundos."

    db.save_chat_message(tenant_id, session_id, "assistant", ai_response)

    return {
        "response": ai_response,
        "session_id": session_id,
    }


def _track_token_usage(tenant_id: str, tokens: int, settings) -> None:
    """Upsert token usage into tenant_usage. Logs warnings at thresholds."""
    try:
        from datetime import date
        month_start = date.today().replace(day=1).isoformat()
        admin = db.get_admin_db()
        result = admin.rpc("increment_token_usage", {
            "p_tenant_id": tenant_id,
            "p_month": month_start,
            "p_tokens": tokens,
        }).execute()
        total = result.data if result.data else 0
        if isinstance(total, (int, float)):
            if total >= settings.hard_token_limit:
                logger.warning("Tenant %s hit hard token limit (%d)", tenant_id, total)
            elif total >= settings.alert_token_threshold:
                logger.warning("Tenant %s at 80%% token usage (%d)", tenant_id, total)
    except Exception as e:
        logger.error("Token tracking failed for %s: %s", tenant_id, e)
