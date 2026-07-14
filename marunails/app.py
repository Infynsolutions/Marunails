from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from datetime import datetime, date, timedelta
from collections import defaultdict
import os
import base64
import anthropic as _anthropic

from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'marunails_secret_2026')

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://dbhxrboacqppximbcokz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRiaHhyYm9hY3FwcHhpbWJjb2t6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0Mjg1NDMsImV4cCI6MjA5OTAwNDU0M30.fcVl9hwRTACJrp4BH7CZdj5ZzPa7-VaAqJlUdHH-NKs')

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Marunailstulum123')

TC_USD = 17

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


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = False
            return redirect(url_for('index'))
        error = 'Contraseña incorrecta'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('salon'))


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route('/')
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


# ── CLIENTES ────────────────────────────────────────────────────────────────────
@app.route('/clientes')
@require_admin
def clientes():
    resumen = None
    try:
        sb = get_sb()
        cortes = fetch_all(sb, 'cortes', 'cliente,fecha,total_mxn,propina_mxn,staff,servicio')
        resumen = resumen_clientes(cortes)
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

    except Exception as e:
        flash(f'Error cargando el cliente: {e}', 'error')

    if cli is None:
        flash('Cliente no encontrado.', 'error')
        return redirect(url_for('clientes'))

    return render_template('cliente.html', cli=cli, historial=historial, info=info)


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
    try:
        sb = get_sb()
        cortes_all = fetch_all(sb, 'cortes', 'fecha,mes,total_mxn,medio_pago')
        gastos_all = fetch_all(sb, 'gastos', 'fecha,mes,importe_mxn,medio_pago')

        def _empty():
            return {'ing_caja': 0, 'ing_banco': 0, 'ing_total': 0,
                    'gasto_caja': 0, 'gasto_banco': 0,
                    'saldo_caja': 0, 'saldo_banco': 0}

        data_mes = defaultdict(_empty)
        data_dia = defaultdict(_empty)

        for c in cortes_all:
            mes   = c.get('mes') or ''
            fecha = c.get('fecha') or ''
            mxn   = float(c.get('total_mxn') or 0)
            medio = c.get('medio_pago', '')
            for d in (data_mes[mes], data_dia[fecha]):
                d['ing_total'] += mxn
                if medio == 'Efectivo':
                    d['ing_caja'] += mxn
                else:
                    d['ing_banco'] += mxn

        for g in gastos_all:
            mes   = g.get('mes') or ''
            fecha = g.get('fecha') or ''
            mxn   = float(g.get('importe_mxn') or 0)
            medio = g.get('medio_pago', '')
            for d in (data_mes[mes], data_dia[fecha]):
                if medio == 'Efectivo':
                    d['gasto_caja'] += mxn
                else:
                    d['gasto_banco'] += mxn

        for mes, d in sorted(data_mes.items()):
            d['mes'] = mes
            d['saldo_caja']  = d['ing_caja']  - d['gasto_caja']
            d['saldo_banco'] = d['ing_banco'] - d['gasto_banco']
            meses.append(d)

        for fecha, d in sorted(data_dia.items(), reverse=True):
            d['fecha'] = fecha
            d['saldo_caja']  = d['ing_caja']  - d['gasto_caja']
            d['saldo_banco'] = d['ing_banco'] - d['gasto_banco']
            dias.append(d)

    except Exception as e:
        flash(f'Error cargando cashflow: {e}', 'error')

    mes_actual    = date.today().strftime('%Y-%m')
    hoy           = date.today().isoformat()
    meses_dias    = sorted({d['fecha'][:7] for d in dias}, reverse=True)
    return render_template('cashflow.html', meses=meses, dias=dias,
                           mes_actual=mes_actual, hoy=hoy, meses_dias=meses_dias)


# ── MOVIMIENTOS (editar / borrar) ───────────────────────────────────────────────
@app.route('/movimientos')
@require_admin
def movimientos():
    cortes, gastos = [], []
    try:
        sb = get_sb()
        cortes = sb.table('cortes').select(
            'id,fecha,cliente,staff,servicio,total_mxn,medio_pago'
        ).order('fecha', desc=True).order('id', desc=True).limit(60).execute().data
        gastos = sb.table('gastos').select(
            'id,fecha,categoria,proveedor,descripcion,importe_mxn,medio_pago'
        ).order('fecha', desc=True).order('id', desc=True).limit(60).execute().data
    except Exception as e:
        flash(f'Error cargando movimientos: {e}', 'error')
    return render_template('movimientos.html', cortes=cortes, gastos=gastos)


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
    return render_template('reservar.html')


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


@app.route('/api/slots')
def api_slots():
    try:
        sb = get_sb()
        colaboradora_id = request.args.get('colaboradora_id', 'any')
        fecha_str = request.args.get('fecha')

        if not fecha_str:
            return jsonify([])

        # Parse services: prefer servicio_ids list, fallback to legacy params
        servicio_ids_str = request.args.get('servicio_ids', '')
        servicio_id      = request.args.get('servicio_id')
        duracion_total_p = request.args.get('duracion_total')

        servicios_info = []  # [{duracion_min, tipo_estacion}, ...]
        duracion = 0

        if servicio_ids_str:
            for sid in (int(x) for x in servicio_ids_str.split(',') if x.strip()):
                srv = sb.table('servicios').select('duracion_min,categoria').eq('id', sid).limit(1).execute()
                if srv.data:
                    cat = srv.data[0]['categoria']
                    servicios_info.append({
                        'duracion_min':   srv.data[0]['duracion_min'],
                        'tipo_estacion':  estacion_de_categoria(cat),
                    })
                    duracion += srv.data[0]['duracion_min']
        elif duracion_total_p:
            duracion = int(duracion_total_p)
        elif servicio_id:
            srv = sb.table('servicios').select('duracion_min,categoria').eq('id', servicio_id).limit(1).execute()
            if not srv.data:
                return jsonify([])
            cat = srv.data[0]['categoria']
            servicios_info = [{'duracion_min': srv.data[0]['duracion_min'], 'tipo_estacion': estacion_de_categoria(cat)}]
            duracion = srv.data[0]['duracion_min']
        else:
            return jsonify([])

        if not duracion:
            return jsonify([])

        fecha_dt   = datetime.strptime(fecha_str, '%Y-%m-%d')
        dia_semana = fecha_dt.weekday()

        # Fetch all turnos for this date with their station type (for capacity check)
        all_turnos_dia = []
        if servicios_info:
            raw = sb.table('turnos').select('hora_inicio,hora_fin,servicios(categoria)').eq('fecha', fecha_str).execute().data
            for t in raw:
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

            turnos_colab = sb.table('turnos').select('hora_inicio,hora_fin').eq(
                'colaboradora_id', colab_id).eq('fecha', fecha_str).execute()
            ocupados = [(t['hora_inicio'][:5], t['hora_fin'][:5]) for t in turnos_colab.data]

            now      = datetime.now()
            min_hora = now + timedelta(hours=2) if fecha_dt.date() == now.date() else None

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
            slots = unique
        else:
            slots = sorted(slots, key=lambda x: x['hora'])

        return jsonify(slots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reservar', methods=['POST'])
def api_reservar():
    try:
        sb = get_sb()
        data = request.json

        existing = sb.table('clientes_reservas').select('id,bloqueado').eq(
            'telefono', data['telefono']).limit(1).execute()
        es_recurrente = bool(existing.data)
        if existing.data:
            if existing.data[0].get('bloqueado'):
                return jsonify({'error': 'No es posible completar la reserva online. Por favor contactá directamente al salón.'}), 403
            cliente_id = existing.data[0]['id']
        else:
            insert_data = {
                'nombre': data['nombre'],
                'apellido': data.get('apellido', ''),
                'telefono': data['telefono'],
                'email': data.get('email', ''),
                'idioma': data.get('idioma', 'es'),
                'acepto_politicas': data.get('acepto_politicas', False),
                'notas': data.get('notas', ''),
                'es_recurrente': False,
            }
            if data.get('fecha_nacimiento'):
                insert_data['fecha_nacimiento'] = data['fecha_nacimiento']
            cliente = sb.table('clientes_reservas').insert(insert_data).execute()
            cliente_id = cliente.data[0]['id']

        servicio_ids = data.get('servicio_ids') or []
        if not servicio_ids and data.get('servicio_id'):
            servicio_ids = [data['servicio_id']]
        if not servicio_ids:
            return jsonify({'error': 'Servicio requerido'}), 400

        servicios_data = []
        duracion_total = 0
        for sid in servicio_ids:
            srv = sb.table('servicios').select('precio_desde,duracion_min').eq('id', sid).limit(1).execute()
            if not srv.data:
                return jsonify({'error': f'Servicio {sid} no encontrado'}), 400
            servicios_data.append(srv.data[0])
            duracion_total += srv.data[0]['duracion_min']

        hora_ini = data['hora']
        hora_fin_total_dt = datetime.strptime(hora_ini, '%H:%M') + timedelta(minutes=duracion_total)
        hora_fin_total = hora_fin_total_dt.strftime('%H:%M')

        colaboradora_id = data.get('colaboradora_id')
        if not colaboradora_id or colaboradora_id == 'any':
            colab_slots = sb.table('disponibilidad').select('colaboradora_id').eq(
                'dia_semana', datetime.strptime(data['fecha'], '%Y-%m-%d').weekday()
            ).execute()
            for row in colab_slots.data:
                cid = row['colaboradora_id']
                conflicto = sb.table('turnos').select('id').eq(
                    'colaboradora_id', cid).eq('fecha', data['fecha']).execute()
                ocupados = [(t['hora_inicio'][:5], t['hora_fin'][:5]) for t in conflicto.data]
                if not any(hora_ini < o_fin and hora_fin_total < o_ini or hora_fin_total > o_fin and hora_ini > o_fin for o_ini, o_fin in ocupados):
                    if not any(hora_ini < o_fin and hora_fin_total > o_ini for o_ini, o_fin in ocupados):
                        colaboradora_id = cid
                        break

        turnos_creados = []
        hora_cursor = datetime.strptime(hora_ini, '%H:%M')
        for i, sid in enumerate(servicio_ids):
            srv_dur = servicios_data[i]['duracion_min']
            t_ini = hora_cursor.strftime('%H:%M')
            hora_cursor += timedelta(minutes=srv_dur)
            t_fin = hora_cursor.strftime('%H:%M')
            turno = sb.table('turnos').insert({
                'cliente_id': cliente_id,
                'colaboradora_id': colaboradora_id,
                'servicio_id': int(sid),
                'fecha': data['fecha'],
                'hora_inicio': t_ini,
                'hora_fin': t_fin,
                'estado': 'pendiente',
                'precio': servicios_data[i]['precio_desde'],
                'notas': data.get('notas', ''),
                'canal': 'web',
            }).execute()
            turnos_creados.append(turno.data[0]['id'])

        return jsonify({'success': True, 'turno_ids': turnos_creados})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── SISTEMA DE TURNOS — INTERNO ─────────────────────────────────────────────────

@app.route('/agenda')
@require_admin
def agenda():
    return render_template('agenda.html')


@app.route('/api/agenda')
@require_admin
def api_agenda():
    try:
        sb = get_sb()
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        fecha = request.args.get('fecha', date.today().isoformat())
        query = sb.table('turnos').select(
            'id,fecha,hora_inicio,hora_fin,estado,precio,notas,canal,'
            'clientes_reservas(id,nombre,apellido,telefono),'
            'colaboradoras(nombre),'
            'servicios(nombre,duracion_min)'
        )
        if desde and hasta:
            query = query.gte('fecha', desde).lte('fecha', hasta)
        else:
            query = query.eq('fecha', fecha)
        data = query.order('fecha').order('hora_inicio').execute()
        return jsonify(data.data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cliente/<int:cid>/historial')
@require_admin
def api_cliente_historial(cid):
    try:
        sb = get_sb()
        cliente = sb.table('clientes_reservas').select('*').eq('id', cid).limit(1).execute()
        if not cliente.data:
            return jsonify({'error': 'Cliente no encontrado'}), 404
        turnos = sb.table('turnos').select(
            'id,fecha,hora_inicio,hora_fin,estado,precio,notas,'
            'colaboradoras(nombre),servicios(nombre)'
        ).eq('cliente_id', cid).order('fecha', desc=True).execute()
        return jsonify({'cliente': cliente.data[0], 'turnos': turnos.data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/turno/<int:tid>/estado', methods=['POST'])
@require_admin
def cambiar_estado_turno(tid):
    try:
        sb = get_sb()
        estado = request.json.get('estado')
        sb.table('turnos').update({'estado': estado}).eq('id', tid).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/walkin', methods=['POST'])
@require_admin
def api_walkin():
    try:
        sb = get_sb()
        data = request.json
        nombre    = (data.get('nombre') or 'Walk in').strip() or 'Walk in'
        telefono  = (data.get('telefono') or '').strip()
        serv_id   = data.get('servicio_id')
        colab_id  = data.get('colaboradora_id')
        hora_ini  = data.get('hora') or datetime.now().strftime('%H:%M')
        notas     = data.get('notas', '').strip()
        fecha_hoy = date.today().isoformat()

        if not serv_id or not colab_id:
            return jsonify({'error': 'Servicio y colaboradora son obligatorios'}), 400

        servicio = sb.table('servicios').select('precio_desde,duracion_min,nombre').eq(
            'id', serv_id).limit(1).execute()
        if not servicio.data:
            return jsonify({'error': 'Servicio no encontrado'}), 400
        duracion = servicio.data[0]['duracion_min']
        hora_fin = (datetime.strptime(hora_ini, '%H:%M') + timedelta(minutes=duracion)).strftime('%H:%M')

        # Buscar o crear cliente
        if telefono:
            existing = sb.table('clientes_reservas').select('id').eq('telefono', telefono).limit(1).execute()
        else:
            existing = type('R', (), {'data': []})()

        if existing.data:
            cliente_id = existing.data[0]['id']
        else:
            cli = sb.table('clientes_reservas').insert({
                'nombre': nombre,
                'apellido': '',
                'telefono': telefono or '',
                'email': '',
                'idioma': 'es',
                'acepto_politicas': False,
                'notas': '',
                'es_recurrente': bool(telefono and existing.data),
            }).execute()
            cliente_id = cli.data[0]['id']

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

        return jsonify({'success': True, 'turno_id': turno.data[0]['id']})
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
        result = []
        for c in colabs.data:
            cs = sb.table('colaboradora_servicios').select('servicio_id').eq(
                'colaboradora_id', c['id']).execute()
            c['servicio_ids'] = [r['servicio_id'] for r in cs.data]
            result.append(c)
        return jsonify(result)
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
            'id,fecha,hora_inicio,estado,precio,canal,'
            'clientes_reservas(id),'
            'colaboradoras(nombre),'
            'servicios(nombre)'
        ).gte('fecha', desde).lte('fecha', hasta).execute().data

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

        cliente_id = None
        if telefono:
            existing = sb.table('clientes_reservas').select('id').eq('telefono', telefono).limit(1).execute()
            if existing.data:
                cliente_id = existing.data[0]['id']

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
@require_admin
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
@require_admin
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
