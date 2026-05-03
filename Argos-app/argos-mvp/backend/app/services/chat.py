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

SYSTEM_PROMPT_TEMPLATE = """Sos Argos, el asistente financiero IA de {empresa}.
Tenés acceso a los datos financieros actualizados de la empresa.

DATOS ACTUALES DEL NEGOCIO:
{contexto_financiero}

REGLAS:
- Respondé siempre en español rioplatense, de forma clara y orientada a la acción.
- Usá números concretos de los datos cuando respondas.
- Si detectás algo preocupante, mencionalo proactivamente.
- Si no tenés datos suficientes para responder, decilo honestamente y sugerí qué
  información completar en el Google Sheet.
- Formateá montos con punto como separador de miles (ej: $1.234.567).
- Sé conciso pero completo. Priorizá la información más relevante.
- Cuando hables de tendencias, compará siempre con el período anterior.
- No inventes datos que no tenés. Basate estrictamente en la información proporcionada.
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


async def chat(tenant_id: str, user_message: str, session_id: Optional[str] = None) -> dict:
    """
    Process a chat message from the user.
    Returns the AI response with session tracking.
    """
    settings = get_settings()

    if not session_id:
        session_id = str(uuid.uuid4())

    # Get tenant info
    tenant = db.get_tenant(tenant_id)
    if not tenant:
        return {
            "response": "No encontré datos para esta empresa. Verificá la configuración.",
            "session_id": session_id,
        }

    empresa_name = tenant.get("name", "tu empresa")

    # Build context
    try:
        contexto = _build_financial_context(tenant_id)
    except Exception as e:
        logger.error("Error building context for tenant %s: %s", tenant_id, e)
        contexto = "(No se pudieron cargar los datos financieros en este momento)"

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        empresa=empresa_name,
        contexto_financiero=contexto,
    )

    # Get chat history for continuity
    history = db.get_chat_history(tenant_id, session_id, limit=10)
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    # Save user message
    db.save_chat_message(tenant_id, session_id, "user", user_message)

    # Call Claude API
    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        ai_response = response.content[0].text
    except anthropic.APITimeoutError:
        logger.error("Claude API timeout for tenant %s", tenant_id)
        ai_response = "Disculpá, tardé demasiado en procesar tu consulta. ¿Podés intentar de nuevo?"
    except Exception as e:
        logger.error("Claude API error for tenant %s: %s", tenant_id, e)
        ai_response = "Hubo un error al procesar tu consulta. Por favor intentá de nuevo en unos segundos."

    # Save assistant message
    db.save_chat_message(tenant_id, session_id, "assistant", ai_response)

    return {
        "response": ai_response,
        "session_id": session_id,
    }
