import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, cadena_de_turno, choques_movimiento  # noqa: E402


def turno(id, ini, fin, cliente=1, colab=10, fecha='2026-10-06', estado='confirmado'):
    return {'id': id, 'cliente_id': cliente, 'colaboradora_id': colab, 'fecha': fecha,
            'hora_inicio': ini + ':00', 'hora_fin': fin + ':00', 'estado': estado,
            'canal': 'recepcion', 'created_at': '2026-10-05T12:00:00+00:00'}


# ── cadena_de_turno ──

def test_cadena_agrupa_servicios_encadenados_de_la_misma_cita():
    a, b, c = turno(1, '10:00', '12:10'), turno(2, '12:10', '12:45'), turno(3, '12:45', '13:25')
    assert [t['id'] for t in cadena_de_turno([c, a, b], b)] == [1, 2, 3]


def test_cadena_corta_cuando_hay_un_hueco():
    a, b = turno(1, '10:00', '11:00'), turno(2, '11:30', '12:00')
    assert [t['id'] for t in cadena_de_turno([a, b], a)] == [1]


def test_cadena_ignora_otra_clienta_otra_chica_y_cancelados():
    a = turno(1, '10:00', '11:00')
    otra_clienta = turno(2, '11:00', '12:00', cliente=2)
    otra_chica = turno(3, '11:00', '12:00', colab=11)
    cancelado = turno(4, '11:00', '12:00', estado='cancelado_cliente')
    assert [t['id'] for t in cadena_de_turno([a, otra_clienta, otra_chica, cancelado], a)] == [1]


def test_cadena_de_un_turno_cancelado_es_solo_ese_turno():
    a = turno(1, '10:00', '11:00', estado='no_show')
    b = turno(2, '11:00', '12:00')
    assert [t['id'] for t in cadena_de_turno([a, b], a)] == [1]


# ── choques_movimiento ──

HORARIO = [(9 * 60, 19 * 60)]


def mov(ini, fin, est='manicura'):
    return {'hora_inicio': ini, 'hora_fin': fin, 'tipo_estacion': est}


def otro(ini, fin, propio=False, est=None, cliente='Ana'):
    return {'es_de_colab': propio, 'hora_inicio': ini, 'hora_fin': fin, 'tipo_estacion': est, 'cliente': cliente}


def test_sin_choques():
    assert choques_movimiento([mov(600, 660)], [otro(660, 720, propio=True)], 'GABY', HORARIO, False) == []


def test_choque_con_otra_cita_de_la_misma_chica():
    avisos = choques_movimiento([mov(600, 660)], [otro(630, 700, propio=True, cliente='Sorimar')],
                                'GABY', HORARIO, False)
    assert avisos == ['GABY ya tiene a Sorimar de 10:30 a 11:40.']


def test_cita_de_otra_chica_a_la_misma_hora_no_choca():
    assert choques_movimiento([mov(600, 660, est=None)], [otro(600, 660)], 'GABY', HORARIO, False) == []


def test_estacion_llena():
    llenas = [otro(600, 660, est='manicura'), otro(620, 700, est='manicura')]
    avisos = choques_movimiento([mov(630, 690)], llenas, 'GABY', HORARIO, False)
    assert avisos == ['No queda mesa de manicure libre de 10:30 a 11:30.']


def test_fuera_de_horario_y_dia_bloqueado_y_dia_libre():
    assert choques_movimiento([mov(1140, 1200)], [], 'GABY', HORARIO, False) == \
        ['Queda fuera del horario de GABY (09:00–19:00).']
    assert choques_movimiento([mov(600, 660)], [], 'GABY', HORARIO, True) == ['GABY tiene el día bloqueado.']
    assert choques_movimiento([mov(600, 660)], [], 'GABY', [], False) == ['GABY no trabaja ese día.']


def test_grupo_se_valida_entero_contra_el_horario():
    grupo = [mov(1080, 1110), mov(1110, 1170)]  # 18:00–19:30, el horario termina 19:00
    assert choques_movimiento(grupo, [], 'GABY', HORARIO, False) == \
        ['Queda fuera del horario de GABY (09:00–19:00).']


# ── permisos ──

def test_equipo_sin_sesion_no_entra_a_la_agenda():
    c = app.test_client()
    assert c.get('/agenda').status_code == 302
    assert c.get('/api/agenda').status_code == 401


def test_chica_del_equipo_no_entra_al_sistema(monkeypatch):
    c = app.test_client()
    with c.session_transaction() as s:
        s['equipo_id'] = 10
        s['equipo_nombre'] = 'GABY'
    r = c.get('/cashflow')
    assert r.status_code == 302 and r.headers['Location'].endswith('/agenda')
    assert c.post('/api/pago-sena/1/reembolso').status_code == 403
    assert c.put('/admin/api/colaboradora/10/pin', json={'pin': '1234'}).status_code == 403


# ── PUT /api/turno/<id> contra una base en memoria ──

class _Q:
    def __init__(self, db, tabla):
        self.db, self.tabla, self.filtros, self.cambios, self.n = db, tabla, [], None, None

    def select(self, *_a, **_k): return self
    def order(self, *_a, **_k): return self
    def limit(self, n): self.n = n; return self
    def eq(self, k, v): self.filtros.append(lambda r: r.get(k) == v); return self
    def in_(self, k, vs): self.filtros.append(lambda r: r.get(k) in vs); return self
    def update(self, cambios): self.cambios = cambios; return self
    def insert(self, row): self.db.setdefault(self.tabla, []).append(row); self.cambios = 'insert'; return self

    def execute(self):
        rows = [r for r in self.db.get(self.tabla, []) if all(f(r) for f in self.filtros)]
        if isinstance(self.cambios, dict):
            for r in rows:
                r.update(self.cambios)
        return type('R', (), {'data': rows[:self.n] if self.n else rows})()


class _DB:
    def __init__(self, data): self.data = data
    def table(self, t): return _Q(self.data, t)


def _base():
    srv = {'id': 1, 'nombre': 'Gel Manicure', 'duracion_min': 60, 'precio_desde': 500, 'categoria': 'Manicure'}
    srv2 = {'id': 2, 'nombre': 'Pedicure Spa', 'duracion_min': 45, 'precio_desde': 600, 'categoria': 'Pedicure'}
    cli = {'id': 7, 'nombre': 'Sorimar', 'apellido': 'Estrada', 'telefono': '9840000000'}

    def t(id, ini, fin, colab, sid, cliente=7):
        return {'id': id, 'cliente_id': cliente, 'colaboradora_id': colab, 'servicio_id': sid, 'fecha': '2026-10-06',
                'hora_inicio': ini + ':00', 'hora_fin': fin + ':00', 'estado': 'confirmado', 'canal': 'recepcion',
                'created_at': '2026-10-05T12:00:00+00:00', 'clientes_reservas': cli,
                'servicios': {'categoria': 'Manicure' if sid == 1 else 'Pedicure'}}
    return {
        'turnos': [t(1, '10:00', '11:00', 10, 1), t(2, '11:00', '11:45', 10, 2),
                   t(3, '12:00', '13:00', 11, 1, cliente=8)],
        'colaboradoras': [{'id': 10, 'nombre': 'GABY'}, {'id': 11, 'nombre': 'FANNY'}],
        'servicios': [srv, srv2],
        'clientes_reservas': [cli],
        'disponibilidad': [{'colaboradora_id': 10, 'dia_semana': 1, 'hora_inicio': '09:00:00', 'hora_fin': '19:00:00'},
                           {'colaboradora_id': 11, 'dia_semana': 1, 'hora_inicio': '09:00:00', 'hora_fin': '19:00:00'}],
        'bloqueos': [],
    }


def _cliente_admin(monkeypatch, data):
    import app as m
    monkeypatch.setattr(m, 'get_sb', lambda: _DB(data))
    monkeypatch.setattr(m, 'registrar_cambio', lambda *a, **k: None)
    c = m.app.test_client()
    with c.session_transaction() as s:
        s['admin_logged_in'] = True
    return c


def test_mover_cita_completa_a_otra_chica(monkeypatch):
    data = _base()
    c = _cliente_admin(monkeypatch, data)
    r = c.put('/api/turno/1', json={'fecha': '2026-10-06', 'hora_inicio': '14:00',
                                    'colaboradora_id': 11, 'mover_grupo': True})
    assert r.status_code == 200, r.json
    t1, t2 = data['turnos'][0], data['turnos'][1]
    assert (t1['hora_inicio'], t1['hora_fin'], t1['colaboradora_id']) == ('14:00', '15:00', 11)
    assert (t2['hora_inicio'], t2['hora_fin'], t2['colaboradora_id']) == ('15:00', '15:45', 11)
    assert r.json['servicios'] == ['Gel Manicure', 'Pedicure Spa']


def test_mover_solo_el_segundo_servicio(monkeypatch):
    data = _base()
    c = _cliente_admin(monkeypatch, data)
    r = c.put('/api/turno/2', json={'hora_inicio': '16:00', 'mover_grupo': False})
    assert r.status_code == 200
    assert data['turnos'][0]['hora_inicio'] == '10:00:00'          # el primero no se tocó
    assert (data['turnos'][1]['hora_inicio'], data['turnos'][1]['hora_fin']) == ('16:00', '16:45')


def test_choque_devuelve_409_sin_escribir_y_forzar_escribe(monkeypatch):
    data = _base()
    c = _cliente_admin(monkeypatch, data)
    body = {'hora_inicio': '12:30', 'colaboradora_id': 11, 'mover_grupo': False}
    r = c.put('/api/turno/1', json=body)
    assert r.status_code == 409
    assert any('FANNY ya tiene' in a for a in r.json['conflictos'])
    assert data['turnos'][0]['hora_inicio'] == '10:00:00'
    r = c.put('/api/turno/1', json={**body, 'forzar': True})
    assert r.status_code == 200
    assert data['turnos'][0]['hora_inicio'] == '12:30'


def test_cambiar_servicio_toma_duracion_y_precio_nuevos(monkeypatch):
    data = _base()
    c = _cliente_admin(monkeypatch, data)
    r = c.put('/api/turno/1', json={'servicio_id': 2, 'mover_grupo': True, 'forzar': True})
    assert r.status_code == 200
    t1, t2 = data['turnos'][0], data['turnos'][1]
    assert (t1['servicio_id'], t1['precio'], t1['hora_fin']) == (2, 600, '10:45')
    assert (t2['hora_inicio'], t2['hora_fin']) == ('10:45', '11:30')   # el siguiente se corre
