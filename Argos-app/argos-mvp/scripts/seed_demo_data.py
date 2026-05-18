"""
Seed script — La Percha (tienda de ropa femenina y masculina).
Genera datos realistas para demo: stock, ventas, gastos, cobranzas pendientes.

Usage:
    cd argos-mvp
    PYTHONPATH=backend python scripts/seed_demo_data.py
"""

import os
import sys
import random
from datetime import datetime, timedelta

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

TENANT_ID = "00000000-0000-0000-0000-000000000001"

# ═══════════════════════════════════════════════
# LIMPIAR DATOS ANTERIORES
# ═══════════════════════════════════════════════

print("🧹 Limpiando datos anteriores del tenant...")
db.table("stock_movements").delete().eq("tenant_id", TENANT_ID).execute()
db.table("transactions").delete().eq("tenant_id", TENANT_ID).execute()
db.table("products").delete().eq("tenant_id", TENANT_ID).execute()
db.table("alerts").delete().eq("tenant_id", TENANT_ID).execute()
db.table("chat_messages").delete().eq("tenant_id", TENANT_ID).execute()
db.table("sync_log").delete().eq("tenant_id", TENANT_ID).execute()
print("  ✅ Datos anteriores eliminados")

# ═══════════════════════════════════════════════
# TENANT: La Percha (tienda de ropa)
# ═══════════════════════════════════════════════

print("🏪 Creando tenant: La Percha...")
db.table("tenants").upsert({
    "id": TENANT_ID,
    "name": "La Percha",
    "plan": "pro",
    "currency": "ARS",
    "timezone": "America/Argentina/Buenos_Aires",
    "spreadsheet_ids": [],
    "config": {
        "sheets_enabled": False,
        "industry": "retail_ropa",
        "employees": 5,
        "alert_thresholds": {
            "saldo_minimo": 300000,
            "factura_vencida_dias": 15,
            "desvio_gasto_pct": 120,
        },
    },
}).execute()

# ═══════════════════════════════════════════════
# PRODUCTS (10 prendas reales)
# ═══════════════════════════════════════════════

print("👗 Creando productos...")

PRODUCTS = [
    {"name": "Jean slim mujer",      "sku": "JEA-F01", "unit_price": 28000, "min_threshold": 5},
    {"name": "Jean wide leg",         "sku": "JEA-F02", "unit_price": 32000, "min_threshold": 4},
    {"name": "Remera oversize",       "sku": "REM-U01", "unit_price": 12500, "min_threshold": 8},
    {"name": "Camisa de lino",        "sku": "CAM-U01", "unit_price": 18000, "min_threshold": 5},
    {"name": "Vestido midi floral",   "sku": "VES-F01", "unit_price": 35000, "min_threshold": 3},
    {"name": "Short de jean",         "sku": "SHO-U01", "unit_price": 19500, "min_threshold": 5},
    {"name": "Buzo canguro",          "sku": "BUZ-U01", "unit_price": 24000, "min_threshold": 4},
    {"name": "Campera de cuero eco",  "sku": "CAM-U02", "unit_price": 89000, "min_threshold": 2},
    {"name": "Calza deportiva",       "sku": "CAL-F01", "unit_price": 14500, "min_threshold": 6},
    {"name": "Musculosa elastizada",  "sku": "MUS-F01", "unit_price": 9500,  "min_threshold": 8},
]

product_ids = {}
for p in PRODUCTS:
    data = {**p, "tenant_id": TENANT_ID}
    res = db.table("products").upsert(data, on_conflict="tenant_id,sku").execute()
    if res.data:
        product_ids[p["sku"]] = res.data[0]["id"]
        print("  ✅ {} (${:,})".format(p["name"], p["unit_price"]))

# ═══════════════════════════════════════════════
# STOCK MOVEMENTS
# Stock inicial + ventas simuladas
# Algunos productos quedan con stock bajo (para ver alertas)
# ═══════════════════════════════════════════════

print("📦 Generando movimientos de stock...")

now = datetime.utcnow()

# Stock inicial por producto (hace 60 días)
STOCK_INICIAL = {
    "JEA-F01": 22, "JEA-F02": 18, "REM-U01": 35, "CAM-U01": 20, "VES-F01": 14,
    "SHO-U01": 25, "BUZ-U01": 20, "CAM-U02": 8,  "CAL-F01": 30, "MUS-F01": 40,
}

# Ventas por producto (hace que algunos queden bajos de stock)
VENTAS_STOCK = {
    "JEA-F01": 20,  # queda 2 — stock CRÍTICO (bajo min_threshold=5)
    "JEA-F02": 5,   # queda 13
    "REM-U01": 28,  # queda 7 — ok
    "CAM-U01": 18,  # queda 2 — CRÍTICO (bajo min_threshold=5)
    "VES-F01": 12,  # queda 2 — CRÍTICO (bajo min_threshold=3)
    "SHO-U01": 8,   # queda 17
    "BUZ-U01": 17,  # queda 3 — ADVERTENCIA (cerca del min_threshold=4)
    "CAM-U02": 1,   # queda 7
    "CAL-F01": 24,  # queda 6 — ok (min_threshold=6, justo al límite)
    "MUS-F01": 32,  # queda 8 — ok
}

movements = []
for sku, pid in product_ids.items():
    # Entrada inicial
    movements.append({
        "tenant_id": TENANT_ID, "product_id": pid,
        "type": "entrada", "quantity": STOCK_INICIAL[sku],
        "note": "Stock inicial temporada",
        "date": (now - timedelta(days=60)).isoformat(),
    })
    # Reposición a mitad de temporada en algunos
    if sku in ["REM-U01", "MUS-F01", "CAL-F01"]:
        movements.append({
            "tenant_id": TENANT_ID, "product_id": pid,
            "type": "entrada", "quantity": random.randint(10, 20),
            "note": "Reposición proveedor",
            "date": (now - timedelta(days=30)).isoformat(),
        })
    # Ventas históricas
    sold = VENTAS_STOCK[sku]
    ventas_realizadas = 0
    while ventas_realizadas < sold:
        qty = min(random.randint(1, 3), sold - ventas_realizadas)
        movements.append({
            "tenant_id": TENANT_ID, "product_id": pid,
            "type": "venta", "quantity": qty,
            "note": "venta",
            "date": (now - timedelta(days=random.randint(1, 55))).isoformat(),
        })
        ventas_realizadas += qty

for m in movements:
    db.table("stock_movements").insert(m).execute()
print("  ✅ {} movimientos de stock".format(len(movements)))

# ═══════════════════════════════════════════════
# TRANSACTIONS — 4 meses de datos reales de tienda de ropa
# ═══════════════════════════════════════════════

print("📊 Generando transacciones (4 meses)...")

INGRESOS = [
    {"cat": "Ventas mostrador", "descs": [
        "Venta jean slim + remera", "Venta vestido midi", "Venta campera cuero",
        "Venta buzo + calza", "Venta pack 3 remeras", "Venta short + musculosa",
        "Venta jean wide leg", "Venta camisa de lino", "Venta conjunto deportivo",
        "Venta ropa verano cliente habitual", "Cobro por devolución de cambio",
        "Venta outlet fines de semana",
    ], "min": 12000, "max": 95000},
    {"cat": "Ventas online", "descs": [
        "Pedido MercadoLibre", "Pedido TiendaNube", "Pedido Instagram DM",
        "Pedido WhatsApp envío interior", "Pedido web + envío",
        "Venta pack ropa online", "Pedido MercadoShops",
    ], "min": 15000, "max": 75000},
    {"cat": "Ventas mayoristas", "descs": [
        "Pedido mayorista Boutique Norte", "Pedido Tienda Once",
        "Venta a revendedora zona sur", "Pedido mayorista Rosario",
        "Venta lote jeans revendedora", "Pedido mayorista CABA",
        "Venta temporada a multimarca",
    ], "min": 80000, "max": 400000},
]

GASTOS = [
    {"cat": "Proveedores", "descs": [
        "Compra jeans proveedor La Salada", "Compra remeras por mayor",
        "Importación camperas cuero eco", "Compra vestidos temporada",
        "Proveedor calzas deportivas", "Compra shorts y musculosas",
        "Colección nueva proveedor Flores", "Compra telas confección propia",
    ], "min": 80000, "max": 600000},
    {"cat": "Alquiler", "descs": [
        "Alquiler local comercial", "Expensas local",
    ], "min": 250000, "max": 350000},
    {"cat": "Sueldos", "descs": [
        "Sueldos empleadas mes", "Sueldo encargada tienda",
        "Horas extra temporada alta",
    ], "min": 300000, "max": 500000},
    {"cat": "Marketing", "descs": [
        "Publicidad Meta Ads", "Sesión de fotos producto",
        "Contenido Instagram reels", "Influencer colaboración",
        "Mantenimiento TiendaNube", "Diseño catálogo temporada",
    ], "min": 15000, "max": 90000},
    {"cat": "Servicios", "descs": [
        "Contador mensual", "Internet local", "Luz y gas",
        "Bolsas y packaging", "Percheros y exhibidores", "Sistema de gestión",
    ], "min": 8000, "max": 45000},
    {"cat": "Impuestos", "descs": [
        "Monotributo", "Ingresos brutos mensual", "Tasa municipal",
    ], "min": 30000, "max": 80000},
]

transactions = []
start_date = now - timedelta(days=120)
day = start_date
ref_counter = 2000

# Mayoristas con facturas pendientes (nombres fijos para coherencia)
MAYORISTAS_PENDIENTES = [
    ("Boutique Norte", "FA-2087", 185000),
    ("Tienda Once", "FA-2091", 230000),
    ("Multimarca Rosario", "FA-2103", 142000),
]

while day <= now:
    # Domingos cerrado
    if day.weekday() == 6:
        day += timedelta(days=1)
        continue
    # Sábados baja actividad
    if day.weekday() == 5 and random.random() < 0.3:
        day += timedelta(days=1)
        continue

    # 2-6 ventas por día (tienda de ropa tiene flujo constante)
    n_ventas = random.randint(2, 6)
    for _ in range(n_ventas):
        # 70% mostrador, 20% online, 10% mayorista
        roll = random.random()
        if roll < 0.70:
            cat_info = INGRESOS[0]  # mostrador
        elif roll < 0.90:
            cat_info = INGRESOS[1]  # online
        else:
            cat_info = INGRESOS[2]  # mayorista

        amount = round(random.uniform(cat_info["min"], cat_info["max"]), 0)
        desc = random.choice(cat_info["descs"])
        ref_counter += 1
        # Mayoristas: 30% pendiente; mostrador/online: 95% cobrado
        if cat_info["cat"] == "Ventas mayoristas":
            status = "cobrado" if random.random() < 0.70 else "pendiente"
        else:
            status = "cobrado" if random.random() < 0.95 else "pendiente"

        transactions.append({
            "tenant_id": TENANT_ID,
            "date": day.replace(hour=random.randint(9, 20), minute=random.randint(0, 59)).isoformat(),
            "amount": amount,
            "type": "ingreso",
            "category": cat_info["cat"],
            "description": desc,
            "status": status,
            "reference": "FA-{}".format(ref_counter),
        })

    # 0-2 gastos por día
    for _ in range(random.randint(0, 2)):
        cat_info = random.choice(GASTOS)
        # Sueldos y alquiler: solo 1 vez por mes
        if cat_info["cat"] in ("Sueldos", "Alquiler", "Impuestos") and day.day != 1:
            continue
        amount = round(random.uniform(cat_info["min"], cat_info["max"]), 0)
        desc = random.choice(cat_info["descs"])
        ref_counter += 1
        transactions.append({
            "tenant_id": TENANT_ID,
            "date": day.replace(hour=random.randint(9, 18), minute=random.randint(0, 59)).isoformat(),
            "amount": amount,
            "type": "gasto",
            "category": cat_info["cat"],
            "description": desc,
            "status": "pagado",
            "reference": "OC-{}".format(ref_counter),
        })

    day += timedelta(days=1)

# Agregar facturas mayoristas VENCIDAS (para que el agente de cobranzas las muestre)
for cliente, referencia, monto in MAYORISTAS_PENDIENTES:
    dias_atras = random.randint(35, 55)  # vencidas hace más de 30 días
    transactions.append({
        "tenant_id": TENANT_ID,
        "date": (now - timedelta(days=dias_atras)).isoformat(),
        "amount": monto,
        "type": "ingreso",
        "category": "Ventas mayoristas",
        "description": "Pedido mayorista {}".format(cliente),
        "status": "pendiente",
        "reference": referencia,
    })

# Insertar en batches
BATCH = 50
print("  Insertando {} transacciones en lotes de {}...".format(len(transactions), BATCH))
for i in range(0, len(transactions), BATCH):
    batch = transactions[i:i + BATCH]
    db.table("transactions").upsert(batch, on_conflict="tenant_id,date,description").execute()
    print("  ... lote {}/{}".format(i // BATCH + 1, (len(transactions) // BATCH) + 1))

# ═══════════════════════════════════════════════
# ALERTAS
# ═══════════════════════════════════════════════

print("🔔 Creando alertas...")
alerts = [
    {
        "tenant_id": TENANT_ID,
        "severity": "critica",
        "title": "Factura vencida — Boutique Norte",
        "body": "La factura FA-2087 por $185.000 venció hace 38 días sin registro de pago. Recomendamos contactar directamente al comprador.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "critica",
        "title": "Stock crítico: Jean slim mujer y Camisa de lino",
        "body": "Quedan 2 unidades de Jean slim mujer (mín. 5) y 2 de Camisa de lino (mín. 5). Con la rotación actual se agotan en menos de 3 días.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "critica",
        "title": "Vestido midi floral — stock agotándose",
        "body": "Solo quedan 2 unidades del Vestido midi floral (mín. 3). Producto con alta rotación en temporada — reabastecer con urgencia.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "advertencia",
        "title": "3 facturas mayoristas sin cobrar (+30 días)",
        "body": "Boutique Norte ($185.000), Tienda Once ($230.000) y Multimarca Rosario ($142.000) tienen facturas vencidas. Total en riesgo: $557.000.",
        "status": "activa",
    },
    {
        "tenant_id": TENANT_ID,
        "severity": "advertencia",
        "title": "Gasto en proveedores sube 18% este mes",
        "body": "La compra de stock este mes fue un 18% mayor al promedio. Revisar si hay margen suficiente para absorber el aumento.",
        "status": "activa",
    },
]

for alert in alerts:
    db.table("alerts").insert(alert).execute()
print("  ✅ {} alertas creadas".format(len(alerts)))

# ═══════════════════════════════════════════════
# SYNC LOG
# ═══════════════════════════════════════════════

db.table("sync_log").insert({
    "tenant_id": TENANT_ID,
    "rows_processed": len(transactions),
    "rows_new": len(transactions),
    "rows_updated": 0,
    "errors": [],
    "completed_at": now.isoformat(),
}).execute()

print("")
print("✅ Seed completo — La Percha")
print("   Transacciones: {}".format(len(transactions)))
print("   Productos: {}".format(len(PRODUCTS)))
print("   Movimientos de stock: {}".format(len(movements)))
print("   Alertas: {}".format(len(alerts)))
print("")
print("   Facturas vencidas para cobranzas:")
for cliente, ref, monto in MAYORISTAS_PENDIENTES:
    print("   · {} {} — ${}".format(ref, cliente, "{:,}".format(monto)))
print("")
print("🚀  Backend: cd backend && uvicorn app.main:app --reload --port 8000")
print("📊  API:     curl http://localhost:8000/api/v1/dashboard/{}".format(TENANT_ID))
