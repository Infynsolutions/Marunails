from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
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
    {'nombre': 'MARU',            'comision': 0.4},
    {'nombre': 'KAREN RECEPCION', 'comision': 0.3},
    {'nombre': 'KAREN',           'comision': 0.4},
    {'nombre': 'MILI',            'comision': 0.3},
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


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ── REGISTRAR CORTE ────────────────────────────────────────────────────────────
@app.route('/corte', methods=['GET', 'POST'])
def corte():
    if request.method == 'POST':
        fecha_str     = request.form.get('fecha')
        cliente       = request.form.get('cliente', '').strip() or 'Walk in'
        staff_nombre  = request.form.get('staff')
        servicio      = request.form.get('servicio')
        moneda        = request.form.get('moneda', 'MXN')
        total_cobrado = float(request.form.get('total_cobrado') or 0)
        propina       = float(request.form.get('propina') or 0)
        medio_pago    = request.form.get('medio_pago')
        notas         = request.form.get('notas', '').strip()

        if not staff_nombre or not servicio or not medio_pago or total_cobrado <= 0:
            flash('Completá todos los campos obligatorios.', 'error')
            return redirect(url_for('corte'))

        d          = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        tc         = TC_USD if moneda == 'USD' else 1
        venta_neta = total_cobrado - propina
        semana, mes, quincena = get_week_quincena(d)

        row = {
            'fecha':         fecha_str,
            'cliente':       cliente,
            'staff':         staff_nombre,
            'servicio':      servicio,
            'moneda':        moneda,
            'total_cobrado': total_cobrado,
            'propina':       propina if propina else 0,
            'medio_pago':    medio_pago,
            'notas':         notas,
            'venta_neta':    round(venta_neta, 2),
            'tc':            tc,
            'total_mxn':     round(total_cobrado * tc, 2),
            'propina_mxn':   round(propina * tc, 2),
            'neto_mxn':      round(venta_neta * tc, 2),
            'mes':           mes,
            'semana':        semana,
            'quincena':      quincena,
        }

        try:
            get_sb().table('cortes').insert(row).execute()
            flash(f'Corte registrado — {staff_nombre} · {servicio} · ${total_cobrado:,.0f}', 'success')
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
        fecha_str    = request.form.get('fecha')
        categoria    = request.form.get('categoria')
        subcategoria = request.form.get('subcategoria', '').strip()
        proveedor    = request.form.get('proveedor', '').strip()
        descripcion  = request.form.get('descripcion', '').strip()
        moneda       = request.form.get('moneda', 'MXN')
        importe      = float(request.form.get('importe') or 0)
        medio_pago   = request.form.get('medio_pago')
        notas        = request.form.get('notas', '').strip()

        if not categoria or not medio_pago or importe == 0:
            flash('Completá todos los campos obligatorios.', 'error')
            return redirect(url_for('gasto'))

        d   = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        tc  = TC_USD if moneda == 'USD' else 1
        semana, mes, quincena = get_week_quincena(d)

        row = {
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

        try:
            get_sb().table('gastos').insert(row).execute()
            flash(f'Gasto registrado — {categoria} · ${importe:,.0f}', 'success')
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
        cortes_res = sb.table('cortes').select('mes,total_mxn,medio_pago').execute()
        gastos_res = sb.table('gastos').select('mes,importe_mxn,medio_pago').execute()

        data = defaultdict(lambda: {
            'ing_caja': 0, 'ing_banco': 0, 'ing_total': 0,
            'gasto_caja': 0, 'gasto_banco': 0,
            'saldo_caja': 0, 'saldo_banco': 0,
        })

        for c in cortes_res.data:
            mes = c.get('mes') or ''
            mxn = float(c.get('total_mxn') or 0)
            medio = c.get('medio_pago', '')
            data[mes]['ing_total'] += mxn
            if medio == 'Efectivo':
                data[mes]['ing_caja'] += mxn
            else:
                data[mes]['ing_banco'] += mxn

        for g in gastos_res.data:
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


if __name__ == '__main__':
    print('\n  MaruNails corriendo en http://localhost:5000\n')
    app.run(debug=False, host='0.0.0.0', port=5000)
