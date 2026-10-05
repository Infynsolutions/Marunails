import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import (ReservaError, buscar_clienta, clienta_para_reserva,  # noqa: E402
                 directorio_clientas, tel_digitos)

CLIENTAS = [
    {'id': 1, 'nombre': 'Jessica Luongo', 'apellido': '', 'telefono': '+52 984 111 2233', 'email': 'jess@mail.com'},
    {'id': 2, 'nombre': 'Ana', 'apellido': '', 'telefono': '9840000001', 'email': ''},
    {'id': 3, 'nombre': 'Juli', 'apellido': '', 'telefono': '', 'email': ''},
    {'id': 4, 'nombre': 'Sofia', 'apellido': 'Ponce', 'telefono': '9845556677', 'email': ''},
]


# ── buscar_clienta ──

def test_telefono_con_otro_formato_es_la_misma_clienta():
    assert tel_digitos('+52 (984) 111-2233') == tel_digitos('9841112233')
    assert buscar_clienta(CLIENTAS, 'Otra', telefono='984 111 2233')['id'] == 1


def test_email_sin_importar_mayusculas():
    assert buscar_clienta(CLIENTAS, 'Jess', telefono='9999999999', email=' JESS@mail.com ')['id'] == 1


def test_nombre_completo_coincide_aunque_cambie_el_telefono():
    assert buscar_clienta(CLIENTAS, 'jessica  luongo', telefono='9990001111')['id'] == 1
    assert buscar_clienta(CLIENTAS, 'Sofia', 'Ponce')['id'] == 4


def test_nombre_suelto_con_otro_telefono_es_otra_persona():
    assert buscar_clienta(CLIENTAS, 'Ana', telefono='9847778888') is None


def test_nombre_suelto_de_una_ficha_sin_telefono_coincide():
    assert buscar_clienta(CLIENTAS, 'juli', telefono='9841234567')['id'] == 3


def test_walk_in_y_vacio_nunca_coinciden():
    con_walkin = CLIENTAS + [{'id': 9, 'nombre': 'Walk in', 'apellido': '', 'telefono': '', 'email': ''}]
    assert buscar_clienta(con_walkin, 'Walk in') is None
    assert buscar_clienta(CLIENTAS, '') is None


# ── clienta_para_reserva contra una base en memoria ──

class _Q:
    def __init__(self, db, tabla):
        self.db, self.tabla, self.filtros, self.op = db, tabla, [], None

    def select(self, *_a, **_k): return self
    def range(self, *_a): return self
    def eq(self, k, v): self.filtros.append(lambda r: r.get(k) == v); return self
    def update(self, cambios): self.op = ('update', cambios); return self
    def insert(self, row): self.op = ('insert', row); return self

    def execute(self):
        filas = self.db.setdefault(self.tabla, [])
        if self.op and self.op[0] == 'insert':
            row = {'id': max([r['id'] for r in filas] or [0]) + 1, **self.op[1]}
            filas.append(row)
            return type('R', (), {'data': [row]})()
        rows = [r for r in filas if all(f(r) for f in self.filtros)]
        if self.op:
            for r in rows:
                r.update(self.op[1])
        return type('R', (), {'data': rows})()


class _DB:
    def __init__(self, data): self.data = data
    def table(self, t): return _Q(self.data, t)


def _db():
    return _DB({'clientes_reservas': [dict(c) for c in CLIENTAS]})


def test_reusa_la_existente_y_completa_lo_que_le_falta():
    db = _db()
    cid = clienta_para_reserva(db, {'nombre': 'Juli', 'telefono': '984 123 4567', 'email': 'juli@mail.com'})
    juli = next(c for c in db.data['clientes_reservas'] if c['id'] == 3)
    assert cid == 3 and len(db.data['clientes_reservas']) == 4
    assert juli['telefono'] == '984 123 4567' and juli['email'] == 'juli@mail.com'


def test_no_pisa_datos_que_ya_tiene():
    db = _db()
    clienta_para_reserva(db, {'nombre': 'Jessica Luongo', 'telefono': '9990001111', 'email': 'otro@mail.com'})
    jess = next(c for c in db.data['clientes_reservas'] if c['id'] == 1)
    assert jess['telefono'] == '+52 984 111 2233' and jess['email'] == 'jess@mail.com'


def test_da_de_alta_solo_si_no_existe():
    db = _db()
    cid = clienta_para_reserva(db, {'nombre': 'Marbel Inda', 'telefono': '9841000000'})
    assert cid == 5 and db.data['clientes_reservas'][-1]['nombre'] == 'Marbel Inda'


def test_la_elegida_en_el_buscador_manda():
    db = _db()
    assert clienta_para_reserva(db, {'cliente_id': '2', 'nombre': 'Ana', 'telefono': '9847778888'}) == 2
    with pytest.raises(ReservaError):
        clienta_para_reserva(db, {'cliente_id': 99, 'nombre': 'X', 'telefono': '1'})


def test_bloqueada_no_reserva_online():
    db = _db()
    db.data['clientes_reservas'][1]['bloqueado'] = True
    with pytest.raises(ReservaError) as e:
        clienta_para_reserva(db, {'nombre': 'Ana', 'telefono': '984 000 0001'}, rechazar_bloqueada=True)
    assert e.value.status == 403
    assert clienta_para_reserva(db, {'nombre': 'Ana', 'telefono': '9840000001'}) == 2   # la recepción sí


# ── directorio_clientas ──

def test_directorio_junta_agenda_y_fichas_de_cortes_sin_duplicar():
    cortes = [{'cliente': 'juli', 'fecha': '2026-07-01'}, {'cliente': 'Juli ', 'fecha': '2026-07-20'},
              {'cliente': 'Raquel', 'fecha': '2026-06-02'}, {'cliente': 'Walk in', 'fecha': '2026-06-02'}]
    agenda = [{'id': 3, 'nombre': 'Juli', 'apellido': '', 'telefono': '984'},
              {'id': 8, 'nombre': 'Walk in', 'apellido': '', 'telefono': ''}]
    d = directorio_clientas(agenda, cortes, {'raquel': '9841112222'})
    assert [(c['id'], c['nombre'], c['visitas']) for c in d] == [(3, 'Juli', 2), (None, 'Raquel', 1)]
    assert d[0]['ultima'] == '2026-07-20' and d[1]['telefono'] == '9841112222'
