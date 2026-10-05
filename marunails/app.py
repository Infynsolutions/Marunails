from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from datetime import datetime, date, timedelta, timezone
from collections import defaultdict
from zoneinfo import ZoneInfo
import os
import re
import hmac
import hashlib
import base64
import httpx
import anthropic as _anthropic

from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Sin valores por defecto: el repo es público. Sin SECRET_KEY la sesión usa una clave al azar
# (no se puede falsificar, pero no sobrevive entre instancias): en Vercel tiene que estar cargada.
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(32)
# Las chicas del equipo quedan logueadas 30 días en su celular
app.permanent_session_lifetime = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://dbhxrboacqppximbcokz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')  # anon: solo para correr local sin service key

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')   # sin cargar = nadie entra como admin

TC_USD = 17

# ── Seña de reserva (Mercado Pago Checkout Pro) ──
# Sin MP_ACCESS_TOKEN la reserva web funciona como antes (sin seña).
# Production usa MP_ACCESS_TOKEN_PROD (token de producción); Preview, MP_ACCESS_TOKEN (de prueba)
MP_ACCESS_TOKEN     = os.environ.get('MP_ACCESS_TOKEN_PROD') or os.environ.get('MP_ACCESS_TOKEN', '')
MP_WEBHOOK_SECRET   = os.environ.get('MP_WEBHOOK_SECRET', '')
PUBLIC_BASE_URL     = os.environ.get('BASE_URL_MP', 'https://www.marunailstulum.com').rstrip('/')
MP_NOTIFICATION_URL = os.environ.get('MP_NOTIFICATION_URL', f'{PUBLIC_BASE_URL}/api/mp/webhook')
SENA_MXN            = int(os.environ.get('SENA_MXN', '200'))
# Service key (secreta, solo backend): pagos_sena tiene RLS sin políticas, la key anon no la ve
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
SENA_ACTIVA         = bool(MP_ACCESS_TOKEN and SUPABASE_SERVICE_KEY)
# Cuánto tiempo queda retenido el horario esperando la seña, según de dónde vino la cita.
# El link de MP vence MP_MARGEN_MIN antes, para que llegue el webhook.
HOLD_MIN_POR_CANAL  = {'web': 20, 'recepcion': 120}
MP_MARGEN_MIN       = 5
TZ_SALON            = ZoneInfo('America/Cancun')

# Estados de turno que NO ocupan el horario
ESTADOS_LIBERAN = {'cancelado_cliente', 'cancelado_salon', 'no_show', 'reprogramado'}

STAFF = [
    {'nombre': 'FLOR',            'comision': 0.4},
    {'nombre': 'FANNY',           'comision': 0.4},
    {'nombre': 'GABY',            'comision': 0.4},
    {'nombre': 'MARU',            'comision': 0.4},
    {'nombre': 'KAREN RECEPCION', 'comision': 0.3},
    {'nombre': 'KAREN',           'comision': 0.4},
    {'nombre': 'MILI',            'comision': 0.3},
    {'nombre': 'BELU',            'comision': 0.6},
]

SERVICIOS = [
    'Manos Gel', 'Pies Gel', 'Esculpidas', 'Lifting', 'Laminado',
    'Perfilado', 'Facial', 'Extension pestañas', 'Manicura Spa',
    'Kapping Gel', 'Extras', 'Acrilicas Esculpidas', 'Services Esculpidas',
    'Pedicure Spa', 'Depilacion rostro', 'Seña',
]

MEDIOS_PAGO = ['Efectivo', 'Tarjeta', 'Transferencia', 'USD cash', 'Otro']

CAPACIDAD_ESTACIONES = {
    'manicura': 2,
    'pedicura': 2,
    'estetica': 1,
}

CATEGORIA_A_ESTACION = {
    'Manicure':       'manicura',
    'Pedicure':       'pedicura',
    'Glow Up Facial': 'estetica',
    'Brows & Lashes': 'estetica',
    'Additional':     'manicura',
}


def estacion_de_categoria(categoria):
    return CATEGORIA_A_ESTACION.get(categoria)

CATEGORIAS_GASTO = [
    'Productos', 'Renta', 'Servicios', 'Sueldos/Comisiones', 'Marketing',
    'Impuestos', 'Otros', 'Gastos Operativos', 'Retiros -Mariana',
    'Inversiones nuevas', 'Prestamos',
]

MESES_ES = {
    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
    7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic',
}


def es_admin():
    return bool(session.get('admin_logged_in'))


def equipo_valido():
    """Sesión de una chica del equipo. Se revalida contra equipo_acceso en cada request:
    si la admin le quitó el acceso (o la desactivó) la sesión deja de valer."""
    cid = session.get('equipo_id')
    if not cid:
        return False
    try:
        fila = sb_service().table('equipo_acceso').select('updated_at').eq(
            'colaboradora_id', cid).limit(1).execute().data
    except Exception:
        return False
    if not fila or fila[0]['updated_at'] != session.get('equipo_ver'):
        session.clear()
        return False
    return True


def _sin_permiso(destino):
    if request.path.startswith('/api/') or request.path.startswith('/admin/api/'):
        return jsonify({'error': 'Sin permiso. Volvé a iniciar sesión.'}), 401 if destino == 'login' else 403
    return redirect(url_for(destino))


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not es_admin():
            # Una chica del equipo que entra a una página del sistema vuelve a la agenda
            return _sin_permiso('agenda' if session.get('equipo_id') else 'login')
        return f(*args, **kwargs)
    return decorated


def require_equipo(f):
    """Admin o una chica del equipo con sesión válida."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not (es_admin() or equipo_valido()):
            return _sin_permiso('login')
        return f(*args, **kwargs)
    return decorated


def autor_actual():
    """(nombre, colaboradora_id) de quien hace el cambio, para turno_cambios."""
    if es_admin():
        return 'Admin', None
    return session.get('equipo_nombre') or 'Equipo', session.get('equipo_id')


def get_sb():
    """Todas las tablas tienen RLS cerrado a la key anon (migración 006): el server lee y
    escribe con la service key. La anon queda solo para desarrollo local."""
    if SUPABASE_SERVICE_KEY:
        return sb_service()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


_sb_admin = None


def sb_service():
    """Cliente con la service key (bypassea RLS)."""
    global _sb_admin
    if _sb_admin is None:
        _sb_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _sb_admin


def tabla_pagos():
    """pagos_sena solo se toca desde el server con la service key (bypassea RLS)."""
    return sb_service().table('pagos_sena')


def ahora_salon():
    """Hora local de Tulum, naive (el server de Vercel corre en UTC)."""
    return datetime.now(TZ_SALON).replace(tzinfo=None)


def _parse_ts(s):
    """Timestamptz de PostgREST → datetime aware (tolera fracciones de 1-6 dígitos)."""
    s  = re.sub(r'\.\d+', '', s.replace('Z', '+00:00'))
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def hold_min(canal):
    return HOLD_MIN_POR_CANAL.get(canal or 'web', HOLD_MIN_POR_CANAL['web'])


def hold_vencido(t):
    """Cita que esperaba la seña y no se pagó a tiempo (el plazo depende del canal)."""
    return (t.get('estado') == 'esperando_pago' and bool(t.get('created_at'))
            and _parse_ts(t['created_at']) < datetime.now(timezone.utc) - timedelta(minutes=hold_min(t.get('canal'))))


def url_pago(token):
    return f'{PUBLIC_BASE_URL}/pagar/{token}'


def turno_ocupa(t):
    """¿Este turno bloquea el horario de la colaboradora / estación?"""
    return t.get('estado') not in ESTADOS_LIBERAN and not hold_vencido(t)


def mp_request(method, path, json=None, idempotency_key=None):
    headers = {'Authorization': f'Bearer {MP_ACCESS_TOKEN}'}
    if idempotency_key:
        headers['X-Idempotency-Key'] = idempotency_key
    r = httpx.request(method, f'https://api.mercadopago.com{path}',
                      json=json, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()


def format_fecha(d):
    return f"{d.day:02d}-{MESES_ES[d.month]}-{d.year}"


def get_week_quincena(d):
    semana = d.isocalendar()[1]
    mes    = d.strftime('%Y-%m')
    q      = 'Q1' if d.day <= 15 else 'Q2'
    return semana, mes, f'{mes}-{q}'


def fetch_all(sb, tabla, columnas):
    """Trae TODAS las filas de una tabla paginando de a 1000
    (PostgREST devuelve máximo 1000 por request)."""
    filas = []
    start = 0
    while True:
        chunk = sb.table(tabla).select(columnas).range(start, start + 999).execute().data
        filas += chunk
        if len(chunk) < 1000:
            break
        start += 1000
    return filas


def rango_meses_cortes(sb):
    """(primer_mes, ultimo_mes) con data. Usa min/max por fecha para no chocar
    con el tope de 1000 filas de PostgREST."""
    primero = sb.table('cortes').select('mes').order('fecha').limit(1).execute().data
    ultimo  = sb.table('cortes').select('mes').order('fecha', desc=True).limit(1).execute().data
    return (primero[0]['mes'] if primero else None,
            ultimo[0]['mes']  if ultimo  else None)


def lista_meses(primer_mes, mes_fin):
    """Rango continuo de 'YYYY-MM' desde primer_mes hasta mes_fin, descendente."""
    if not primer_mes:
        return []
    y, m   = (int(x) for x in primer_mes.split('-'))
    fy, fm = (int(x) for x in mes_fin.split('-'))
    out = []
    while (y, m) <= (fy, fm):
        out.append(f'{y:04d}-{m:02d}')
        m += 1
        if m > 12:
            m, y = 1, y + 1
    out.reverse()
    return out


def corte_row_from_form(form):
    """Construye la fila de un corte desde el form. Devuelve None si falta algo obligatorio."""
    fecha_str     = form.get('fecha')
    cliente       = form.get('cliente', '').strip() or 'Walk in'
    staff_nombre  = form.get('staff')
    servicio      = form.get('servicio')
    moneda        = form.get('moneda', 'MXN')
    total_cobrado = float(form.get('total_cobrado') or 0)
    propina       = float(form.get('propina') or 0)
    medio_pago    = form.get('medio_pago')
    notas         = form.get('notas', '').strip()

    color = form.get('color', '').strip()

    if not fecha_str or not staff_nombre or not servicio or not medio_pago or total_cobrado <= 0:
        return None

    d          = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    tc         = TC_USD if moneda == 'USD' else 1
    venta_neta = total_cobrado - propina
    semana, mes, quincena = get_week_quincena(d)

    return {
        'fecha':         fecha_str,
        'cliente':       cliente,
        'staff':         staff_nombre,
        'servicio':      servicio,
        'moneda':        moneda,
        'total_cobrado': total_cobrado,
        'propina':       propina if propina else 0,
        'medio_pago':    medio_pago,
        'notas':         notas,
        'color':         color or None,
        'venta_neta':    round(venta_neta, 2),
        'tc':            tc,
        'total_mxn':     round(total_cobrado * tc, 2),
        'propina_mxn':   round(propina * tc, 2),
        'neto_mxn':      round(venta_neta * tc, 2),
        'mes':           mes,
        'semana':        semana,
        'quincena':      quincena,
    }


def gasto_row_from_form(form):
    """Construye la fila de un gasto desde el form. Devuelve None si falta algo obligatorio."""
    fecha_str    = form.get('fecha')
    categoria    = form.get('categoria')
    subcategoria = form.get('subcategoria', '').strip()
    proveedor    = form.get('proveedor', '').strip()
    descripcion  = form.get('descripcion', '').strip()
    moneda       = form.get('moneda', 'MXN')
    importe      = float(form.get('importe') or 0)
    medio_pago   = form.get('medio_pago')
    notas        = form.get('notas', '').strip()

    if not fecha_str or not categoria or not medio_pago or importe == 0:
        return None

    d   = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    tc  = TC_USD if moneda == 'USD' else 1
    semana, mes, quincena = get_week_quincena(d)

    return {
        'fecha':        fecha_str,
        'categoria':    categoria,
        'subcategoria': subcategoria,
        'proveedor':    proveedor,
        'descripcion':  descripcion,
        'moneda':       moneda,
        'importe':      importe,
        'medio_pago':   medio_pago,
        'notas':        notas,
        'tc':           tc,
        'importe_mxn':  round(importe * tc, 2),
        'mes':          mes,
        'semana':       semana,
        'quincena':     quincena,
    }


# ── AGREGACIÓN DE REPORTES ──────────────────────────────────────────────────────
def _num(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def resumen_cortes(cortes):
    """Calcula métricas de ventas/equipo/servicios sobre una lista de cortes."""
    facturacion = 0.0
    propinas    = 0.0
    n           = 0
    por_medio   = defaultdict(float)
    por_dia     = defaultdict(float)
    staff       = defaultdict(lambda: {'facturacion': 0.0, 'clientas': 0, 'propinas': 0.0})
    servicios   = defaultdict(lambda: {'cantidad': 0, 'facturacion': 0.0})

    for c in cortes:
        total   = _num(c.get('total_mxn'))
        propina = _num(c.get('propina_mxn'))
        medio   = c.get('medio_pago') or 'Otro'
        nombre  = (c.get('staff') or '—').strip()
        serv    = (c.get('servicio') or '—').strip()
        fecha   = c.get('fecha') or ''

        facturacion += total
        propinas    += propina
        n           += 1
        por_medio[medio] += total
        por_dia[fecha]   += total

        staff[nombre]['facturacion'] += total
        staff[nombre]['clientas']    += 1
        staff[nombre]['propinas']    += propina

        servicios[serv]['cantidad']    += 1
        servicios[serv]['facturacion'] += total

    ticket = facturacion / n if n else 0.0

    staff_list = sorted(
        ({'nombre': k,
          'ticket':       (v['facturacion'] / v['clientas'] if v['clientas'] else 0),
          'comision_pct': COMISIONES_PCT.get(k, 0),
          'comision_mxn': round(v['facturacion'] * COMISIONES_PCT.get(k, 0)),
          **v}
         for k, v in staff.items()),
        key=lambda x: x['facturacion'], reverse=True)

    serv_list = sorted(
        ({'nombre': k, **v} for k, v in servicios.items()),
        key=lambda x: x['cantidad'], reverse=True)

    dias = sorted(({'fecha': k, 'total': v} for k, v in por_dia.items()),
                  key=lambda x: x['fecha'])

    return {
        'facturacion': facturacion,
        'propinas':    propinas,
        'n':           n,
        'ticket':      ticket,
        'por_medio':   dict(por_medio),
        'staff':       staff_list,
        'servicios':   serv_list,
        'dias':        dias,
    }


# ── AGREGACIÓN DE CLIENTES ──────────────────────────────────────────────────────
DIAS_RIESGO  = 45   # sin volver hace más de X días => "en riesgo"
DIAS_PERDIDA = 90   # sin volver hace más de X días => "perdida"
VISITAS_VIP  = 6    # visitas para considerar cliente VIP

COMISIONES_PCT = {s['nombre']: s['comision'] for s in STAFF}

app.jinja_env.globals['DIAS_RIESGO']  = DIAS_RIESGO
app.jinja_env.globals['DIAS_PERDIDA'] = DIAS_PERDIDA
app.jinja_env.globals['VISITAS_VIP']  = VISITAS_VIP
app.jinja_env.filters['abs'] = abs


def cliente_key(nombre):
    """Clave normalizada para agrupar (minúsculas + espacios colapsados).
    Fusiona 'Ingrid' con 'ingrid'."""
    return ' '.join((nombre or '').strip().lower().split())


def es_walkin(key):
    return key.startswith('walk') or key == '' or key == 'sin asignar'


def _dias_entre(f1, f2):
    """Días entre dos fechas 'YYYY-MM-DD' (f2 - f1)."""
    try:
        d1 = datetime.strptime(f1, '%Y-%m-%d').date()
        d2 = datetime.strptime(f2, '%Y-%m-%d').date()
        return (d2 - d1).days
    except (TypeError, ValueError):
        return None


def _finalizar_cliente(d, ref_date):
    """Calcula métricas derivadas de un cliente ya acumulado."""
    # Nombre a mostrar: la grafía original más frecuente, en Title Case
    display = max(d['nombres'].items(), key=lambda x: x[1])[0]
    d['nombre'] = display.title() if display else display
    d['ticket'] = d['total'] / d['visitas'] if d['visitas'] else 0
    d['servicio_fav'] = (max(d['servicios'].items(), key=lambda x: x[1])[0]
                         if d['servicios'] else '—')
    d['staff_fav'] = (max(d['staff'].items(), key=lambda x: x[1])[0]
                      if d['staff'] else '—')

    # Recencia y frecuencia
    d['dias_ultima'] = _dias_entre(d['ultima'], ref_date) if d['ultima'] else None
    if d['visitas'] >= 2 and d['primera'] and d['ultima']:
        span = _dias_entre(d['primera'], d['ultima'])
        d['frecuencia'] = round(span / (d['visitas'] - 1)) if span else 0
    else:
        d['frecuencia'] = None

    # Clasificación
    d['walkin'] = es_walkin(d['key'])
    if d['visitas'] == 1:
        d['categoria'] = 'nuevo'
    elif d['visitas'] >= VISITAS_VIP:
        d['categoria'] = 'vip'
    else:
        d['categoria'] = 'recurrente'
    d['en_riesgo'] = (d['visitas'] >= 2 and d['dias_ultima'] is not None
                      and d['dias_ultima'] > DIAS_RIESGO)

    # limpiar estructuras internas
    d.pop('nombres', None)
    d.pop('servicios', None)
    d.pop('staff', None)
    return d


def agregar_clientes(cortes, ref_date):
    """Agrupa una lista de cortes por cliente y devuelve dicts con métricas."""
    cli = {}
    for c in cortes:
        raw = (c.get('cliente') or '').strip()
        key = cliente_key(raw)
        if not key:
            continue
        d = cli.get(key)
        if d is None:
            d = cli[key] = {
                'key': key, 'nombres': defaultdict(int),
                'visitas': 0, 'total': 0.0, 'propinas': 0.0,
                'primera': None, 'ultima': None,
                'servicios': defaultdict(int), 'staff': defaultdict(int),
            }
        d['nombres'][raw] += 1
        d['visitas'] += 1
        d['total'] += _num(c.get('total_mxn'))
        d['propinas'] += _num(c.get('propina_mxn'))
        f = c.get('fecha') or ''
        if f:
            if d['primera'] is None or f < d['primera']:
                d['primera'] = f
            if d['ultima'] is None or f > d['ultima']:
                d['ultima'] = f
        d['servicios'][(c.get('servicio') or '—').strip()] += 1
        d['staff'][(c.get('staff') or '—').strip()] += 1

    return [_finalizar_cliente(d, ref_date) for d in cli.values()]


ESTADO_LABEL = {
    'esperando_pago': 'Esperando seña', 'pendiente': 'Pendiente', 'confirmado': 'Confirmado',
    'en_espera': 'En espera', 'llegó': 'Llegó', 'en_servicio': 'En servicio', 'finalizado': 'Finalizado',
    'cancelado_cliente': 'Canceló la clienta', 'cancelado_salon': 'Canceló el salón',
    'no_show': 'No-show', 'reprogramado': 'Reprogramado',
}


def ficha_sin_cortes(key, nombre):
    """Ficha de una clienta que por ahora solo tiene citas en la agenda (sin cobros cargados)."""
    return {'key': key, 'nombre': ' '.join(nombre.split()), 'visitas': 0, 'total': 0.0,
            'propinas': 0.0, 'ticket': 0.0, 'primera': None, 'ultima': None, 'dias_ultima': None,
            'frecuencia': None, 'servicio_fav': '—', 'staff_fav': '—', 'walkin': False,
            'categoria': 'agenda', 'en_riesgo': False}


def resumen_clientes(cortes):
    """Directorio de clientes + métricas de retención."""
    if cortes:
        ref_date = max((c.get('fecha') or '') for c in cortes)
    else:
        ref_date = date.today().isoformat()

    clientes = agregar_clientes(cortes, ref_date)
    reales = [c for c in clientes if not c['walkin']]

    total      = len(reales)
    recurrentes = sum(1 for c in reales if c['visitas'] >= 2)
    nuevos     = sum(1 for c in reales if c['visitas'] == 1)
    vip        = sum(1 for c in reales if c['categoria'] == 'vip')
    en_riesgo  = sum(1 for c in reales if c['en_riesgo'])
    facturacion_real = sum(c['total'] for c in reales)

    reales.sort(key=lambda x: (-x['visitas'], -x['total']))

    return {
        'clientes':    reales,
        'total':       total,
        'recurrentes': recurrentes,
        'nuevos':      nuevos,
        'vip':         vip,
        'en_riesgo':   en_riesgo,
        'retencion':   (recurrentes / total * 100) if total else 0,
        'ticket_cliente': (facturacion_real / total) if total else 0,
        'ref_date':    ref_date,
    }


# ── RETENCIÓN ────────────────────────────────────────────────────────────────────
def retencion_por_mes(cortes):
    """Por cada mes: cuántas clientas visitaron, cuántas eran nuevas vs recurrentes."""
    primer_mes = {}           # key -> primer mes en que visitó
    visitas_por_mes = defaultdict(set)

    for c in sorted(cortes, key=lambda x: x.get('fecha') or ''):
        raw = (c.get('cliente') or '').strip()
        key = cliente_key(raw)
        if not key or es_walkin(key):
            continue
        mes = c.get('mes') or (c.get('fecha') or '')[:7]
        if key not in primer_mes:
            primer_mes[key] = mes
        visitas_por_mes[mes].add(key)

    resultado = []
    for mes in sorted(visitas_por_mes.keys(), reverse=True):
        visitantes = visitas_por_mes[mes]
        nuevas     = sum(1 for k in visitantes if primer_mes[k] == mes)
        recurrentes = len(visitantes) - nuevas
        total = len(visitantes)
        resultado.append({
            'mes':           mes,
            'total':         total,
            'nuevas':        nuevas,
            'recurrentes':   recurrentes,
            'tasa':          round(recurrentes / total * 100) if total else 0,
        })
    return resultado


def clientes_perdidas_y_recuperadas(cortes):
    """
    Perdida:     2+ visitas, última hace > DIAS_PERDIDA días.
    Recuperada:  tuvo un gap > DIAS_PERDIDA entre visitas consecutivas
                 pero su última visita fue hace <= DIAS_PERDIDA días.
    """
    ref = date.today().isoformat()

    fechas_por_cli = defaultdict(list)
    for c in cortes:
        raw = (c.get('cliente') or '').strip()
        key = cliente_key(raw)
        if not key or es_walkin(key):
            continue
        f = c.get('fecha')
        if f:
            fechas_por_cli[key].append(f)

    todos = agregar_clientes(
        [c for c in cortes if not es_walkin(cliente_key(c.get('cliente') or ''))],
        ref
    )
    cli_by_key = {c['key']: c for c in todos}

    perdidas    = []
    recuperadas = []

    for key, fechas in fechas_por_cli.items():
        if len(fechas) < 2:
            continue
        cli = cli_by_key.get(key)
        if not cli:
            continue
        fechas_sorted = sorted(fechas)
        dias = cli.get('dias_ultima')

        tuvo_gap = any(
            (_dias_entre(fechas_sorted[i-1], fechas_sorted[i]) or 0) > DIAS_PERDIDA
            for i in range(1, len(fechas_sorted))
        )

        if dias is not None and dias > DIAS_PERDIDA:
            perdidas.append(cli)
        elif tuvo_gap and dias is not None and dias <= DIAS_PERDIDA:
            recuperadas.append(cli)

    perdidas.sort(key=lambda x: -(x.get('dias_ultima') or 0))
    recuperadas.sort(key=lambda x: x.get('ultima') or '', reverse=True)
    return perdidas, recuperadas


def clientes_por_volver(cortes, ventana=21):
    """Clientas cuya próxima visita estimada (por frecuencia) cae en los próximos `ventana` días."""
    ref = date.today()
    todos = agregar_clientes(
        [c for c in cortes if not es_walkin(cliente_key(c.get('cliente') or ''))],
        ref.isoformat()
    )
    resultado = []
    for c in todos:
        if c['visitas'] < 2 or not c['frecuencia']:
            continue
        try:
            ultima = datetime.strptime(c['ultima'], '%Y-%m-%d').date()
        except (TypeError, ValueError):
            continue
        proxima = ultima + timedelta(days=c['frecuencia'])
        dias    = (proxima - ref).days
        if -7 <= dias <= ventana:          # -7: llegó hace hasta una semana
            c['proxima']      = proxima.isoformat()
            c['dias_proxima'] = dias
            resultado.append(c)
    resultado.sort(key=lambda x: x['dias_proxima'])
    return resultado


# ── AUTH ───────────────────────────────────────────────────────────────────────
PIN_MAX_INTENTOS = 5
PIN_BLOQUEO_MIN  = 15


def equipo_con_acceso():
    """Colaboradoras activas que tienen PIN cargado (para el selector del login)."""
    try:
        ids = [r['colaboradora_id'] for r in
               sb_service().table('equipo_acceso').select('colaboradora_id').execute().data]
    except Exception:
        return []
    if not ids:
        return []
    return get_sb().table('colaboradoras').select('id,nombre').in_('id', ids).eq(
        'activa', True).order('nombre').execute().data


def login_equipo(colab_id, pin):
    """Valida nombre + PIN. Devuelve None si entra, o el mensaje de error."""
    if not colab_id.isdigit() or not re.fullmatch(r'\d{4}', pin or ''):
        return 'Elegí tu nombre y poné tu PIN de 4 números.'
    tabla = sb_service().table('equipo_acceso')
    fila = tabla.select('*').eq('colaboradora_id', int(colab_id)).limit(1).execute().data
    colab = get_sb().table('colaboradoras').select('nombre,activa').eq(
        'id', int(colab_id)).limit(1).execute().data
    if not fila or not colab or not colab[0]['activa']:
        return 'Esa colaboradora no tiene acceso. Pedíselo a la encargada.'
    acc = fila[0]
    ahora = datetime.now(timezone.utc)
    if acc.get('bloqueado_hasta') and _parse_ts(acc['bloqueado_hasta']) > ahora:
        return f'Demasiados intentos. Probá de nuevo en {PIN_BLOQUEO_MIN} minutos.'
    if not check_password_hash(acc['pin_hash'], pin):
        intentos = (acc.get('intentos_fallidos') or 0) + 1
        cambios = {'intentos_fallidos': intentos}
        if intentos >= PIN_MAX_INTENTOS:
            cambios = {'intentos_fallidos': 0,
                       'bloqueado_hasta': (ahora + timedelta(minutes=PIN_BLOQUEO_MIN)).isoformat()}
        tabla.update(cambios).eq('colaboradora_id', int(colab_id)).execute()
        return 'PIN incorrecto.'
    if acc.get('intentos_fallidos') or acc.get('bloqueado_hasta'):
        tabla.update({'intentos_fallidos': 0, 'bloqueado_hasta': None}).eq(
            'colaboradora_id', int(colab_id)).execute()
    session.clear()
    session['equipo_id']     = int(colab_id)
    session['equipo_nombre'] = colab[0]['nombre']
    session['equipo_ver']    = acc['updated_at']
    session.permanent = True
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if es_admin():
        return redirect(url_for('index'))
    if session.get('equipo_id') and equipo_valido():
        return redirect(url_for('agenda'))
    error, modo = None, request.form.get('modo') or request.args.get('modo') or 'equipo'
    if request.method == 'POST':
        if modo == 'admin':
            if ADMIN_PASSWORD and hmac.compare_digest(request.form.get('password', ''), ADMIN_PASSWORD):
                session.clear()
                session['admin_logged_in'] = True
                session.permanent = False
                return redirect(url_for('index'))
            error = 'Contraseña incorrecta'
        else:
            try:
                error = login_equipo(request.form.get('colaboradora_id', ''), request.form.get('pin', ''))
            except Exception as e:
                app.logger.error(f'Login equipo: {e}')
                error = 'No se pudo iniciar sesión. Intentá de nuevo.'
            if not error:
                return redirect(url_for('agenda'))
    equipo = equipo_con_acceso()
    if not equipo and request.method == 'GET' and not request.args.get('modo'):
        modo = 'admin'
    return render_template('login.html', error=error, modo=modo, equipo=equipo,
                           colab_sel=request.form.get('colaboradora_id', ''))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('salon'))


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route('/sistema')
@require_admin
def index():
    mes_actual = date.today().strftime('%Y-%m')
    mes_mostrado = mes_actual
    resumen = None
    try:
        sb = get_sb()
        _, ultimo_mes = rango_meses_cortes(sb)
        if ultimo_mes and mes_actual > ultimo_mes:
            mes_mostrado = ultimo_mes

        res = sb.table('cortes').select(
            'fecha,staff,servicio,medio_pago,total_mxn,propina_mxn'
        ).eq('mes', mes_mostrado).execute()
        resumen = resumen_cortes(res.data)
    except Exception as e:
        flash(f'Error cargando métricas: {e}', 'error')
    return render_template('index.html', resumen=resumen, mes_actual=mes_mostrado)


# ── REPORTES ────────────────────────────────────────────────────────────────────
@app.route('/reportes')
@require_admin
def reportes():
    resumen = None
    meses = []
    mes_sel = request.args.get('mes')
    try:
        sb = get_sb()
        mes_hoy = date.today().strftime('%Y-%m')
        primer_mes, ultimo_mes = rango_meses_cortes(sb)
        mes_fin = max(mes_hoy, ultimo_mes) if ultimo_mes else mes_hoy
        meses = lista_meses(primer_mes, mes_fin)

        # Sin ?mes: arrancar en el último mes con data (o el actual si no hay nada)
        if not mes_sel:
            mes_sel = ultimo_mes or mes_hoy
        if meses and mes_sel not in meses:
            mes_sel = meses[0]

        res = sb.table('cortes').select(
            'fecha,staff,servicio,medio_pago,total_mxn,propina_mxn'
        ).eq('mes', mes_sel).execute()
        resumen = resumen_cortes(res.data)
    except Exception as e:
        flash(f'Error cargando reportes: {e}', 'error')

    return render_template('reportes.html',
                           resumen=resumen, meses=meses, mes_sel=mes_sel)


# ── COMISIONES ──────────────────────────────────────────────────────────────────
@app.route('/comisiones')
@require_admin
def comisiones():
    resumen  = None
    meses    = []
    mes_sel  = request.args.get('mes')
    periodo  = request.args.get('periodo', '0')   # '0'=mes, '1'=1ra quincena, '2'=2da quincena
    try:
        sb = get_sb()
        mes_hoy = date.today().strftime('%Y-%m')
        primer_mes, ultimo_mes = rango_meses_cortes(sb)
        mes_fin = max(mes_hoy, ultimo_mes) if ultimo_mes else mes_hoy
        meses   = lista_meses(primer_mes, mes_fin)

        if not mes_sel:
            mes_sel = ultimo_mes or mes_hoy
        if meses and mes_sel not in meses:
            mes_sel = meses[0]

        cortes_mes = fetch_all(sb, 'cortes', 'fecha,staff,servicio,medio_pago,total_mxn,propina_mxn')
        cortes_mes = [c for c in cortes_mes if (c.get('fecha') or '')[:7] == mes_sel]

        if periodo == '1':
            cortes_mes = [c for c in cortes_mes if int((c.get('fecha') or '1900-01-01')[8:10]) <= 15]
        elif periodo == '2':
            cortes_mes = [c for c in cortes_mes if int((c.get('fecha') or '1900-01-01')[8:10]) > 15]

        resumen = resumen_cortes(cortes_mes)
    except Exception as e:
        flash(f'Error cargando comisiones: {e}', 'error')

    return render_template('comisiones.html',
                           resumen=resumen, meses=meses, mes_sel=mes_sel, periodo=periodo)


# ── CLIENTES ────────────────────────────────────────────────────────────────────
@app.route('/clientes')
@require_admin
def clientes():
    resumen = None
    try:
        sb = get_sb()
        cortes = fetch_all(sb, 'cortes', 'cliente,fecha,total_mxn,propina_mxn,staff,servicio')
        resumen = resumen_clientes(cortes)
        # Clientas que sacaron cita pero todavía no tienen cobros: también tienen ficha
        en_fichas = {c['key'] for c in resumen['clientes']}
        solo_agenda = {}
        for c in fetch_all(sb, 'clientes_reservas', 'id,nombre,apellido'):
            key = clave_clienta(c)
            if key and not es_walkin(key) and key not in en_fichas:
                solo_agenda.setdefault(key, ficha_sin_cortes(key, f"{c['nombre']} {c.get('apellido') or ''}"))
        resumen['clientes'] += sorted(solo_agenda.values(), key=lambda c: c['nombre'])
    except Exception as e:
        flash(f'Error cargando clientes: {e}', 'error')
    return render_template('clientes.html', resumen=resumen)


@app.route('/cliente')
@require_admin
def cliente_detalle():
    key = cliente_key(request.args.get('c', ''))
    if not key:
        return redirect(url_for('clientes'))

    cli = None
    historial = []
    info = {}
    citas = []
    contacto = {}
    try:
        sb = get_sb()
        cortes = fetch_all(sb, 'cortes',
                           'id,cliente,fecha,total_mxn,propina_mxn,staff,servicio,medio_pago,notas,color')
        ref_date = max((c.get('fecha') or '') for c in cortes) if cortes else date.today().isoformat()

        propios = [c for c in cortes if cliente_key(c.get('cliente')) == key]
        if propios:
            cli = agregar_clientes(propios, ref_date)[0]
            historial = sorted(propios, key=lambda c: (c.get('fecha') or '', c.get('id') or 0),
                               reverse=True)

        try:
            res = sb.table('clientes_info').select('*').eq('key', key).limit(1).execute()
            if res.data:
                info = res.data[0]
        except Exception:
            pass

        # Citas de la agenda: las clientas de turnos con el mismo nombre completo
        agenda = [c for c in fetch_all(sb, 'clientes_reservas', 'id,nombre,apellido,telefono,email')
                  if clave_clienta(c) == key]
        if agenda:
            citas = [t for t in sb.table('turnos').select(
                'id,fecha,hora_inicio,estado,precio,canal,created_at,colaboradoras(nombre),servicios(nombre)'
            ).in_('cliente_id', [c['id'] for c in agenda]).order('fecha', desc=True).execute().data
                if not hold_vencido(t)]
            contacto = {'telefono': next((c['telefono'] for c in agenda if c.get('telefono')), ''),
                        'email':    next((c['email'] for c in agenda if c.get('email')), '')}
            if cli is None:
                cli = ficha_sin_cortes(key, f"{agenda[0]['nombre']} {agenda[0].get('apellido') or ''}")

    except Exception as e:
        flash(f'Error cargando el cliente: {e}', 'error')

    if cli is None:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('clientes'))

    return render_template('cliente.html', cli=cli, historial=historial, info=info,
                           citas=citas, contacto=contacto, estados_turno=ESTADO_LABEL)


@app.route('/cliente/<path:key>/info', methods=['POST'])
@require_admin
def editar_info_cliente(key):
    try:
        sb  = get_sb()
        row = {'key': key, 'updated_at': datetime.utcnow().isoformat()}
        for campo in ['telefono', 'cumpleanos', 'idioma', 'canal', 'observaciones', 'preferencias']:
            val = request.form.get(campo, '').strip()
            row[campo] = val if val else None
        sb.table('clientes_info').upsert(row).execute()
        flash('Datos del cliente actualizados.', 'success')
    except Exception as e:
        flash(f'Error guardando datos: {e}', 'error')
    return redirect(url_for('cliente_detalle', c=key))


# ── RETENCIÓN ────────────────────────────────────────────────────────────────────
@app.route('/retencion')
@require_admin
def retencion():
    por_mes     = []
    por_volver  = []
    perdidas    = []
    recuperadas = []
    try:
        sb     = get_sb()
        cortes = fetch_all(sb, 'cortes', 'cliente,fecha,mes,total_mxn,propina_mxn,staff,servicio')
        por_mes               = retencion_por_mes(cortes)
        por_volver            = clientes_por_volver(cortes)
        perdidas, recuperadas = clientes_perdidas_y_recuperadas(cortes)
    except Exception as e:
        flash(f'Error cargando retención: {e}', 'error')
    return render_template('retencion.html',
                           por_mes=por_mes, por_volver=por_volver,
                           perdidas=perdidas, recuperadas=recuperadas)


# ── REGISTRAR CORTE ────────────────────────────────────────────────────────────
@app.route('/corte', methods=['GET', 'POST'])
@require_admin
def corte():
    if request.method == 'POST':
        row = corte_row_from_form(request.form)
        if row is None:
            flash('Completá todos los campos obligatorios.', 'error')
            return redirect(url_for('corte'))

        try:
            get_sb().table('cortes').insert(row).execute()
            flash(f"Corte registrado — {row['staff']} · {row['servicio']} · ${row['total_cobrado']:,.0f}", 'success')
        except Exception as e:
            flash(f'Error al guardar: {e}', 'error')

        return redirect(url_for('corte'))

    return render_template('corte.html',
                           staff=STAFF,
                           servicios=SERVICIOS,
                           medios=MEDIOS_PAGO,
                           today=date.today().isoformat())


# ── IMPORTAR PLANILLA DESDE FOTO ───────────────────────────────────────────────
@app.route('/api/parse-planilla', methods=['POST'])
@require_admin
def api_parse_planilla():
    """Recibe una imagen de la planilla de caja y devuelve las filas extraídas con IA."""
    try:
        if 'imagen' not in request.files:
            return jsonify({'error': 'No se recibió imagen'}), 400
        f = request.files['imagen']
        if not f.filename:
            return jsonify({'error': 'Archivo vacío'}), 400

        img_bytes  = f.read()
        img_b64    = base64.standard_b64encode(img_bytes).decode('utf-8')
        media_type = f.content_type or 'image/jpeg'

        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY no configurada'}), 500

        client = _anthropic.Anthropic(api_key=api_key)

        prompt = """Esta es una planilla de caja de un salón de belleza llamado Maru Nails.
Extraé TODAS las filas con datos (ignorá filas vacías).
Para cada fila devolvé un objeto JSON con exactamente estas claves:
- "cliente": nombre del cliente (string, "Walk in" si está vacío o ilegible)
- "staff": nombre del colaborador/a tal como aparece (string)
- "servicio": nombre del servicio (string)
- "total": monto total cobrado (número sin símbolos, puede ser decimal con coma o punto)
- "propina": propina si la hay (número, 0 si no hay)
- "medio_pago": forma de pago — mapeá a uno de: "Efectivo", "Tarjeta", "Transferencia", "USD cash", "Otro"

Si la imagen muestra una fecha (por ej. "DÍA: 29/6"), incluila en el campo "fecha_planilla" en el primer objeto (formato DD/MM).

Respondé ÚNICAMENTE con un array JSON válido, sin texto extra, sin markdown, sin explicaciones.
Ejemplo: [{"cliente":"Mayra","staff":"Fanny","servicio":"refilAcrilico","total":630,"propina":0,"medio_pago":"Tarjeta"}]"""

        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1024,
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': media_type, 'data': img_b64}},
                    {'type': 'text',  'text': prompt},
                ],
            }],
        )

        import json as _json
        texto = msg.content[0].text.strip()
        # Limpiar posibles markdown code fences
        if texto.startswith('```'):
            texto = texto.split('```')[1]
            if texto.startswith('json'):
                texto = texto[4:]
        filas = _json.loads(texto.strip())
        return jsonify({'filas': filas})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/import-cortes', methods=['POST'])
@require_admin
def api_import_cortes():
    """Recibe un array JSON de filas de corte y las inserta en bulk."""
    try:
        import json as _json
        data  = request.get_json(force=True)
        filas = data.get('filas', [])
        fecha = data.get('fecha', date.today().isoformat())
        if not filas:
            return jsonify({'error': 'Sin filas'}), 400

        rows = []
        errores = []
        for i, f in enumerate(filas):
            try:
                total   = float(str(f.get('total', 0)).replace(',', '.') or 0)
                propina = float(str(f.get('propina', 0)).replace(',', '.') or 0)
                staff   = (f.get('staff') or '').strip().upper()
                servicio  = (f.get('servicio') or '').strip()
                medio_pago = f.get('medio_pago') or 'Otro'
                cliente   = (f.get('cliente') or 'Walk in').strip() or 'Walk in'
                if not staff or not servicio or total <= 0:
                    errores.append(f"Fila {i+1}: datos incompletos")
                    continue
                d = datetime.strptime(fecha, '%Y-%m-%d').date()
                semana, mes, quincena = get_week_quincena(d)
                rows.append({
                    'fecha':         fecha,
                    'cliente':       cliente,
                    'staff':         staff,
                    'servicio':      servicio,
                    'moneda':        'MXN',
                    'total_cobrado': total,
                    'propina':       propina,
                    'medio_pago':    medio_pago,
                    'notas':         '',
                    'color':         None,
                    'venta_neta':    round(total - propina, 2),
                    'tc':            1,
                    'total_mxn':     round(total, 2),
                    'propina_mxn':   round(propina, 2),
                    'neto_mxn':      round(total - propina, 2),
                    'mes':           mes,
                    'semana':        semana,
                    'quincena':      quincena,
                })
            except Exception as ex:
                errores.append(f"Fila {i+1}: {ex}")

        if rows:
            get_sb().table('cortes').insert(rows).execute()

        return jsonify({'insertados': len(rows), 'errores': errores})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── REGISTRAR GASTO ────────────────────────────────────────────────────────────
@app.route('/gasto', methods=['GET', 'POST'])
@require_admin
def gasto():
    if request.method == 'POST':
        row = gasto_row_from_form(request.form)
        if row is None:
            flash('Completá todos los campos obligatorios.', 'error')
            return redirect(url_for('gasto'))

        try:
            get_sb().table('gastos').insert(row).execute()
            flash(f"Gasto registrado — {row['categoria']} · ${row['importe']:,.0f}", 'success')
        except Exception as e:
            flash(f'Error al guardar: {e}', 'error')

        return redirect(url_for('gasto'))

    return render_template('gasto.html',
                           categorias=CATEGORIAS_GASTO,
                           medios=MEDIOS_PAGO,
                           today=date.today().isoformat())


# ── CASHFLOW ───────────────────────────────────────────────────────────────────
@app.route('/cashflow')
@require_admin
def cashflow():
    meses = []
    dias  = []
    control_caja = {'efectivo': 0, 'tarjeta': 0, 'transferencia': 0, 'total': 0}
    try:
        sb = get_sb()
        cortes_all = fetch_all(sb, 'cortes', 'fecha,mes,total_mxn,medio_pago')
        gastos_all = fetch_all(sb, 'gastos', 'fecha,mes,importe_mxn,medio_pago')

        def _empty():
            return {
                'ing_efectivo': 0, 'ing_tarjeta': 0, 'ing_transferencia': 0, 'ing_total': 0,
                'gasto_efectivo': 0, 'gasto_tarjeta': 0, 'gasto_transferencia': 0, 'gasto_total': 0,
                'saldo_efectivo': 0, 'saldo_tarjeta': 0, 'saldo_transferencia': 0, 'saldo_total': 0,
            }

        data_mes = defaultdict(_empty)
        data_dia = defaultdict(_empty)

        for c in cortes_all:
            mes   = c.get('mes') or ''
            fecha = c.get('fecha') or ''
            mxn   = float(c.get('total_mxn') or 0)
            medio = (c.get('medio_pago') or '').strip()
            for d in (data_mes[mes], data_dia[fecha]):
                d['ing_total'] += mxn
                if medio == 'Efectivo':
                    d['ing_efectivo'] += mxn
                elif medio == 'Tarjeta':
                    d['ing_tarjeta'] += mxn
                else:
                    d['ing_transferencia'] += mxn

        for g in gastos_all:
            mes   = g.get('mes') or ''
            fecha = g.get('fecha') or ''
            mxn   = float(g.get('importe_mxn') or 0)
            medio = (g.get('medio_pago') or '').strip()
            for d in (data_mes[mes], data_dia[fecha]):
                d['gasto_total'] += mxn
                if medio == 'Efectivo':
                    d['gasto_efectivo'] += mxn
                elif medio == 'Tarjeta':
                    d['gasto_tarjeta'] += mxn
                else:
                    d['gasto_transferencia'] += mxn

        for mes, d in sorted(data_mes.items()):
            d['mes'] = mes
            d['saldo_efectivo']      = d['ing_efectivo']      - d['gasto_efectivo']
            d['saldo_tarjeta']       = d['ing_tarjeta']       - d['gasto_tarjeta']
            d['saldo_transferencia'] = d['ing_transferencia'] - d['gasto_transferencia']
            d['saldo_total']         = d['saldo_efectivo'] + d['saldo_tarjeta'] + d['saldo_transferencia']
            meses.append(d)

        for fecha, d in sorted(data_dia.items(), reverse=True):
            d['fecha'] = fecha
            d['saldo_efectivo']      = d['ing_efectivo']      - d['gasto_efectivo']
            d['saldo_tarjeta']       = d['ing_tarjeta']       - d['gasto_tarjeta']
            d['saldo_transferencia'] = d['ing_transferencia'] - d['gasto_transferencia']
            d['saldo_total']         = d['saldo_efectivo'] + d['saldo_tarjeta'] + d['saldo_transferencia']
            dias.append(d)

        control_caja = {
            'efectivo':      sum(d['saldo_efectivo']      for d in meses),
            'tarjeta':       sum(d['saldo_tarjeta']       for d in meses),
            'transferencia': sum(d['saldo_transferencia'] for d in meses),
        }
        control_caja['total'] = control_caja['efectivo'] + control_caja['tarjeta'] + control_caja['transferencia']

    except Exception as e:
        flash(f'Error cargando cashflow: {e}', 'error')

    mes_actual = date.today().strftime('%Y-%m')
    hoy        = date.today().isoformat()
    meses_dias = sorted({d['fecha'][:7] for d in dias}, reverse=True)
    return render_template('cashflow.html', meses=meses, dias=dias,
                           mes_actual=mes_actual, hoy=hoy, meses_dias=meses_dias,
                           control_caja=control_caja)


# ── MOVIMIENTOS (editar / borrar) ───────────────────────────────────────────────
@app.route('/movimientos')
@require_admin
def movimientos():
    cortes, gastos = [], []
    meses = []
    mes_sel = request.args.get('mes')
    try:
        sb = get_sb()
        mes_hoy = date.today().strftime('%Y-%m')
        primer_mes, ultimo_mes = rango_meses_cortes(sb)
        mes_fin = max(mes_hoy, ultimo_mes) if ultimo_mes else mes_hoy
        meses = lista_meses(primer_mes, mes_fin)

        if not mes_sel:
            mes_sel = ultimo_mes or mes_hoy
        if meses and mes_sel not in meses:
            mes_sel = meses[0]

        cortes = fetch_all(sb, 'cortes', 'id,fecha,cliente,staff,servicio,total_mxn,medio_pago')
        cortes = [c for c in cortes if (c.get('fecha') or '')[:7] == mes_sel]
        cortes.sort(key=lambda c: (c.get('fecha') or '', c.get('id') or 0), reverse=True)

        gastos_all = fetch_all(sb, 'gastos', 'id,fecha,categoria,proveedor,descripcion,importe_mxn,medio_pago')
        gastos = [g for g in gastos_all if (g.get('fecha') or '')[:7] == mes_sel]
        gastos.sort(key=lambda g: (g.get('fecha') or '', g.get('id') or 0), reverse=True)

    except Exception as e:
        flash(f'Error cargando movimientos: {e}', 'error')
    return render_template('movimientos.html', cortes=cortes, gastos=gastos,
                           meses=meses, mes_sel=mes_sel)


@app.route('/corte/<int:cid>/editar', methods=['GET', 'POST'])
@require_admin
def editar_corte(cid):
    sb = get_sb()
    if request.method == 'POST':
        row = corte_row_from_form(request.form)
        if row is None:
            flash('Completá todos los campos obligatorios.', 'error')
            return redirect(url_for('editar_corte', cid=cid))
        try:
            sb.table('cortes').update(row).eq('id', cid).execute()
            flash('Corte actualizado.', 'success')
        except Exception as e:
            flash(f'Error al actualizar: {e}', 'error')
        return redirect(url_for('movimientos'))

    try:
        res = sb.table('cortes').select('*').eq('id', cid).limit(1).execute()
    except Exception as e:
        flash(f'Error cargando el corte: {e}', 'error')
        return redirect(url_for('movimientos'))
    if not res.data:
        flash('Corte no encontrado.', 'error')
        return redirect(url_for('movimientos'))

    return render_template('corte.html',
                           c=res.data[0],
                           action=url_for('editar_corte', cid=cid),
                           staff=STAFF,
                           servicios=SERVICIOS,
                           medios=MEDIOS_PAGO,
                           today=date.today().isoformat())


@app.route('/corte/<int:cid>/borrar', methods=['POST'])
@require_admin
def borrar_corte(cid):
    try:
        get_sb().table('cortes').delete().eq('id', cid).execute()
        flash('Corte eliminado.', 'success')
    except Exception as e:
        flash(f'Error al borrar: {e}', 'error')
    return redirect(url_for('movimientos'))


@app.route('/gasto/<int:gid>/editar', methods=['GET', 'POST'])
@require_admin
def editar_gasto(gid):
    sb = get_sb()
    if request.method == 'POST':
        row = gasto_row_from_form(request.form)
        if row is None:
            flash('Completá todos los campos obligatorios.', 'error')
            return redirect(url_for('editar_gasto', gid=gid))
        try:
            sb.table('gastos').update(row).eq('id', gid).execute()
            flash('Gasto actualizado.', 'success')
        except Exception as e:
            flash(f'Error al actualizar: {e}', 'error')
        return redirect(url_for('movimientos'))

    try:
        res = sb.table('gastos').select('*').eq('id', gid).limit(1).execute()
    except Exception as e:
        flash(f'Error cargando el gasto: {e}', 'error')
        return redirect(url_for('movimientos'))
    if not res.data:
        flash('Gasto no encontrado.', 'error')
        return redirect(url_for('movimientos'))

    return render_template('gasto.html',
                           g=res.data[0],
                           action=url_for('editar_gasto', gid=gid),
                           categorias=CATEGORIAS_GASTO,
                           medios=MEDIOS_PAGO,
                           today=date.today().isoformat())


@app.route('/gasto/<int:gid>/borrar', methods=['POST'])
@require_admin
def borrar_gasto(gid):
    try:
        get_sb().table('gastos').delete().eq('id', gid).execute()
        flash('Gasto eliminado.', 'success')
    except Exception as e:
        flash(f'Error al borrar: {e}', 'error')
    return redirect(url_for('movimientos'))


# ── SISTEMA DE TURNOS — PÚBLICO ────────────────────────────────────────────────

@app.route('/reservar')
def reservar():
    return render_template('reservar.html', sena_activa=SENA_ACTIVA, sena_mxn=SENA_MXN)


@app.route('/api/servicios')
def api_servicios():
    try:
        sb = get_sb()
        data = sb.table('servicios').select('*').eq('activo', True).order('categoria').order('orden').execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/colaboradoras/disponibles')
def api_colaboradoras_disponibles():
    """Colaboradoras activas disponibles para una fecha dada (respeta horarios y bloqueos)."""
    try:
        sb = get_sb()
        fecha_str = request.args.get('fecha')
        if not fecha_str:
            from datetime import date
            fecha_str = date.today().isoformat()

        fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_dt.weekday()  # 0=lunes

        todas = sb.table('colaboradoras').select('*').eq('activa', True).execute().data

        bloqueadas_hoy = {
            b['colaboradora_id']
            for b in sb.table('bloqueos').select('colaboradora_id').eq('fecha', fecha_str).eq('todo_el_dia', True).execute().data
        }

        con_horario = {
            d['colaboradora_id']
            for d in sb.table('disponibilidad').select('colaboradora_id').eq('dia_semana', dia_semana).execute().data
        }

        disponibles = [
            c for c in todas
            if c['id'] not in bloqueadas_hoy and c['id'] in con_horario
        ]

        # Si ninguna tiene horario cargado, devolver todas las activas (evita quedarse sin opciones)
        if not disponibles:
            disponibles = [c for c in todas if c['id'] not in bloqueadas_hoy]

        return jsonify(disponibles)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/colaboradoras')
def api_colaboradoras():
    try:
        sb = get_sb()
        servicio_ids_str = request.args.get('servicio_ids', '')
        servicio_id = request.args.get('servicio_id')

        if servicio_ids_str:
            ids = [int(x) for x in servicio_ids_str.split(',') if x.strip()]
            if ids:
                colab_sets = []
                for sid in ids:
                    rows = sb.table('colaboradora_servicios').select('colaboradora_id').eq('servicio_id', sid).execute()
                    colab_sets.append({r['colaboradora_id'] for r in rows.data})
                valid_ids = colab_sets[0]
                for s in colab_sets[1:]:
                    valid_ids = valid_ids.intersection(s)
                if valid_ids:
                    colabs = sb.table('colaboradoras').select('*').in_('id', list(valid_ids)).eq('activa', True).execute().data
                else:
                    colabs = sb.table('colaboradoras').select('*').eq('activa', True).execute().data
            else:
                colabs = sb.table('colaboradoras').select('*').eq('activa', True).execute().data
        elif servicio_id:
            data = sb.table('colaboradora_servicios').select(
                'colaboradoras(*)'
            ).eq('servicio_id', servicio_id).execute()
            colabs = [r['colaboradoras'] for r in data.data
                      if r.get('colaboradoras') and r['colaboradoras'].get('activa')]
            if not colabs:
                colabs = sb.table('colaboradoras').select('*').eq('activa', True).execute().data
        else:
            colabs = sb.table('colaboradoras').select('*').eq('activa', True).execute().data
        return jsonify(colabs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def calcular_slots(sb, colaboradora_id, fecha_str, servicio_ids=None,
                   servicio_id=None, duracion_total=None, respetar_anticipacion=True):
    """Horarios libres para una fecha. colaboradora_id = id o 'any'.
    Devuelve [{colaboradora_id, hora, hora_fin}] (con 'any', uno por hora)."""
    servicios_info = []  # [{duracion_min, tipo_estacion}, ...]
    duracion = 0

    if servicio_ids:
        for sid in servicio_ids:
            srv = sb.table('servicios').select('duracion_min,categoria').eq('id', int(sid)).limit(1).execute()
            if srv.data:
                cat = srv.data[0]['categoria']
                servicios_info.append({
                    'duracion_min':   srv.data[0]['duracion_min'],
                    'tipo_estacion':  estacion_de_categoria(cat),
                })
                duracion += srv.data[0]['duracion_min']
    elif duracion_total:
        duracion = int(duracion_total)
    elif servicio_id:
        srv = sb.table('servicios').select('duracion_min,categoria').eq('id', servicio_id).limit(1).execute()
        if not srv.data:
            return []
        cat = srv.data[0]['categoria']
        servicios_info = [{'duracion_min': srv.data[0]['duracion_min'], 'tipo_estacion': estacion_de_categoria(cat)}]
        duracion = srv.data[0]['duracion_min']
    else:
        return []

    if not duracion:
        return []

    fecha_dt   = datetime.strptime(fecha_str, '%Y-%m-%d')
    dia_semana = fecha_dt.weekday()

    # Turnos del día que ocupan lugar (sin cancelados ni señas vencidas)
    turnos_dia = [
        t for t in sb.table('turnos').select(
            'colaboradora_id,hora_inicio,hora_fin,estado,canal,created_at,servicios(categoria)'
        ).eq('fecha', fecha_str).execute().data
        if turno_ocupa(t)
    ]

    # Ocupación por estación (para el chequeo de capacidad)
    all_turnos_dia = []
    if servicios_info:
        for t in turnos_dia:
            cat = t.get('servicios', {}).get('categoria') if t.get('servicios') else None
            all_turnos_dia.append({
                'hora_inicio':    t['hora_inicio'][:5],
                'hora_fin':       t['hora_fin'][:5],
                'tipo_estacion':  estacion_de_categoria(cat) if cat else None,
            })

    if colaboradora_id == 'any':
        colabs    = sb.table('colaboradoras').select('id').eq('activa', True).execute().data
        colab_ids = [c['id'] for c in colabs]
    else:
        colab_ids = [int(colaboradora_id)]

    # Hoy: la web pide 2 hs de anticipación; la recepción puede cargar "para ahora"
    # (hasta 30 min atrás), pero no horarios que ya pasaron
    now      = ahora_salon()
    min_hora = None
    if fecha_dt.date() == now.date():
        min_hora = now + timedelta(hours=2) if respetar_anticipacion else now - timedelta(minutes=30)

    slots = []
    for colab_id in colab_ids:
        schedule = sb.table('disponibilidad').select('hora_inicio,hora_fin').eq(
            'colaboradora_id', colab_id).eq('dia_semana', dia_semana).execute()
        if not schedule.data:
            continue

        bloqueos = sb.table('bloqueos').select('*').eq(
            'colaboradora_id', colab_id).eq('fecha', fecha_str).execute()
        if bloqueos.data and any(b.get('todo_el_dia') for b in bloqueos.data):
            continue

        ocupados = [(t['hora_inicio'][:5], t['hora_fin'][:5])
                    for t in turnos_dia if t.get('colaboradora_id') == colab_id]

        for sched in schedule.data:
            h_start  = sched['hora_inicio'][:5]
            h_end    = sched['hora_fin'][:5]
            cur      = datetime.strptime(f"{fecha_str} {h_start}", '%Y-%m-%d %H:%M')
            end      = datetime.strptime(f"{fecha_str} {h_end}",   '%Y-%m-%d %H:%M')
            slot_dur = timedelta(minutes=duracion)
            interval = timedelta(minutes=30)

            while cur + slot_dur <= end:
                s_str = cur.strftime('%H:%M')
                e_str = (cur + slot_dur).strftime('%H:%M')

                if min_hora and cur < min_hora:
                    cur += interval
                    continue

                # 1. Colaboradora libre durante toda la franja
                if any(s_str < o_fin and e_str > o_ini for o_ini, o_fin in ocupados):
                    cur += interval
                    continue

                # 2. Estaciones disponibles para cada servicio en secuencia
                station_ok   = True
                hora_cursor  = cur
                for srv_info in servicios_info:
                    srv_s   = hora_cursor.strftime('%H:%M')
                    hora_cursor += timedelta(minutes=srv_info['duracion_min'])
                    srv_e   = hora_cursor.strftime('%H:%M')
                    estacion = srv_info['tipo_estacion']
                    if estacion and estacion in CAPACIDAD_ESTACIONES:
                        cap       = CAPACIDAD_ESTACIONES[estacion]
                        ocupacion = sum(
                            1 for t in all_turnos_dia
                            if t['tipo_estacion'] == estacion
                            and t['hora_inicio'] < srv_e
                            and t['hora_fin']    > srv_s
                        )
                        if ocupacion >= cap:
                            station_ok = False
                            break

                if station_ok:
                    slots.append({'colaboradora_id': colab_id, 'hora': s_str, 'hora_fin': e_str})
                cur += interval

    if colaboradora_id == 'any':
        seen, unique = set(), []
        for s in sorted(slots, key=lambda x: x['hora']):
            if s['hora'] not in seen:
                seen.add(s['hora'])
                unique.append(s)
        return unique
    return sorted(slots, key=lambda x: x['hora'])


@app.route('/api/slots')
def api_slots():
    try:
        fecha_str = request.args.get('fecha')
        if not fecha_str:
            return jsonify([])
        servicio_ids = [int(x) for x in request.args.get('servicio_ids', '').split(',') if x.strip()]
        return jsonify(calcular_slots(
            get_sb(),
            request.args.get('colaboradora_id', 'any'),
            fecha_str,
            servicio_ids=servicio_ids,
            servicio_id=request.args.get('servicio_id'),
            duracion_total=request.args.get('duracion_total'),
            respetar_anticipacion=not (request.args.get('admin') and (es_admin() or equipo_valido())),
        ))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


class ReservaError(Exception):
    def __init__(self, msg, status=400, **extra):
        super().__init__(msg)
        self.status, self.extra = status, extra


# ── CLIENTAS: una sola ficha por persona ───────────────────────────────────────
def clave_clienta(c):
    """Clave de ficha de una clienta de la agenda: su nombre completo normalizado.
    Es la misma clave que agrupa los cortes, así la ficha junta cobros y citas."""
    return cliente_key(f"{c.get('nombre') or ''} {c.get('apellido') or ''}")


def tel_digitos(tel):
    """Últimos 10 dígitos: '+52 984 182 6374' y '9841826374' son el mismo teléfono."""
    d = re.sub(r'\D', '', tel or '')
    return d[-10:] if len(d) >= 8 else ''


def buscar_clienta(clientas, nombre='', apellido='', telefono='', email=''):
    """Clienta ya cargada que coincide por teléfono, email o nombre completo (en ese orden).
    Un nombre suelto ('Ana') solo alcanza si esa ficha no tiene teléfono: dos 'Ana' con
    teléfonos distintos son dos personas."""
    tel = tel_digitos(telefono)
    if tel:
        c = next((c for c in clientas if tel_digitos(c.get('telefono')) == tel), None)
        if c:
            return c
    mail = (email or '').strip().lower()
    if mail:
        c = next((c for c in clientas if (c.get('email') or '').strip().lower() == mail), None)
        if c:
            return c
    key = cliente_key(f'{nombre or ""} {apellido or ""}')
    if not key or es_walkin(key):
        return None
    mismas = [c for c in clientas if clave_clienta(c) == key]
    if len(mismas) == 1 and (' ' in key or not tel_digitos(mismas[0].get('telefono'))):
        return mismas[0]
    return None


def clienta_para_reserva(sb, data, rechazar_bloqueada=False):
    """La clienta de una cita: la elegida en el buscador (cliente_id), una ya cargada que
    coincida, o una nueva. A una existente solo se le completan teléfono/email vacíos."""
    clientas = fetch_all(sb, 'clientes_reservas', 'id,nombre,apellido,telefono,email,bloqueado')
    if data.get('cliente_id'):
        c = next((x for x in clientas if str(x['id']) == str(data['cliente_id'])), None)
        if not c:
            raise ReservaError('La clienta elegida ya no existe. Búscala de nuevo.', 404)
    else:
        c = buscar_clienta(clientas, data.get('nombre'), data.get('apellido'),
                           data.get('telefono'), data.get('email'))

    if c:
        if rechazar_bloqueada and c.get('bloqueado'):
            raise ReservaError('No es posible completar la reserva online. '
                               'Por favor contactá directamente al salón.', 403)
        faltan = {k: data[k].strip() for k in ('telefono', 'email')
                  if (data.get(k) or '').strip() and not (c.get(k) or '').strip()}
        if faltan:
            sb.table('clientes_reservas').update(faltan).eq('id', c['id']).execute()
        return c['id']

    nueva = {
        'nombre': data['nombre'],
        'apellido': data.get('apellido') or '',
        'telefono': data.get('telefono') or '',
        'email': data.get('email') or '',
        'idioma': data.get('idioma') or 'es',
        'acepto_politicas': bool(data.get('acepto_politicas')),
        'notas': data.get('notas') or '',
        'es_recurrente': False,
    }
    if data.get('fecha_nacimiento'):
        nueva['fecha_nacimiento'] = data['fecha_nacimiento']
    return sb.table('clientes_reservas').insert(nueva).execute().data[0]['id']


def directorio_clientas(clientas, cortes, tel_fichas):
    """Lista para el buscador de la agenda: clientas de la agenda + fichas de los cortes que
    todavía no sacaron cita. Cada una con sus visitas (cortes) y última visita."""
    fichas = {f['key']: f for f in agregar_clientes(
        [c for c in cortes if not es_walkin(cliente_key(c.get('cliente')))], date.today().isoformat())}
    lista, cubiertas = [], set()
    for c in clientas:
        key = clave_clienta(c)
        if not key or es_walkin(key):
            continue
        f = fichas.get(key) or {}
        cubiertas.add(key)
        lista.append({'id': c['id'], 'key': key, 'telefono': c.get('telefono') or '',
                      'nombre': f"{c.get('nombre') or ''} {c.get('apellido') or ''}".strip(),
                      'visitas': f.get('visitas', 0), 'ultima': f.get('ultima')})
    for key, f in fichas.items():
        if key not in cubiertas:
            lista.append({'id': None, 'key': key, 'telefono': tel_fichas.get(key) or '',
                          'nombre': f['nombre'], 'visitas': f['visitas'], 'ultima': f['ultima']})
    lista.sort(key=lambda x: (-x['visitas'], x['nombre'].lower()))
    return lista


def crear_reserva(sb, data, canal, con_sena=True, respetar_anticipacion=True, rechazar_bloqueada=False):
    """Crea la cita (uno o más servicios en secuencia). La usan la web y la recepción.
    Con seña: citas en esperando_pago + pagos_sena + preferencia de MP (horario retenido
    según HOLD_MIN_POR_CANAL). Sin seña: citas confirmadas."""
    servicio_ids = data.get('servicio_ids') or []
    if not servicio_ids and data.get('servicio_id'):
        servicio_ids = [data['servicio_id']]
    if not servicio_ids:
        raise ReservaError('Servicio requerido')

    servicios_data = []
    for sid in servicio_ids:
        srv = sb.table('servicios').select('nombre,precio_desde,duracion_min').eq('id', sid).limit(1).execute()
        if not srv.data:
            raise ReservaError(f'Servicio {sid} no encontrado')
        servicios_data.append(srv.data[0])

    # Revalidar el horario en el server: otra persona pudo tomarlo mientras tanto
    hora_ini = data['hora']
    pedida   = data.get('colaboradora_id')
    pedida   = 'any' if not pedida or pedida == 'any' else int(pedida)
    libres   = calcular_slots(sb, pedida, data['fecha'], servicio_ids=servicio_ids,
                              respetar_anticipacion=respetar_anticipacion)
    slot     = next((s for s in libres if s['hora'] == hora_ini), None)
    if not slot:
        raise ReservaError('Ese horario ya no está disponible. Por favor elige otro.', 409, horario_tomado=True)
    colaboradora_id = slot['colaboradora_id']

    cliente_id = clienta_para_reserva(sb, data, rechazar_bloqueada)

    pago = None
    if con_sena and SENA_ACTIVA:
        pago = tabla_pagos().insert({
            'cliente_id': cliente_id,
            'monto':      SENA_MXN,
            'estado':     'pendiente',
        }).execute().data[0]

    if pago:
        estado = 'esperando_pago'
    elif con_sena:
        estado = 'pendiente'      # seña pedida pero MP sin configurar: como antes
    else:
        estado = 'confirmado'

    turnos_creados = []
    hora_cursor = datetime.strptime(hora_ini, '%H:%M')
    for i, sid in enumerate(servicio_ids):
        t_ini = hora_cursor.strftime('%H:%M')
        hora_cursor += timedelta(minutes=servicios_data[i]['duracion_min'])
        t_fin = hora_cursor.strftime('%H:%M')
        row = {
            'cliente_id': cliente_id,
            'colaboradora_id': colaboradora_id,
            'servicio_id': int(sid),
            'fecha': data['fecha'],
            'hora_inicio': t_ini,
            'hora_fin': t_fin,
            'estado': estado,
            'precio': servicios_data[i]['precio_desde'],
            'notas': data.get('notas', ''),
            'canal': canal,
        }
        if pago:
            row['pago_sena_id'] = pago['id']
        turno = sb.table('turnos').insert(row).execute()
        turnos_creados.append(turno.data[0]['id'])

    resultado = {
        'turno_ids':       turnos_creados,
        'colaboradora_id': colaboradora_id,
        'servicios':       [s['nombre'] for s in servicios_data],
        'estado':          estado,
    }
    if not pago:
        return resultado

    try:
        pref = crear_preferencia_sena(pago, data, resultado['servicios'],
                                      hold_min(canal) - MP_MARGEN_MIN)
    except Exception:
        # Sin link de pago no hay reserva: liberar el horario
        sb.table('turnos').delete().eq('pago_sena_id', pago['id']).execute()
        tabla_pagos().delete().eq('id', pago['id']).execute()
        raise ReservaError('No pudimos generar el pago de la seña. Intenta de nuevo en unos minutos.', 502)

    tabla_pagos().update({'mp_preference_id': pref['id']}).eq('id', pago['id']).execute()
    resultado.update({
        'init_point': pref['init_point'],
        'url_pago':   url_pago(pago['token']),
        'monto':      pago['monto'],
    })
    return resultado


@app.route('/api/reservar', methods=['POST'])
def api_reservar():
    try:
        sb = get_sb()
        data = request.json
        data.pop('cliente_id', None)      # la web no elige clienta: se reconoce por sus datos
        r = crear_reserva(sb, data, 'web', con_sena=True, rechazar_bloqueada=True)
        return jsonify({'success': True, 'turno_ids': r['turno_ids'], 'init_point': r.get('init_point')}
                       if r.get('init_point') else {'success': True, 'turno_ids': r['turno_ids']})
    except ReservaError as e:
        return jsonify({'error': str(e), **e.extra}), e.status
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cita', methods=['POST'])
@require_equipo
def api_cita():
    """Cita cargada por la recepción desde la agenda (con o sin seña)."""
    try:
        sb = get_sb()
        data = request.json or {}
        data['nombre']   = (data.get('nombre') or '').strip()
        data['telefono'] = (data.get('telefono') or '').strip()
        if not data['nombre'] or not data['telefono']:
            return jsonify({'error': 'Nombre y teléfono son obligatorios.'}), 400
        if not data.get('fecha') or not data.get('hora'):
            return jsonify({'error': 'Elegí fecha y horario.'}), 400
        data['acepto_politicas'] = False
        r = crear_reserva(sb, data, 'recepcion', con_sena=bool(data.get('con_sena', True)),
                          respetar_anticipacion=False)
        colab = sb.table('colaboradoras').select('nombre').eq('id', r['colaboradora_id']).limit(1).execute().data
        r['colaboradora'] = colab[0]['nombre'] if colab else ''
        for tid in r['turno_ids']:
            registrar_cambio(tid, 'creado', f"Creó la cita para el {data['fecha']} a las {data['hora']}"
                                            f" con {r['colaboradora']}")
        r.pop('init_point', None)
        r['hold_min'] = hold_min('recepcion')
        return jsonify({'success': True, **r})
    except ReservaError as e:
        return jsonify({'error': str(e), **e.extra}), e.status
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pagar/<token>')
def pagar_sena(token):
    """Link corto que se manda por WhatsApp: lleva al checkout o al resultado."""
    if not re.fullmatch(r'[0-9a-fA-F-]{36}', token):
        return redirect(url_for('reservar'))
    rows = tabla_pagos().select('*').eq('token', token).limit(1).execute().data
    if not rows:
        return redirect(url_for('reservar'))
    pago = rows[0]
    resultado = url_for('reservar_resultado', t=token)
    if pago['estado'] in ('aprobado', 'reembolsado') or not pago.get('mp_preference_id'):
        return redirect(resultado)
    turnos = turnos_de_pago(get_sb(), pago['id'])
    if not turnos or any(hold_vencido(t) for t in turnos):
        return redirect(resultado)
    try:
        return redirect(mp_request('GET', f"/checkout/preferences/{pago['mp_preference_id']}")['init_point'])
    except Exception as e:
        app.logger.error(f'Pagar {token}: {e}')
        return redirect(resultado)


# ── SEÑA — MERCADO PAGO ─────────────────────────────────────────────────────────

def crear_preferencia_sena(pago, cliente, servicios_nombres, expira_min):
    ahora = datetime.now(TZ_SALON)
    vence = ahora + timedelta(minutes=expira_min)
    url_resultado = f"{PUBLIC_BASE_URL}/reservar/resultado?t={pago['token']}"
    body = {
        'items': [{
            'id':          f"sena-{pago['id']}",
            'title':       'Seña cita Maru Nails',
            'description': ', '.join(servicios_nombres)[:250],
            'quantity':    1,
            'currency_id': 'MXN',
            'unit_price':  pago['monto'],
        }],
        'payer': {
            'name':    cliente.get('nombre', ''),
            'surname': cliente.get('apellido', ''),
        },
        'external_reference':   str(pago['id']),
        'notification_url':     MP_NOTIFICATION_URL,
        'back_urls':            {'success': url_resultado, 'failure': url_resultado, 'pending': url_resultado},
        'auto_return':          'approved',
        'binary_mode':          True,   # aprobado o rechazado al instante, sin pendientes
        'expires':              True,
        'expiration_date_from': ahora.isoformat(timespec='milliseconds'),
        'expiration_date_to':   vence.isoformat(timespec='milliseconds'),
        'payment_methods': {
            # Sin OXXO / efectivo / cajero: se acreditan tarde y no sirven para retener un horario
            'excluded_payment_types': [{'id': 'ticket'}, {'id': 'atm'}],
            'installments': 1,
        },
        'statement_descriptor': 'MARU NAILS',
    }
    if cliente.get('email'):
        body['payer']['email'] = cliente['email']
    return mp_request('POST', '/checkout/preferences', json=body)


def turnos_de_pago(sb, pago_id):
    return sb.table('turnos').select(
        'id,colaboradora_id,servicio_id,fecha,hora_inicio,hora_fin,estado,canal,created_at'
    ).eq('pago_sena_id', pago_id).order('hora_inicio').execute().data


def horario_sigue_libre(sb, turnos):
    """Para una seña pagada con la retención ya vencida: ¿nadie tomó el horario?"""
    if not turnos:
        return False
    if not any(hold_vencido(t) for t in turnos):
        return True
    primero = turnos[0]
    libres = calcular_slots(sb, primero['colaboradora_id'], primero['fecha'],
                            servicio_ids=[t['servicio_id'] for t in turnos],
                            respetar_anticipacion=False)
    return any(s['hora'] == primero['hora_inicio'][:5] for s in libres)


def procesar_pago(payment_id):
    """Sincroniza un pago de MP con la reserva. Idempotente: lo llaman el webhook y
    la página de resultado. Siempre consulta el pago a la API (no confía en el payload)."""
    sb = get_sb()
    p = mp_request('GET', f'/v1/payments/{payment_id}')
    ref = str(p.get('external_reference') or '')
    if not ref.isdigit():
        return None
    rows = tabla_pagos().select('*').eq('id', int(ref)).limit(1).execute().data
    if not rows:
        return None
    pago = rows[0]
    if pago['estado'] in ('aprobado', 'reembolsado'):
        return pago['estado']

    status = p.get('status')
    if status == 'approved':
        if p.get('currency_id') != 'MXN' or float(p.get('transaction_amount') or 0) < pago['monto']:
            tabla_pagos().update({
                'notas': f"Pago {payment_id} aprobado con monto inesperado — revisar",
            }).eq('id', pago['id']).execute()
            return pago['estado']

        turnos = turnos_de_pago(sb, pago['id'])
        tabla_pagos().update({
            'estado':        'aprobado',
            'mp_payment_id': str(payment_id),
            'pagado_at':     datetime.now(timezone.utc).isoformat(),
        }).eq('id', pago['id']).execute()

        if horario_sigue_libre(sb, turnos):
            sb.table('turnos').update({'estado': 'confirmado'}).eq(
                'pago_sena_id', pago['id']).eq('estado', 'esperando_pago').execute()
            return 'aprobado'

        # Pagó tarde y el horario ya lo tomó otra clienta: devolver automáticamente
        mp_request('POST', f'/v1/payments/{payment_id}/refunds', json={},
                   idempotency_key=f'refund-{payment_id}')
        tabla_pagos().update({
            'estado':         'reembolsado',
            'reembolsado_at': datetime.now(timezone.utc).isoformat(),
            'notas':          'Pagó con la reserva vencida y el horario ya estaba tomado. Devolución automática.',
        }).eq('id', pago['id']).execute()
        sb.table('turnos').update({'estado': 'cancelado_salon'}).eq('pago_sena_id', pago['id']).execute()
        return 'reembolsado'

    if status in ('rejected', 'cancelled') and pago['estado'] == 'pendiente':
        # El horario sigue retenido hasta que venza: puede reintentar con otra tarjeta
        tabla_pagos().update({'estado': 'rechazado'}).eq('id', pago['id']).execute()
        return 'rechazado'
    return pago['estado']


def firma_webhook_valida(data_id):
    """Valida x-signature de Mercado Pago (si hay secret configurado y viene el header)."""
    firma = request.headers.get('x-signature', '')
    if not MP_WEBHOOK_SECRET or not firma:
        return True  # igual es seguro: procesar_pago consulta el pago a la API con nuestro token
    partes = dict(p.strip().split('=', 1) for p in firma.split(',') if '=' in p)
    manifest = f"id:{str(data_id).lower()};request-id:{request.headers.get('x-request-id', '')};ts:{partes.get('ts', '')};"
    esperado = hmac.new(MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperado, partes.get('v1', ''))


@app.route('/api/mp/webhook', methods=['POST'])
def mp_webhook():
    body    = request.get_json(silent=True) or {}
    tipo    = request.args.get('type') or request.args.get('topic') or body.get('type') or body.get('topic')
    data_id = request.args.get('data.id') or (body.get('data') or {}).get('id') or request.args.get('id')
    if tipo != 'payment' or not data_id:
        return '', 200
    if not firma_webhook_valida(data_id):
        return '', 401
    try:
        procesar_pago(data_id)
    except Exception as e:
        # 500 → MP reintenta la notificación más tarde
        app.logger.error(f'Webhook MP {data_id}: {e}')
        return '', 500
    return '', 200


@app.route('/reservar/resultado')
def reservar_resultado():
    sb    = get_sb()
    token = request.args.get('t', '')
    if not re.fullmatch(r'[0-9a-fA-F-]{36}', token):
        return redirect(url_for('reservar'))
    rows = tabla_pagos().select('*').eq('token', token).limit(1).execute().data
    if not rows:
        return redirect(url_for('reservar'))
    pago = rows[0]

    # Por si el webhook todavía no llegó
    payment_id = request.args.get('payment_id') or request.args.get('collection_id')
    if payment_id and payment_id.isdigit() and pago['estado'] not in ('aprobado', 'reembolsado'):
        try:
            procesar_pago(payment_id)
            pago = tabla_pagos().select('*').eq('id', pago['id']).limit(1).execute().data[0]
        except Exception as e:
            app.logger.error(f'Resultado MP {payment_id}: {e}')

    turnos = turnos_de_pago(sb, pago['id'])
    serv_ids = list({t['servicio_id'] for t in turnos})
    nombres = {s['id']: s['nombre'] for s in
               sb.table('servicios').select('id,nombre').in_('id', serv_ids).execute().data} if serv_ids else {}
    cliente = sb.table('clientes_reservas').select('nombre').eq('id', pago['cliente_id']).limit(1).execute().data

    reintento_url = None
    if pago['estado'] in ('pendiente', 'rechazado') and turnos and not any(hold_vencido(t) for t in turnos) \
            and pago.get('mp_preference_id'):
        try:
            reintento_url = mp_request('GET', f"/checkout/preferences/{pago['mp_preference_id']}")['init_point']
        except Exception:
            pass

    return render_template('reservar_resultado.html',
                           estado=pago['estado'],
                           monto=pago['monto'],
                           nombre=(cliente[0]['nombre'] if cliente else ''),
                           servicios=[nombres.get(t['servicio_id'], '') for t in turnos],
                           fecha=turnos[0]['fecha'] if turnos else None,
                           hora=turnos[0]['hora_inicio'][:5] if turnos else None,
                           reintento_url=reintento_url)


@app.route('/api/pago-sena/<int:pid>/reembolso', methods=['POST'])
@require_admin
def api_reembolso_sena(pid):
    try:
        sb = get_sb()
        rows = tabla_pagos().select('*').eq('id', pid).limit(1).execute().data
        if not rows:
            return jsonify({'error': 'Seña no encontrada'}), 404
        pago = rows[0]
        if pago['estado'] == 'reembolsado':
            return jsonify({'success': True})
        if pago['estado'] != 'aprobado' or not pago.get('mp_payment_id'):
            return jsonify({'error': 'Esta seña no está pagada'}), 400
        mp_request('POST', f"/v1/payments/{pago['mp_payment_id']}/refunds", json={},
                   idempotency_key=f"refund-{pago['mp_payment_id']}")
        tabla_pagos().update({
            'estado':         'reembolsado',
            'reembolsado_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', pid).execute()
        return jsonify({'success': True})
    except httpx.HTTPStatusError as e:
        return jsonify({'error': f'Mercado Pago rechazó la devolución: {e.response.text[:200]}'}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── SISTEMA DE TURNOS — INTERNO ─────────────────────────────────────────────────

ESTADOS_TURNO = {
    'esperando_pago', 'pendiente', 'confirmado', 'en_espera', 'llegó', 'en_servicio',
    'finalizado', 'cancelado_cliente', 'cancelado_salon', 'no_show', 'reprogramado',
}
ESTACION_LABEL = {'manicura': 'mesa de manicure', 'pedicura': 'tarima de pedicure', 'estetica': 'camilla'}


def _min(h):
    """'HH:MM' o 'HH:MM:SS' → minutos desde las 00:00."""
    return int(h[:2]) * 60 + int(h[3:5])


def _hhmm(m):
    return f'{m // 60:02d}:{m % 60:02d}'


def cadena_de_turno(turnos_dia, turno):
    """Los servicios de una misma cita: misma clienta, día y colaboradora, encadenados
    (cada uno empieza cuando termina el anterior). Incluye al turno; ordenados por hora."""
    if not turno_ocupa(turno):
        return [turno]
    mismos = sorted(
        [t for t in turnos_dia
         if t['cliente_id'] == turno['cliente_id'] and t['colaboradora_id'] == turno['colaboradora_id']
         and t['fecha'] == turno['fecha'] and turno_ocupa(t)],
        key=lambda t: t['hora_inicio'])
    idx = next((i for i, t in enumerate(mismos) if t['id'] == turno['id']), None)
    if idx is None:
        return [turno]
    ini = fin = idx
    while ini > 0 and mismos[ini - 1]['hora_fin'][:5] == mismos[ini]['hora_inicio'][:5]:
        ini -= 1
    while fin < len(mismos) - 1 and mismos[fin]['hora_fin'][:5] == mismos[fin + 1]['hora_inicio'][:5]:
        fin += 1
    return mismos[ini:fin + 1]


def choques_movimiento(movidos, otros, colab_nombre, horario, bloqueada):
    """Avisos al mover turnos a una colaboradora/día. No bloquean: la UI pregunta "¿mover igual?".
    movidos: [{hora_inicio, hora_fin, tipo_estacion}] en la posición nueva (minutos).
    otros:   turnos que ocupan ese día, sin los movidos
             [{colaboradora_id, hora_inicio, hora_fin, tipo_estacion, cliente, es_de_colab}].
    horario: [(ini, fin)] en minutos de la colaboradora ese día de la semana ([] = no trabaja).
    bloqueada: tiene el día bloqueado."""
    avisos = []
    if bloqueada:
        avisos.append(f'{colab_nombre} tiene el día bloqueado.')
    elif not horario:
        avisos.append(f'{colab_nombre} no trabaja ese día.')
    else:
        ini, fin = movidos[0]['hora_inicio'], movidos[-1]['hora_fin']
        if not any(h_ini <= ini and fin <= h_fin for h_ini, h_fin in horario):
            rangos = ', '.join(f'{_hhmm(a)}–{_hhmm(b)}' for a, b in horario)
            avisos.append(f'Queda fuera del horario de {colab_nombre} ({rangos}).')
    for m in movidos:
        for o in otros:
            if o['es_de_colab'] and o['hora_inicio'] < m['hora_fin'] and o['hora_fin'] > m['hora_inicio']:
                aviso = (f"{colab_nombre} ya tiene a {o['cliente']} de "
                         f"{_hhmm(o['hora_inicio'])} a {_hhmm(o['hora_fin'])}.")
                if aviso not in avisos:
                    avisos.append(aviso)
        est = m.get('tipo_estacion')
        if est in CAPACIDAD_ESTACIONES:
            ocupadas = sum(1 for o in otros if o['tipo_estacion'] == est
                           and o['hora_inicio'] < m['hora_fin'] and o['hora_fin'] > m['hora_inicio'])
            if ocupadas >= CAPACIDAD_ESTACIONES[est]:
                avisos.append(f"No queda {ESTACION_LABEL.get(est, est)} libre de "
                              f"{_hhmm(m['hora_inicio'])} a {_hhmm(m['hora_fin'])}.")
    return avisos


def registrar_cambio(turno_id, accion, detalle, antes=None, despues=None):
    """Deja constancia de quién hizo qué. Nunca rompe la operación principal."""
    autor, autor_id = autor_actual()
    try:
        sb_service().table('turno_cambios').insert({
            'turno_id': turno_id, 'autor': autor, 'autor_colaboradora_id': autor_id,
            'accion': accion, 'detalle': detalle, 'antes': antes, 'despues': despues,
        }).execute()
    except Exception as e:
        app.logger.error(f'turno_cambios {turno_id}: {e}')


def _fecha_corta(iso):
    d = datetime.strptime(iso, '%Y-%m-%d')
    return f"{['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'][d.weekday()]} {d.day} {MESES_ES[d.month]}"


@app.route('/agenda')
@require_equipo
def agenda():
    return render_template('agenda.html', sena_activa=SENA_ACTIVA, sena_mxn=SENA_MXN,
                           hold_recepcion_min=hold_min('recepcion'),
                           es_admin=es_admin(), equipo_id=session.get('equipo_id'),
                           equipo_nombre=session.get('equipo_nombre', ''))


@app.route('/api/agenda')
@require_equipo
def api_agenda():
    try:
        sb = get_sb()
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        fecha = request.args.get('fecha', ahora_salon().date().isoformat())
        query = sb.table('turnos').select(
            'id,fecha,hora_inicio,hora_fin,estado,precio,notas,canal,created_at,pago_sena_id,'
            'cliente_id,colaboradora_id,servicio_id,'
            'clientes_reservas(id,nombre,apellido,telefono),'
            'colaboradoras(nombre),'
            'servicios(nombre,duracion_min,categoria)'
        )
        if desde and hasta:
            query = query.gte('fecha', desde).lte('fecha', hasta)
        else:
            query = query.eq('fecha', fecha)
        turnos = [t for t in query.order('fecha').order('hora_inicio').execute().data
                  if not hold_vencido(t)]

        # Señas: query aparte y merge en código
        pago_ids = list({t['pago_sena_id'] for t in turnos if t.get('pago_sena_id')})
        pagos = {p['id']: p for p in tabla_pagos().select(
            'id,monto,estado,token').in_('id', pago_ids).execute().data} if pago_ids and SUPABASE_SERVICE_KEY else {}
        for p in pagos.values():
            p['url_pago'] = url_pago(p.pop('token'))
        for t in turnos:
            t['sena'] = pagos.get(t.get('pago_sena_id'))
        return jsonify(turnos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cliente/<int:cid>/historial')
@require_equipo
def api_cliente_historial(cid):
    try:
        sb = get_sb()
        cliente = sb.table('clientes_reservas').select('*').eq('id', cid).limit(1).execute()
        if not cliente.data:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        turnos = sb.table('turnos').select(
            'id,fecha,hora_inicio,hora_fin,estado,precio,notas,canal,created_at,'
            'colaboradoras(nombre),servicios(nombre)'
        ).eq('cliente_id', cid).order('fecha', desc=True).execute()
        return jsonify({'cliente': {**cliente.data[0], 'ficha_key': clave_clienta(cliente.data[0])},
                        'turnos': [t for t in turnos.data if not hold_vencido(t)]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/clientas')
@require_equipo
def api_clientas():
    """Directorio del buscador de clientas de la agenda (nueva cita / walk-in)."""
    try:
        sb = get_sb()
        tel_fichas = {r['key']: r.get('telefono') for r in fetch_all(sb, 'clientes_info', 'key,telefono')}
        return jsonify(directorio_clientas(
            fetch_all(sb, 'clientes_reservas', 'id,nombre,apellido,telefono'),
            fetch_all(sb, 'cortes', 'cliente,fecha,total_mxn,propina_mxn,staff,servicio'),
            tel_fichas))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/turno/<int:tid>/estado', methods=['POST'])
@require_equipo
def cambiar_estado_turno(tid):
    try:
        sb = get_sb()
        estado = (request.json or {}).get('estado')
        if estado not in ESTADOS_TURNO:
            return jsonify({'error': 'Estado inválido'}), 400
        prev = sb.table('turnos').select('estado').eq('id', tid).limit(1).execute().data
        if not prev:
            return jsonify({'error': 'Turno no encontrado'}), 404
        sb.table('turnos').update({'estado': estado}).eq('id', tid).execute()
        if prev[0]['estado'] != estado:
            registrar_cambio(tid, 'estado', f"Cambió el estado de {prev[0]['estado']} a {estado}",
                             {'estado': prev[0]['estado']}, {'estado': estado})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/turno/<int:tid>', methods=['PUT'])
@require_equipo
def api_mover_turno(tid):
    """Mover (fecha, hora, colaboradora) o editar (servicio, notas) un turno.
    mover_grupo: arrastra también los otros servicios encadenados de la misma cita.
    Si hay choques y no viene forzar → 409 con los avisos para que la UI pregunte."""
    try:
        sb = get_sb()
        d = request.json or {}
        cols = 'id,cliente_id,colaboradora_id,servicio_id,fecha,hora_inicio,hora_fin,estado,canal,created_at'
        rows = sb.table('turnos').select(cols).eq('id', tid).limit(1).execute().data
        if not rows:
            return jsonify({'error': 'Turno no encontrado'}), 404
        t = rows[0]

        fecha = d.get('fecha') or t['fecha']
        hora  = (d.get('hora_inicio') or t['hora_inicio'])[:5]
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', fecha) or not re.fullmatch(r'\d{2}:\d{2}', hora):
            return jsonify({'error': 'Fecha u hora inválida'}), 400
        colab_id    = int(d.get('colaboradora_id') or t['colaboradora_id'] or 0)
        servicio_id = int(d.get('servicio_id') or t['servicio_id'])
        if not colab_id:
            return jsonify({'error': 'Elegí la colaboradora'}), 400

        colab = sb.table('colaboradoras').select('id,nombre').eq('id', colab_id).limit(1).execute().data
        if not colab:
            return jsonify({'error': 'Colaboradora no encontrada'}), 400
        colab_nombre = colab[0]['nombre']

        grupo = [t]
        if d.get('mover_grupo'):
            dia_orig = sb.table('turnos').select(cols).eq('fecha', t['fecha']).eq(
                'cliente_id', t['cliente_id']).execute().data
            grupo = cadena_de_turno(dia_orig, t)

        serv_ids = list({g['servicio_id'] for g in grupo} | {servicio_id})
        servs = {s['id']: s for s in sb.table('servicios').select(
            'id,nombre,duracion_min,precio_desde,categoria').in_('id', serv_ids).execute().data}
        if servicio_id not in servs:
            return jsonify({'error': 'Servicio no encontrado'}), 400

        # Se reubican en secuencia desde el nuevo inicio, conservando la duración de cada uno.
        # Si cambia el servicio, ese turno toma la duración del nuevo y los siguientes se corren.
        cursor = _min(hora) - (_min(t['hora_inicio']) - _min(grupo[0]['hora_inicio']))
        nuevos = []
        for g in grupo:
            sid = servicio_id if g['id'] == tid else g['servicio_id']
            dur = (servs[sid]['duracion_min'] if sid != g['servicio_id']
                   else _min(g['hora_fin']) - _min(g['hora_inicio']))
            nuevos.append({'turno': g, 'servicio_id': sid, 'hora_inicio': cursor, 'hora_fin': cursor + dur,
                           'tipo_estacion': estacion_de_categoria(servs[sid].get('categoria'))})
            cursor += dur
        if nuevos[0]['hora_inicio'] < 0 or nuevos[-1]['hora_fin'] > 24 * 60:
            return jsonify({'error': 'El horario se sale del día'}), 400

        if not d.get('forzar'):
            ids = {g['id'] for g in grupo}
            dia_dest = sb.table('turnos').select(
                'id,colaboradora_id,hora_inicio,hora_fin,estado,canal,created_at,'
                'clientes_reservas(nombre,apellido),servicios(categoria)'
            ).eq('fecha', fecha).execute().data
            otros = []
            for o in dia_dest:
                if o['id'] in ids or not turno_ocupa(o):
                    continue
                cli = o.get('clientes_reservas') or {}
                otros.append({
                    'es_de_colab':   o['colaboradora_id'] == colab_id,
                    'hora_inicio':   _min(o['hora_inicio']),
                    'hora_fin':      _min(o['hora_fin']),
                    'tipo_estacion': estacion_de_categoria((o.get('servicios') or {}).get('categoria')),
                    'cliente':       f"{cli.get('nombre') or ''} {cli.get('apellido') or ''}".strip() or 'otra clienta',
                })
            dia_semana = datetime.strptime(fecha, '%Y-%m-%d').weekday()
            horario = [(_min(h['hora_inicio']), _min(h['hora_fin'])) for h in sb.table('disponibilidad').select(
                'hora_inicio,hora_fin').eq('colaboradora_id', colab_id).eq('dia_semana', dia_semana).execute().data]
            bloqueada = bool(sb.table('bloqueos').select('id').eq('colaboradora_id', colab_id).eq(
                'fecha', fecha).eq('todo_el_dia', True).execute().data)
            choques = choques_movimiento(nuevos, otros, colab_nombre, horario, bloqueada)
            if choques:
                return jsonify({'error': 'Hay choques', 'conflictos': choques}), 409

        nombres_colab = {colab_id: colab_nombre}
        viejos_ids = {g['colaboradora_id'] for g in grupo if g['colaboradora_id'] and g['colaboradora_id'] != colab_id}
        if viejos_ids:
            nombres_colab.update({c['id']: c['nombre'] for c in sb.table('colaboradoras').select(
                'id,nombre').in_('id', list(viejos_ids)).execute().data})

        for n in nuevos:
            g = n['turno']
            cambios = {'fecha': fecha, 'hora_inicio': _hhmm(n['hora_inicio']),
                       'hora_fin': _hhmm(n['hora_fin']), 'colaboradora_id': colab_id}
            if n['servicio_id'] != g['servicio_id']:
                cambios['servicio_id'] = n['servicio_id']
                cambios['precio'] = servs[n['servicio_id']]['precio_desde']
            if g['id'] == tid and 'notas' in d:
                cambios['notas'] = (d.get('notas') or '').strip()
            antes = {'fecha': g['fecha'], 'hora_inicio': g['hora_inicio'][:5],
                     'colaboradora_id': g['colaboradora_id'], 'servicio_id': g['servicio_id']}
            despues = {'fecha': fecha, 'hora_inicio': cambios['hora_inicio'],
                       'colaboradora_id': colab_id, 'servicio_id': n['servicio_id']}
            sb.table('turnos').update(cambios).eq('id', g['id']).execute()

            partes = []
            if antes['fecha'] != fecha or antes['hora_inicio'] != despues['hora_inicio'] or antes['colaboradora_id'] != colab_id:
                partes.append(
                    f"Movió de {_fecha_corta(antes['fecha'])} {antes['hora_inicio']} "
                    f"({nombres_colab.get(antes['colaboradora_id'], 'sin asignar')}) a "
                    f"{_fecha_corta(fecha)} {despues['hora_inicio']} ({colab_nombre})")
            if 'servicio_id' in cambios:
                partes.append(f"Cambió el servicio a {servs[n['servicio_id']]['nombre']}")
            if 'notas' in cambios:
                partes.append('Editó las notas')
            if partes:
                registrar_cambio(g['id'], 'movido' if partes[0].startswith('Movió') else 'editado',
                                 '. '.join(partes), antes, despues)

        cli = sb.table('clientes_reservas').select('nombre,telefono').eq('id', t['cliente_id']).limit(1).execute().data
        return jsonify({
            'success':      True,
            'turno_ids':    [n['turno']['id'] for n in nuevos],
            'fecha':        fecha,
            'hora':         _hhmm(nuevos[0]['hora_inicio']),
            'colaboradora': colab_nombre,
            'servicios':    [servs[n['servicio_id']]['nombre'] for n in nuevos],
            'cliente':      cli[0] if cli else None,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/turno/<int:tid>/cambios')
@require_equipo
def api_turno_cambios(tid):
    try:
        rows = sb_service().table('turno_cambios').select('autor,accion,detalle,created_at').eq(
            'turno_id', tid).order('created_at', desc=True).limit(20).execute().data
        return jsonify(rows)
    except Exception:
        return jsonify([])


@app.route('/api/walkin', methods=['POST'])
@require_equipo
def api_walkin():
    try:
        sb = get_sb()
        data = request.json
        nombre    = (data.get('nombre') or 'Walk in').strip() or 'Walk in'
        telefono  = (data.get('telefono') or '').strip()
        serv_id   = data.get('servicio_id')
        colab_id  = data.get('colaboradora_id')
        hora_ini  = data.get('hora') or ahora_salon().strftime('%H:%M')
        notas     = data.get('notas', '').strip()
        fecha_hoy = ahora_salon().date().isoformat()

        if not serv_id or not colab_id:
            return jsonify({'error': 'Servicio y colaboradora son obligatorios'}), 400

        servicio = sb.table('servicios').select('precio_desde,duracion_min,nombre').eq(
            'id', serv_id).limit(1).execute()
        if not servicio.data:
            return jsonify({'error': 'Servicio no encontrado'}), 400
        duracion = servicio.data[0]['duracion_min']
        hora_fin = (datetime.strptime(hora_ini, '%H:%M') + timedelta(minutes=duracion)).strftime('%H:%M')

        cliente_id = clienta_para_reserva(sb, {'nombre': nombre, 'telefono': telefono,
                                               'cliente_id': data.get('cliente_id')})

        turno = sb.table('turnos').insert({
            'cliente_id':     cliente_id,
            'colaboradora_id': int(colab_id),
            'servicio_id':    int(serv_id),
            'fecha':          fecha_hoy,
            'hora_inicio':    hora_ini,
            'hora_fin':       hora_fin,
            'estado':         'llegó',
            'precio':         servicio.data[0]['precio_desde'],
            'notas':          notas,
            'canal':          'walk-in',
        }).execute()

        registrar_cambio(turno.data[0]['id'], 'creado', f'Registró el walk-in a las {hora_ini}')
        return jsonify({'success': True, 'turno_id': turno.data[0]['id']})
    except ReservaError as e:
        return jsonify({'error': str(e)}), e.status
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ADMIN PANEL ────────────────────────────────────────────────────────────────

@app.route('/admin')
@require_admin
def admin():
    return render_template('admin.html')


# ─ Servicios ─
@app.route('/admin/api/servicios')
@require_admin
def admin_api_servicios():
    sb = get_sb()
    data = sb.table('servicios').select('*').order('categoria').order('orden').execute()
    return jsonify(data.data)


@app.route('/admin/api/servicio', methods=['POST'])
@require_admin
def admin_crear_servicio():
    try:
        sb = get_sb()
        d = request.json
        row = {
            'nombre':       d['nombre'].strip(),
            'categoria':    d['categoria'].strip(),
            'descripcion':  d.get('descripcion', '').strip(),
            'precio_desde': int(d['precio_desde']),
            'precio_hasta': int(d['precio_hasta']) if d.get('precio_hasta') else None,
            'duracion_min': int(d['duracion_min']),
            'activo':       True,
            'orden':        int(d.get('orden', 0)),
        }
        res = sb.table('servicios').insert(row).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/servicio/<int:sid>', methods=['PUT'])
@require_admin
def admin_editar_servicio(sid):
    try:
        sb = get_sb()
        d = request.json
        row = {
            'nombre':       d['nombre'].strip(),
            'categoria':    d['categoria'].strip(),
            'descripcion':  d.get('descripcion', '').strip(),
            'precio_desde': int(d['precio_desde']),
            'precio_hasta': int(d['precio_hasta']) if d.get('precio_hasta') else None,
            'duracion_min': int(d['duracion_min']),
            'orden':        int(d.get('orden', 0)),
        }
        res = sb.table('servicios').update(row).eq('id', sid).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/servicio/<int:sid>/toggle', methods=['POST'])
@require_admin
def admin_toggle_servicio(sid):
    try:
        sb = get_sb()
        cur = sb.table('servicios').select('activo').eq('id', sid).limit(1).execute()
        nuevo = not cur.data[0]['activo']
        sb.table('servicios').update({'activo': nuevo}).eq('id', sid).execute()
        return jsonify({'activo': nuevo})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─ Colaboradoras ─
@app.route('/admin/api/colaboradoras-full')
@require_admin
def admin_api_colaboradoras_full():
    try:
        sb = get_sb()
        colabs = sb.table('colaboradoras').select('*').order('nombre').execute()
        try:
            con_pin = {r['colaboradora_id'] for r in
                       sb_service().table('equipo_acceso').select('colaboradora_id').execute().data}
        except Exception:
            con_pin = set()
        result = []
        for c in colabs.data:
            cs = sb.table('colaboradora_servicios').select('servicio_id').eq(
                'colaboradora_id', c['id']).execute()
            c['servicio_ids'] = [r['servicio_id'] for r in cs.data]
            c['tiene_pin'] = c['id'] in con_pin
            result.append(c)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/colaboradora/<int:cid>/pin', methods=['PUT', 'DELETE'])
@require_admin
def admin_pin_colaboradora(cid):
    """Carga/cambia el PIN de acceso a la agenda (PUT) o le quita el acceso (DELETE).
    Cambiarlo o quitarlo cierra la sesión que tenga abierta (cambia updated_at)."""
    try:
        tabla = sb_service().table('equipo_acceso')
        if request.method == 'DELETE':
            tabla.delete().eq('colaboradora_id', cid).execute()
            return jsonify({'success': True})
        pin = str((request.json or {}).get('pin', ''))
        if not re.fullmatch(r'\d{4}', pin):
            return jsonify({'error': 'El PIN tiene que ser de 4 números.'}), 400
        tabla.upsert({
            'colaboradora_id':   cid,
            'pin_hash':          generate_password_hash(pin),
            'intentos_fallidos': 0,
            'bloqueado_hasta':   None,
            'updated_at':        datetime.now(timezone.utc).isoformat(),
        }).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/colaboradora', methods=['POST'])
@require_admin
def admin_crear_colaboradora():
    try:
        sb = get_sb()
        d = request.json
        row = {
            'nombre':   d['nombre'].strip().upper(),
            'rol':      d.get('rol', '').strip(),
            'comision': float(d.get('comision', 0.4)),
            'activa':   True,
        }
        res = sb.table('colaboradoras').insert(row).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/colaboradora/<int:cid>', methods=['PUT'])
@require_admin
def admin_editar_colaboradora(cid):
    try:
        sb = get_sb()
        d = request.json
        row = {
            'nombre':   d['nombre'].strip().upper(),
            'rol':      d.get('rol', '').strip(),
            'comision': float(d.get('comision', 0.4)),
        }
        res = sb.table('colaboradoras').update(row).eq('id', cid).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/colaboradora/<int:cid>/toggle', methods=['POST'])
@require_admin
def admin_toggle_colaboradora(cid):
    try:
        sb = get_sb()
        cur = sb.table('colaboradoras').select('activa').eq('id', cid).limit(1).execute()
        nuevo = not cur.data[0]['activa']
        sb.table('colaboradoras').update({'activa': nuevo}).eq('id', cid).execute()
        if not nuevo:
            # Si se va del equipo, pierde el acceso a la agenda
            try:
                sb_service().table('equipo_acceso').delete().eq('colaboradora_id', cid).execute()
            except Exception as e:
                app.logger.error(f'equipo_acceso {cid}: {e}')
        return jsonify({'activa': nuevo})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/colaboradora/<int:cid>/servicios', methods=['PUT'])
@require_admin
def admin_servicios_colaboradora(cid):
    try:
        sb = get_sb()
        servicio_ids = request.json.get('servicio_ids', [])
        sb.table('colaboradora_servicios').delete().eq('colaboradora_id', cid).execute()
        if servicio_ids:
            rows = [{'colaboradora_id': cid, 'servicio_id': int(sid)} for sid in servicio_ids]
            sb.table('colaboradora_servicios').insert(rows).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─ Bloqueos por fecha (público — para el calendario de reserva) ─
@app.route('/api/bloqueos/<int:cid>')
def api_bloqueos_colab(cid):
    try:
        sb = get_sb()
        mes = request.args.get('mes')  # YYYY-MM
        q = sb.table('bloqueos').select('id,fecha,motivo,todo_el_dia').eq(
            'colaboradora_id', cid).eq('todo_el_dia', True)
        if mes:
            q = q.gte('fecha', f'{mes}-01').lte('fecha', f'{mes}-31')
        return jsonify(q.execute().data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/bloqueos', methods=['POST'])
@require_admin
def admin_create_bloqueo():
    try:
        sb = get_sb()
        data = request.json
        result = sb.table('bloqueos').insert({
            'colaboradora_id': data['colaboradora_id'],
            'fecha': data['fecha'],
            'motivo': data.get('motivo', ''),
            'todo_el_dia': True,
        }).execute()
        return jsonify({'success': True, 'id': result.data[0]['id']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/bloqueos/<int:bid>', methods=['DELETE'])
@require_admin
def admin_delete_bloqueo(bid):
    try:
        sb = get_sb()
        sb.table('bloqueos').delete().eq('id', bid).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ─ Disponibilidad ─
@app.route('/admin/api/disponibilidad/<int:cid>')
@require_admin
def admin_get_disponibilidad(cid):
    try:
        sb = get_sb()
        data = sb.table('disponibilidad').select('*').eq(
            'colaboradora_id', cid).order('dia_semana').execute()
        sched = {}
        for row in data.data:
            sched[str(row['dia_semana'])] = {
                'hora_inicio': str(row['hora_inicio'])[:5],
                'hora_fin':    str(row['hora_fin'])[:5],
            }
        return jsonify(sched)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/api/disponibilidad/<int:cid>', methods=['PUT'])
@require_admin
def admin_set_disponibilidad(cid):
    try:
        sb = get_sb()
        dias = request.json
        sb.table('disponibilidad').delete().eq('colaboradora_id', cid).execute()
        rows = []
        for dia_str, horario in dias.items():
            if horario:
                rows.append({
                    'colaboradora_id': cid,
                    'dia_semana':      int(dia_str),
                    'hora_inicio':     horario['hora_inicio'],
                    'hora_fin':        horario['hora_fin'],
                })
        if rows:
            sb.table('disponibilidad').insert(rows).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── TURNOS — ESTADÍSTICAS ─────────────────────────────────────────────────────
@app.route('/api/turnos/reportes')
@require_admin
def api_turnos_reportes():
    try:
        sb    = get_sb()
        desde = request.args.get('desde', date.today().strftime('%Y-%m-01'))
        hasta = request.args.get('hasta', date.today().isoformat())

        turnos = sb.table('turnos').select(
            'id,fecha,hora_inicio,estado,precio,canal,created_at,'
            'clientes_reservas(id),'
            'colaboradoras(nombre),'
            'servicios(nombre)'
        ).gte('fecha', desde).lte('fecha', hasta).execute().data
        turnos = [t for t in turnos if not hold_vencido(t)]

        por_estado   = defaultdict(int)
        por_servicio = defaultdict(int)
        por_colab    = defaultdict(int)
        por_hora     = defaultdict(int)
        cli_ids      = []
        facturado    = 0

        for t in turnos:
            estado = t.get('estado') or 'pendiente'
            por_estado[estado] += 1
            if t.get('servicios') and t['servicios'].get('nombre'):
                por_servicio[t['servicios']['nombre']] += 1
            if t.get('colaboradoras') and t['colaboradoras'].get('nombre'):
                por_colab[t['colaboradoras']['nombre']] += 1
            hora = (t.get('hora_inicio') or '')[:2]
            if hora.isdigit():
                por_hora[hora] += 1
            if t.get('clientes_reservas') and t['clientes_reservas'].get('id'):
                cli_ids.append(t['clientes_reservas']['id'])
            if estado == 'finalizado':
                facturado += (t.get('precio') or 0)

        unique_clis = list(set(cli_ids))
        nuevos_count = 0
        recurrentes_count = 0
        if unique_clis:
            prev_rows = sb.table('turnos').select('cliente_id').lt('fecha', desde).execute().data
            previo_ids = {r['cliente_id'] for r in prev_rows if r.get('cliente_id')}
            recurrentes_count = sum(1 for cid in unique_clis if cid in previo_ids)
            nuevos_count = len(unique_clis) - recurrentes_count

        return jsonify({
            'total':        len(turnos),
            'facturado':    facturado,
            'por_estado':   dict(sorted(por_estado.items(), key=lambda x: x[1], reverse=True)),
            'por_servicio': dict(sorted(por_servicio.items(), key=lambda x: x[1], reverse=True)[:10]),
            'por_colab':    dict(sorted(por_colab.items(), key=lambda x: x[1], reverse=True)),
            'por_hora':     dict(sorted(por_hora.items())),
            'clientes': {
                'total_unicos': len(unique_clis),
                'nuevos':       nuevos_count,
                'recurrentes':  recurrentes_count,
            },
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── LISTA DE ESPERA ─────────────────────────────────────────────────────────────
@app.route('/api/lista-espera')
def api_lista_espera():
    try:
        sb   = get_sb()
        data = sb.table('lista_espera').select(
            '*,servicios(nombre),colaboradoras(nombre)'
        ).eq('estado', 'activo').order('created_at').execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lista-espera', methods=['POST'])
def api_agregar_espera():
    try:
        sb       = get_sb()
        d        = request.json
        nombre   = (d.get('nombre') or '').strip()
        telefono = (d.get('telefono') or '').strip()
        if not nombre and not telefono:
            return jsonify({'error': 'Nombre o teléfono son obligatorios'}), 400

        ya = buscar_clienta(fetch_all(sb, 'clientes_reservas', 'id,nombre,apellido,telefono,email'),
                            nombre, telefono=telefono)
        cliente_id = ya['id'] if ya else None

        row = {
            'nombre':          nombre or None,
            'telefono':        telefono or None,
            'cliente_id':      cliente_id,
            'servicio_id':     int(d['servicio_id']) if d.get('servicio_id') else None,
            'colaboradora_id': int(d['colaboradora_id']) if d.get('colaboradora_id') else None,
            'fecha_preferida': d.get('fecha_preferida') or None,
            'hora_preferida':  d.get('hora_preferida') or None,
            'notas':           d.get('notas', '').strip() or None,
            'estado':          'activo',
        }
        res = sb.table('lista_espera').insert(row).execute()
        return jsonify({'success': True, 'id': res.data[0]['id']})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/lista-espera/<int:eid>/estado', methods=['POST'])
@require_equipo
def api_estado_espera(eid):
    try:
        sb    = get_sb()
        estado = request.json.get('estado')
        sb.table('lista_espera').update({'estado': estado}).eq('id', eid).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── CLIENTE — PERFIL (alergias / bloqueo) ─────────────────────────────────────
@app.route('/api/cliente/<int:cid>/perfil', methods=['POST'])
@require_equipo
def api_actualizar_perfil_cliente(cid):
    try:
        sb  = get_sb()
        d   = request.json
        upd = {}
        if 'alergias' in d:
            upd['alergias'] = d['alergias'].strip() or None
        if 'bloqueado' in d:
            upd['bloqueado'] = bool(d['bloqueado'])
        if 'motivo_bloqueo' in d:
            upd['motivo_bloqueo'] = d['motivo_bloqueo'].strip() or None
        if upd:
            sb.table('clientes_reservas').update(upd).eq('id', cid).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── ADMIN — CLIENTES ──────────────────────────────────────────────────────────
@app.route('/admin/api/clientes')
@require_admin
def admin_api_clientes():
    try:
        sb       = get_sb()
        clientes = sb.table('clientes_reservas').select(
            'id,nombre,apellido,telefono,bloqueado,motivo_bloqueo,alergias,created_at'
        ).order('nombre').execute().data

        noshows  = sb.table('turnos').select('cliente_id').eq('estado', 'no_show').execute().data
        ns_count = defaultdict(int)
        for row in noshows:
            if row.get('cliente_id'):
                ns_count[row['cliente_id']] += 1
        for c in clientes:
            c['no_shows'] = ns_count.get(c['id'], 0)

        return jsonify(clientes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── SALÓN — PÁGINA PÚBLICA ────────────────────────────────────────────────────
@app.route('/')
@app.route('/salon')
def salon():
    servicios, colabs = [], []
    try:
        sb = get_sb()
        servicios = sb.table('servicios').select(
            'nombre,categoria,precio_desde,precio_hasta,duracion_min,descripcion'
        ).eq('activo', True).order('categoria').order('orden').execute().data
        colabs = sb.table('colaboradoras').select(
            'nombre,rol,foto_url'
        ).eq('activa', True).order('nombre').execute().data
    except Exception:
        pass
    return render_template('salon.html', servicios=servicios, colabs=colabs)


if __name__ == '__main__':
    print('\n  MaruNails corriendo en http://localhost:5000\n')
    app.run(debug=False, host='0.0.0.0', port=5000)
