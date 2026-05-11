"""
Seed script — Inserts demo data for testing.
Uses a realistic Café Aruba dataset (coffee distributor).

Usage:
    cd backend
    python -m scripts.seed_demo_data

Or from project root:
    PYTHONPATH=backend python scripts/seed_demo_data.py
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in backend/.env")
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_KEY)

# ═══════════════════════════════════════════════
# TENANT: Café Aruba (coffee distributor)
# ═══════════════════════════════════════════════

TENANT_ID = "00000000-0000-0000-0000-000000000001"

print("🔧 Creating tenant: Café Aruba...")
db.table("tenants").upsert({
    "id": TENANT_ID,
    "name": "Café Aruba",
    "plan": "pro",
    "currency": "ARS",
    "timezone": "America/Argentina/Buenos_Aires",
    "spreadsheet_ids": [],
    "config": {
        "sheets_enabled": False,  # D3: web-first, no Sheets sync
        "industry": "gastronomia",
        "employees": 12,
        "alert_thresholds": {
            "saldo_minimo": 500000,
            "factura_vencida_dias": 15,
            "desvio_gasto_pct": 120,
        },
    },
}).execute()

# ═══════════════════════════════════════════════
# TRANSACTIONS — 4 months of realistic data
# ═══════════════════════════════════════════════

print("📊 Generating transactions...")

# Income categories with typical amounts for a coffee distributor
INGRESOS = [
    {"cat": "Ventas mayoristas", "descs": [
        "Venta a Restaurante El Gaucho", "Venta a Hotel Palermo",
        "Venta a Café Central", "Venta a Panadería La Estrella",
        "Venta a Oficinas Corp BA", "Venta a Bar Rivadavia",
        "Venta a Hotel Costa Sur", "Venta a Catering Premium",
    ], "min": 80000, "max": 450000},
    {"cat": "Ventas minoristas", "descs": [
        "Venta mostrador", "Pedido online", "Venta ferias",
        "Venta Instagram", "Pedido WhatsApp",
    ], "min": 15000, "max": 95000},
    {"cat": "Ventas e-commerce", "descs": [
        "MercadoLibre pedido", "Tienda web pedido",
        "Pedido Rappi", "Pedido PedidosYa",
    ], "min": 25000, "max": 120000},
    {"cat": "Servicios", "descs": [
        "Capacitación baristas Hotel X", "Consultoría blend custom",
        "Evento degustación corporativa",
    ], "min": 50000, "max": 200000},
]

GASTOS = [
    {"cat": "Materia prima", "descs": [
        "Compra café verde Brasil", "Compra café Colombia",
        "Importación blend especial", "Proveedor insumos packaging",
    ], "min": 150000, "max": 600000},
    {"cat": "Logística", "descs": [
        "Flete entregas CABA", "Envíos interior",
        "LogísticaExpress mensual", "Combustible camioneta",
    ], "min": 30000, "max": 120000},
    {"cat": "Sueldos", "descs": [
        "Sueldos equipo producción", "Sueldos administración",
        "Sueldo vendedor senior",
    ], "min": 200000, "max": 500000},
    {"cat": "Alquiler", "descs": [
        "Alquiler depósito Barracas", "Alquiler oficina",
    ], "min": 180000, "max": 350000},
    {"cat": "Marketing", "descs": [
        "Publicidad Instagram", "Diseño packaging nuevo",
        "Stand feria gastronómica", "Influencer campaña",
    ], "min": 20000, "max": 100000},
    {"cat": "Servicios", "descs": [
        "Contador mensual", "Internet y telefonía",
        "Software gestión", "Seguro mercadería",
    ], "min": 15000, "max": 60000},
]

transactions = []
now = datetime.utcnow()
start_date = now - timedelta(days=120)  # ~4 months back

day = start_date
ref_counter = 1000

while day <= now:
    # Skip some weekends
    if day.weekday() >= 5 and random.random() < 0.6:
        day += timedelta(days=1)
        continue

    # 1-4 income transactions per day
    for _ in range(random.randint(1, 4)):
        cat_info = random.choice(INGRESOS)
        amount = round(random.uniform(cat_info["min"], cat_info["max"]), 0)
        desc = random.choice(cat_info["descs"])
        ref_counter += 1

        # Most are cobrado, some pendiente
        status = "cobrado" if random.random() < 0.75 else "pendiente"

        transactions.append({
            "tenant_id": TENANT_ID,
            "date": day.replace(
                hour=random.randint(8, 18),
                minute=random.randint(0, 59),
            ).isoformat(),
            "amount": amount,
            "type": "ingreso",
            "category": cat_info["cat"],
            "description": desc,
            "status": status,
            "reference": "FA-{}".format(ref_counter),
        })

    # 0-2 expense transactions per day
    for _ in range(random.randint(0, 2)):
        cat_info = random.choice(GASTOS)
        amount = round(random.uniform(cat_info["min"], cat_info["max"]), 0)
        desc = random.choice(cat_info["descs"])
        ref_counter += 1

        transactions.append({
            "tenant_id": TENANT_ID,
            "date": day.replace(
                hour=random.randint(8, 18),
                minute=random.randint(0, 59),
            ).isoformat(),
            "amount": amount,
            "type": "gasto",
            "category": cat_info["cat"],
            "description": desc,
            "status": "pagado",
            "reference": "OC-{}".format(ref_counter),
        })

    day += timedelta(days=1)

# Insert in batches
BATCH = 50
print("  Inserting {} transactions in batches of {}...".format(len(transactions), BATCH))
for i in range(0, len(transactions), BATCH):
    batch = transactions[i:i + BATCH]
    db.table("transactions").upsert(batch, on_conflict="tenant_id,date,description").execute()
    print("  ... batch {}/{}".format(i // BATCH + 1, (len(transactions) // BATCH) + 1))

# ═══════════════════════════════════════════════
# ALERTS
# ═══════════════════════════════════════════════

print("🔔 Creating alerts...")
alerts = [
    {
        "tenant_id": TENANT_ID,
        "severity": "critica",
        "title": "Factura vencida — Restaurante El Gaucho",
        "body": "La factura FA-1089 por $280.000 venció hace 14 días sin registro de pago. Este cliente tiene historial de pagos a tiempo. Sugerimos contacto directo.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "critica",
        "title": "Saldo operativo por debajo del mínimo",
        "body": "El saldo en cuenta cayó a $892.400, un 8.2% menos que la semana pasada. Con los gastos proyectados para los próximos 10 días, el margen de seguridad es ajustado.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "advertencia",
        "title": "Gasto en logística subió 15% este mes",
        "body": "LogísticaExpress facturó $98.000 vs $85.000 del mes anterior. Sin justificación documentada.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "advertencia",
        "title": "3 facturas vencen esta semana",
        "body": "Hotel Palermo ($145.000), Café Central ($67.000) y Oficinas Corp BA ($210.000) vencen entre el 24 y 28 de marzo.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "advertencia",
        "title": "Compra de materia prima inusualmente alta",
        "body": "La importación de blend especial por $580.000 excede en un 40% la compra habitual. Verificar si fue intencional.",
        "status": "activa",
    },
]

for alert in alerts:
    db.table("alerts").insert(alert).execute()

# ═══════════════════════════════════════════════
# SYNC LOG (simulated)
# ═══════════════════════════════════════════════

print("📋 Creating sync log...")
db.table("sync_log").insert({
    "tenant_id": TENANT_ID,
    "rows_processed": len(transactions),
    "rows_new": len(transactions),
    "rows_updated": 0,
    "errors": [],
    "completed_at": now.isoformat(),
}).execute()

# ═══════════════════════════════════════════════
# PRODUCTS + STOCK (showroom demo)
# ═══════════════════════════════════════════════

print("👗 Creating demo products...")

PRODUCTS = [
    {"name": "Remera manga corta",  "sku": "RMC-001", "unit_price": 8500,  "min_threshold": 5},
    {"name": "Jean skinny azul",    "sku": "JSK-001", "unit_price": 22000, "min_threshold": 3},
    {"name": "Vestido floral",      "sku": "VFL-001", "unit_price": 18000, "min_threshold": 3},
    {"name": "Buzo canguro",        "sku": "BUZ-001", "unit_price": 15000, "min_threshold": 4},
    {"name": "Campera de abrigo",   "sku": "CAM-001", "unit_price": 35000, "min_threshold": 2},
]

product_ids = {}
for p in PRODUCTS:
    p["tenant_id"] = TENANT_ID
    res = db.table("products").upsert(p, on_conflict="tenant_id,sku").execute()
    if res.data:
        product_ids[p["sku"]] = res.data[0]["id"]
        print("  ✅ {}".format(p["name"]))

# Stock movements: initial entrada + some ventas
movements = []
for sku, pid in product_ids.items():
    movements.append({
        "tenant_id": TENANT_ID, "product_id": pid,
        "type": "entrada", "quantity": random.randint(15, 30),
        "note": "Stock inicial",
        "date": (now - timedelta(days=60)).isoformat(),
    })
    for _ in range(random.randint(3, 8)):
        movements.append({
            "tenant_id": TENANT_ID, "product_id": pid,
            "type": "venta", "quantity": random.randint(1, 3),
            "note": "venta",
            "date": (now - timedelta(days=random.randint(1, 30))).isoformat(),
        })

for m in movements:
    db.table("stock_movements").insert(m).execute()
print("  ✅ {} movimientos de stock".format(len(movements)))

print("")
print("✅ Seed complete!")
print("   Tenant: Café Aruba (ID: {})".format(TENANT_ID))
print("   Transactions: {}".format(len(transactions)))
print("   Alerts: {}".format(len(alerts)))
print("")
print("🚀 Start the backend with:")
print("   cd backend && uvicorn app.main:app --reload --port 8000")
print("")
print("📊 Test the dashboard:")
print("   curl http://localhost:8000/api/v1/dashboard/{}".format(TENANT_ID))
