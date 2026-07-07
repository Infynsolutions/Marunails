from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date, timedelta
from collections import defaultdict
import os

from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'marunails_secret_2026')

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://dbhxrboacqppximbcokz.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRiaHhyYm9hY3FwcHhpbWJjb2t6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0Mjg1NDMsImV4cCI6MjA5OTAwNDU0M30.fcVl9hwRTACJrp4BH7CZdj5ZzPa7-VaAqJlUdHH-NKs')

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

CATEGORIAS_GASTO = [
    'Productos', 'Renta', 'Servicios', 'Sueldos/Comisiones', 'Marketing',
    'Impuestos', 'Otros', 'Gastos Operativos', 'Retiros -Mariana',
    'Inversiones nuevas', 'Prestamos',
]

MESES_ES = {
    1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun',
    7: 'jul', 8: 'ago', 9: 'sep', 10: 'oct', 11: 'nov', 12: 'dic',
}


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


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    mes_actual = date.today().strftime('%Y-%m')
    mes_mostrado = mes_actual
    resumen = None
    try:
        sb = get_sb()
        # Mostrar el mes actual; si no tiene cortes, el último mes con data
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


# ── REGISTRAR GASTO ────────────────────────────────────────────────────────────
@app.route('/gasto', methods=['GET', 'POST'])
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
def cashflow():
    meses = []
    try:
        sb = get_sb()
        cortes_all = fetch_all(sb, 'cortes', 'mes,total_mxn,medio_pago')
        gastos_all = fetch_all(sb, 'gastos', 'mes,importe_mxn,medio_pago')

        data = defaultdict(lambda: {
            'ing_caja': 0, 'ing_banco': 0, 'ing_total': 0,
            'gasto_caja': 0, 'gasto_banco': 0,
            'saldo_caja': 0, 'saldo_banco': 0,
        })

        for c in cortes_all:
            mes = c.get('mes') or ''
            mxn = float(c.get('total_mxn') or 0)
            medio = c.get('medio_pago', '')
            data[mes]['ing_total'] += mxn
            if medio == 'Efectivo':
                data[mes]['ing_caja'] += mxn
            else:
                data[mes]['ing_banco'] += mxn

        for g in gastos_all:
            mes = g.get('mes') or ''
            mxn = float(g.get('importe_mxn') or 0)
            medio = g.get('medio_pago', '')
            if medio == 'Efectivo':
                data[mes]['gasto_caja'] += mxn
            else:
                data[mes]['gasto_banco'] += mxn

        for mes, d in sorted(data.items()):
            d['mes'] = mes
            d['saldo_caja']  = d['ing_caja']  - d['gasto_caja']
            d['saldo_banco'] = d['ing_banco'] - d['gasto_banco']
            meses.append(d)

    except Exception as e:
        flash(f'Error cargando cashflow: {e}', 'error')

    mes_actual = date.today().strftime('%Y-%m')
    return render_template('cashflow.html', meses=meses, mes_actual=mes_actual)


# ── MOVIMIENTOS (editar / borrar) ───────────────────────────────────────────────
@app.route('/movimientos')
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
def borrar_corte(cid):
    try:
        get_sb().table('cortes').delete().eq('id', cid).execute()
        flash('Corte eliminado.', 'success')
    except Exception as e:
        flash(f'Error al borrar: {e}', 'error')
    return redirect(url_for('movimientos'))


@app.route('/gasto/<int:gid>/editar', methods=['GET', 'POST'])
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
def borrar_gasto(gid):
    try:
        get_sb().table('gastos').delete().eq('id', gid).execute()
        flash('Gasto eliminado.', 'success')
    except Exception as e:
        flash(f'Error al borrar: {e}', 'error')
    return redirect(url_for('movimientos'))


if __name__ == '__main__':
    print('\n  MaruNails corriendo en http://localhost:5000\n')
    app.run(debug=False, host='0.0.0.0', port=5000)
