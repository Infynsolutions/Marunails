from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'punadosano_secret_2024'

_DATA_DIR = os.environ.get('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_DATA_DIR, 'inventario.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    print(f'[DB] DATA_DIR={_DATA_DIR}')
    print(f'[DB] DB_PATH={DB_PATH}')
    print(f'[DB] dir exists={os.path.isdir(_DATA_DIR)}, writable={os.access(_DATA_DIR, os.W_OK)}')
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS proveedores (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS productos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT    NOT NULL,
            presentacion TEXT,
            categoria    TEXT,
            proveedor_id INTEGER NOT NULL,
            stock_actual INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            precio       INTEGER DEFAULT 0,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        );
        CREATE TABLE IF NOT EXISTS movimientos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            tipo        TEXT    NOT NULL CHECK(tipo IN ('venta','entrada')),
            cantidad    INTEGER NOT NULL,
            fecha       TEXT    DEFAULT (datetime('now','localtime')),
            nota        TEXT,
            cobrado     INTEGER DEFAULT 0,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        );
    ''')
    conn.commit()

    # Migraciones sobre DB existente
    try:
        c.execute('ALTER TABLE movimientos ADD COLUMN cobrado INTEGER DEFAULT 0')
        conn.commit()
    except Exception:
        pass  # columna ya existe

    # Actualizar mínimo de 3 → 5 si ya había datos
    c.execute('UPDATE productos SET stock_minimo = 5 WHERE stock_minimo = 3')
    conn.commit()

    # Poblar solo si está vacío
    if c.execute('SELECT COUNT(*) FROM proveedores').fetchone()[0] == 0:
        for nombre in ['MANANTIAL', 'GRANIX', 'MARCO', 'LAUTARO', 'SAN CAYETANO', 'ALTOS SINGUIL']:
            c.execute('INSERT INTO proveedores (nombre) VALUES (?)', (nombre,))
        conn.commit()

        prov = {r['nombre']: r['id'] for r in c.execute('SELECT id, nombre FROM proveedores')}

        # (nombre, presentacion, categoria, proveedor, precio)
        productos_data = [
            # CEREALES – MANANTIAL
            ('FIBRA DE SALVADO',         '100 GR.', 'CEREALES',           'MANANTIAL',    1300),
            ('CEREAL INTEGRAL',          '350 GR.', 'CEREALES',           'MANANTIAL',    3800),
            ('OSITOS (MIEL Y AVENA)',    '250 GR.', 'CEREALES',           'MANANTIAL',    1800),
            ('AVENA INSTANTANEA',        '400 GR.', 'VARIOS',             'MANANTIAL',    1600),
            # CEREALES – GRANIX
            ('ALMOHADITA AVELLANA',      '250 GR.', 'CEREALES',           'GRANIX',       4200),
            ('ALMOHADITA MANI',          '250 GR.', 'CEREALES',           'GRANIX',       4200),
            ('ALMOHADITA FRUTILLA',      '250 GR.', 'CEREALES',           'GRANIX',       4200),
            ('GRANOLA PUÑADO SANO',      '500 GR.', 'CEREALES',           'GRANIX',       8900),
            # CEREALES – SAN CAYETANO
            ('QUINOA POP',               '150 GR.', 'CEREALES',           'SAN CAYETANO', 1600),
            # FRUTOS SECOS – MARCO
            ('NUECES',                   '400 GR.', 'FRUTOS SECOS',       'MARCO',        8400),
            ('NUECES',                   '200 GR.', 'FRUTOS SECOS',       'MARCO',        4400),
            ('PASAS DE UVA MORENA',      '200 GR.', 'FRUTOS SECOS',       'MARCO',        1900),
            # FRUTOS SECOS – SAN CAYETANO
            ('PASAS DE UVA RUBIA',       '200 GR.', 'FRUTOS SECOS',       'SAN CAYETANO', 2500),
            ('CASTAÑAS DE CAJÚ NATURALES','200 GR.','FRUTOS SECOS',       'SAN CAYETANO', 5700),
            ('ALMENDRA NON PAREIL',      '200 GR.', 'FRUTOS SECOS',       'SAN CAYETANO', 6600),
            ('PISTACHO',                 '150 GR.', 'FRUTOS SECOS',       'SAN CAYETANO', 9900),
            # FRUTOS SECOS – ALTOS SINGUIL
            ('MIX FRUTOS SECOS POWER',   '650 GR.', 'FRUTOS SECOS',       'ALTOS SINGUIL',7600),
            ('MIX FRUTOS SECOS POWER',   '200 GR.', 'FRUTOS SECOS',       'ALTOS SINGUIL',2400),
            # SEMILLAS – SAN CAYETANO
            ('MIX DE 6 SEMILLAS (SIN TAC)','200 GR.','SEMILLAS',          'SAN CAYETANO', 1800),
            # SEMILLAS – ALTOS SINGUIL
            ('SEMILLA DE GIRASOL PELADO','150 GR.', 'SEMILLAS',           'ALTOS SINGUIL',1300),
            ('SEMILLA DE SESAMO INTEGRAL','150 GR.','SEMILLAS',           'ALTOS SINGUIL',1500),
            ('SEMILLA DE CHIA',          '150 GR.', 'SEMILLAS',           'ALTOS SINGUIL',2100),
            ('SEMILLA DE LINO',          '200 GR.', 'SEMILLAS',           'ALTOS SINGUIL',1300),
            # FRUTAS DESHIDRATADAS – ALTOS SINGUIL
            ('CIRUELA DESHIDRATADA SIN CAROZO','250 GR.','FRUTAS DESHIDRATADAS','ALTOS SINGUIL',3400),
            ('DATILES DEGLET NOUR CON CAROZO', '250 GR.','FRUTAS DESHIDRATADAS','ALTOS SINGUIL',3200),
            # VARIOS – ALTOS SINGUIL
            ('COCO RALLADO MID FAT',     '150 GR.', 'VARIOS',             'ALTOS SINGUIL',2100),
            ('MANTEQUILLA DE MANI ODDIS', None,     'VARIOS',             'ALTOS SINGUIL',3700),
            # VARIOS – LAUTARO
            ('MIEL PURA',                None,      'VARIOS',             'LAUTARO',      4200),
            ('STEVIA BOLIVIANA',         None,      'VARIOS',             'LAUTARO',      5800),
            # VARIOS – SAN CAYETANO
            ('ACEITE DE COCO',           '100 CC.', 'VARIOS',             'SAN CAYETANO', 7400),
            ('ACEITE DE COCO',           '360 CC.', 'VARIOS',             'SAN CAYETANO',13000),
            ('AZUCAR IMPALPABLE',        '250 GR.', 'VARIOS',             'SAN CAYETANO', 1700),
            ('AZUCAR MASCABO',           '250 GR.', 'VARIOS',             'SAN CAYETANO', 1900),
            ('SOJA TEXTURIZADA',         '300 GR.', 'VARIOS',             'SAN CAYETANO', 1600),
            ('CHIPS DE CHOCOLATE SEMIAMARGO','200 GR.','VARIOS',          'SAN CAYETANO', 3200),
            ('CACAO AMARGO BRASIL',      '150 GR.', 'VARIOS',             'SAN CAYETANO', 4000),
            ('HARINA DE ALMENDRA SIN PIEL','150 GR.','VARIOS',            'SAN CAYETANO', 6300),
            ('HARINA DE COCO',           '150 GR.', 'VARIOS',             'SAN CAYETANO', 1800),
        ]

        for nombre, pres, cat, prov_nombre, precio in productos_data:
            c.execute(
                'INSERT INTO productos (nombre, presentacion, categoria, proveedor_id, stock_actual, stock_minimo, precio) '
                'VALUES (?, ?, ?, ?, 0, 5, ?)',
                (nombre, pres, cat, prov[prov_nombre], precio)
            )
        conn.commit()

    conn.close()


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
@app.route('/')
def dashboard():
    conn = get_db()
    productos = conn.execute('''
        SELECT p.*, pr.nombre AS proveedor_nombre
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        ORDER BY p.categoria, p.nombre, p.presentacion
    ''').fetchall()
    conn.close()

    total     = len(productos)
    sin_stock = sum(1 for p in productos if p['stock_actual'] == 0)
    stock_bajo= sum(1 for p in productos if 0 < p['stock_actual'] <= p['stock_minimo'])
    stock_ok  = total - sin_stock - stock_bajo

    return render_template('index.html',
                           productos=productos,
                           total=total,
                           sin_stock=sin_stock,
                           stock_bajo=stock_bajo,
                           stock_ok=stock_ok)


# ── REGISTRAR VENTA ────────────────────────────────────────────────────────────
@app.route('/venta', methods=['GET', 'POST'])
def venta():
    conn = get_db()
    if request.method == 'POST':
        ids       = request.form.getlist('producto_id')
        cantidades= request.form.getlist('cantidad')
        nota      = request.form.get('nota', '').strip()
        cobrado   = 1 if request.form.get('cobrado') == '1' else 0

        if not ids:
            flash('El pedido está vacío.', 'error')
            conn.close()
            return redirect(url_for('venta'))

        # Validar stock antes de modificar nada
        errores = []
        items = []
        for pid_str, cant_str in zip(ids, cantidades):
            pid   = int(pid_str)
            cant  = int(cant_str)
            prod  = conn.execute('SELECT * FROM productos WHERE id = ?', (pid,)).fetchone()
            if cant <= 0:
                errores.append(f'{prod["nombre"]}: la cantidad debe ser mayor a 0.')
            elif cant > prod['stock_actual']:
                errores.append(f'{prod["nombre"]}: stock insuficiente (disponible: {prod["stock_actual"]}).')
            else:
                items.append((pid, cant, prod))

        if errores:
            for e in errores:
                flash(e, 'error')
            conn.close()
            return redirect(url_for('venta'))

        # Registrar todos los movimientos en una sola transacción
        for pid, cant, prod in items:
            conn.execute('UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?', (cant, pid))
            conn.execute("INSERT INTO movimientos (producto_id, tipo, cantidad, nota, cobrado) VALUES (?, 'venta', ?, ?, ?)",
                         (pid, cant, nota, cobrado))
        conn.commit()

        estado_pago = 'cobrado' if cobrado else 'pendiente de cobro'
        cliente_txt = f' para {nota}' if nota else ''
        flash(f'Pedido{cliente_txt} registrado ({estado_pago}) — {len(items)} producto{"s" if len(items) > 1 else ""}.', 'success')
        conn.close()
        return redirect(url_for('venta'))

    # Agrupar productos por categoría para el select
    rows = conn.execute('''
        SELECT p.id, p.nombre, p.presentacion, p.stock_actual, p.categoria, p.precio
        FROM productos p
        ORDER BY p.categoria, p.nombre, p.presentacion
    ''').fetchall()
    conn.close()

    categorias = {}
    for r in rows:
        cat = r['categoria']
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(r)

    return render_template('venta.html', categorias=categorias)


# ── AGREGAR STOCK ──────────────────────────────────────────────────────────────
@app.route('/entrada', methods=['GET', 'POST'])
def entrada():
    conn = get_db()
    if request.method == 'POST':
        ids       = request.form.getlist('producto_id')
        cantidades= request.form.getlist('cantidad')
        nota      = request.form.get('nota', '').strip()

        if not ids:
            flash('La entrada está vacía.', 'error')
            conn.close()
            return redirect(url_for('entrada'))

        errores = []
        items = []
        for pid_str, cant_str in zip(ids, cantidades):
            pid  = int(pid_str)
            cant = int(cant_str)
            prod = conn.execute('SELECT * FROM productos WHERE id = ?', (pid,)).fetchone()
            if cant <= 0:
                errores.append(f'{prod["nombre"]}: la cantidad debe ser mayor a 0.')
            else:
                items.append((pid, cant, prod))

        if errores:
            for e in errores:
                flash(e, 'error')
            conn.close()
            return redirect(url_for('entrada'))

        for pid, cant, prod in items:
            conn.execute('UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?', (cant, pid))
            conn.execute("INSERT INTO movimientos (producto_id, tipo, cantidad, nota) VALUES (?, 'entrada', ?, ?)",
                         (pid, cant, nota))
        conn.commit()

        total_unid = sum(c for _, c, _ in items)
        nota_txt = f' — {nota}' if nota else ''
        flash(f'Entrada confirmada{nota_txt}: {len(items)} producto{"s" if len(items) > 1 else ""}, {total_unid} unidades en total.', 'success')
        conn.close()
        return redirect(url_for('entrada'))

    # Agrupar por proveedor para el select
    rows = conn.execute('''
        SELECT p.id, p.nombre, p.presentacion, p.stock_actual, pr.nombre AS proveedor_nombre
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        ORDER BY pr.nombre, p.nombre, p.presentacion
    ''').fetchall()
    conn.close()

    proveedores = {}
    for r in rows:
        prov = r['proveedor_nombre']
        if prov not in proveedores:
            proveedores[prov] = []
        proveedores[prov].append(r)

    return render_template('entrada.html', proveedores=proveedores)


# ── BORRAR MOVIMIENTO ─────────────────────────────────────────────────────────
@app.route('/historial/borrar', methods=['POST'])
def borrar_movimiento():
    nota        = request.form.get('nota', '')
    fecha_minuto= request.form.get('fecha_minuto', '')   # 'YYYY-MM-DD HH:MM'
    tipo        = request.form.get('tipo', '')

    if not fecha_minuto or not tipo:
        flash('Datos insuficientes para borrar.', 'error')
        return redirect(url_for('historial'))

    conn = get_db()
    # Buscar todos los movimientos del grupo
    movs = conn.execute('''
        SELECT id, producto_id, cantidad, tipo FROM movimientos
        WHERE tipo = ?
          AND COALESCE(nota, '') = ?
          AND strftime('%Y-%m-%d %H:%M', fecha) = ?
    ''', (tipo, nota if nota != '—' else '', fecha_minuto)).fetchall()

    if not movs:
        flash('No se encontraron movimientos para borrar.', 'error')
        conn.close()
        return redirect(url_for('historial'))

    for m in movs:
        # Restaurar stock
        if m['tipo'] == 'venta':
            conn.execute('UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?',
                         (m['cantidad'], m['producto_id']))
        else:
            conn.execute('UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?',
                         (m['cantidad'], m['producto_id']))
        conn.execute('DELETE FROM movimientos WHERE id = ?', (m['id'],))

    conn.commit()
    conn.close()
    flash(f'Movimiento eliminado y stock restaurado ({len(movs)} producto{"s" if len(movs) > 1 else ""}).', 'success')
    return redirect(url_for('historial'))


# ── PEDIDOS ────────────────────────────────────────────────────────────────────
@app.route('/pedidos')
def pedidos():
    conn = get_db()
    rows = conn.execute('''
        SELECT p.*, pr.nombre AS proveedor_nombre
        FROM productos p
        JOIN proveedores pr ON p.proveedor_id = pr.id
        WHERE p.stock_actual <= p.stock_minimo
        ORDER BY pr.nombre, p.nombre, p.presentacion
    ''').fetchall()
    conn.close()

    pedidos = {}
    for p in rows:
        prov = p['proveedor_nombre']
        if prov not in pedidos:
            pedidos[prov] = []
        pedidos[prov].append(p)

    return render_template('pedidos.html', pedidos=pedidos)


# ── HISTORIAL ──────────────────────────────────────────────────────────────────
@app.route('/historial')
def historial():
    conn = get_db()
    movimientos = conn.execute('''
        SELECT
            MIN(m.fecha)                              AS fecha,
            m.tipo,
            COALESCE(NULLIF(m.nota,''), '—')          AS nota,
            m.cobrado,
            COUNT(m.id)                               AS num_productos,
            SUM(m.cantidad)                           AS total_unidades,
            SUM(p.precio * m.cantidad)                AS total_pesos
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        GROUP BY m.tipo, m.nota, m.cobrado, strftime('%Y-%m-%d %H:%M', m.fecha)
        ORDER BY fecha DESC
        LIMIT 100
    ''').fetchall()
    conn.close()
    return render_template('historial.html', movimientos=movimientos)


# ── COBROS ────────────────────────────────────────────────────────────────────
@app.route('/cobros')
def cobros():
    conn = get_db()
    pendientes = conn.execute('''
        SELECT
            MIN(m.fecha)                         AS fecha,
            COALESCE(NULLIF(m.nota,''), '—')     AS nota,
            SUM(p.precio * m.cantidad)           AS total_pesos
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        WHERE m.tipo = 'venta' AND m.cobrado = 0
        GROUP BY m.nota, strftime('%Y-%m-%d %H:%M', m.fecha)
        ORDER BY fecha DESC
    ''').fetchall()
    cobradas = conn.execute('''
        SELECT
            MIN(m.fecha)                         AS fecha,
            COALESCE(NULLIF(m.nota,''), '—')     AS nota,
            SUM(p.precio * m.cantidad)           AS total_pesos
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        WHERE m.tipo = 'venta' AND m.cobrado = 1
        GROUP BY m.nota, strftime('%Y-%m-%d %H:%M', m.fecha)
        ORDER BY fecha DESC
        LIMIT 50
    ''').fetchall()
    conn.close()
    return render_template('cobros.html', pendientes=pendientes, cobradas=cobradas)


@app.route('/cobros/marcar-pagado', methods=['POST'])
def marcar_pagado():
    nota         = request.form.get('nota', '')
    fecha_minuto = request.form.get('fecha_minuto', '')
    conn = get_db()
    conn.execute('''
        UPDATE movimientos SET cobrado = 1
        WHERE tipo = 'venta'
          AND cobrado = 0
          AND COALESCE(nota, '') = ?
          AND strftime('%Y-%m-%d %H:%M', fecha) = ?
    ''', (nota if nota != '—' else '', fecha_minuto))
    conn.commit()
    conn.close()
    flash('Venta marcada como cobrada.', 'success')
    return redirect(url_for('cobros'))


init_db()

if __name__ == '__main__':
    print('\n  Inventario Puñado Sano corriendo en http://localhost:5000')
    print('  Acceso desde red local: http://<IP-de-tu-PC>:5000\n')
    app.run(debug=False, host='0.0.0.0', port=5000)
