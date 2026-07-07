import csv
import re
import sys
from supabase import create_client

SUPABASE_URL = 'https://dbhxrboacqppximbcokz.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRiaHhyYm9hY3FwcHhpbWJjb2t6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0Mjg1NDMsImV4cCI6MjA5OTAwNDU0M30.fcVl9hwRTACJrp4BH7CZdj5ZzPa7-VaAqJlUdHH-NKs'

MESES_ES = {
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
}

def parse_num(s):
    if not s or not str(s).strip():
        return 0.0
    s = str(s).strip().replace('$', '').replace(' ', '').replace('\xa0', '').replace(' ', '')
    if not s or s == '-':
        return 0.0
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def parse_fecha(s):
    if not s or not s.strip():
        return None
    s = s.strip()

    # DD-mes-YYYY
    m = re.match(r'^(\d{1,2})-(\w+)-(\d{4})$', s)
    if m:
        day, mes, year = m.groups()
        mes_num = MESES_ES.get(mes.lower()[:3])
        if mes_num:
            return f"{year}-{mes_num:02d}-{int(day):02d}"

    # D-mes-YYYY (already matched above)

    # YYYY-MM-DD
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', s)
    if m:
        return s

    # DD/MM (no year) → assume 2026
    m = re.match(r'^(\d{1,2})/(\d{1,2})$', s)
    if m:
        day, month = m.groups()
        return f"2026-{int(month):02d}-{int(day):02d}"

    # DD/MM/YYYY
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', s)
    if m:
        day, month, year = m.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return None

def get_week_quincena(fecha_str):
    from datetime import date
    if not fecha_str:
        return None, None, None
    try:
        d = date.fromisoformat(fecha_str)
        semana = d.isocalendar()[1]
        mes = d.strftime('%Y-%m')
        q = 'Q1' if d.day <= 15 else 'Q2'
        return semana, mes, f'{mes}-{q}'
    except:
        return None, None, None

def migrate_cortes(sb, filepath):
    print(f'\nMigrando CORTES desde {filepath}...')
    rows_ok = 0
    rows_skip = 0

    with open(filepath, encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    # Find header row (contains "Fecha" and "Staff")
    data_start = 0
    for i, row in enumerate(all_rows):
        if row and 'Fecha' in row[0] and len(row) > 2 and 'Staff' in row[2]:
            data_start = i + 1
            break

    batch = []
    for row in all_rows[data_start:]:
        if len(row) < 9:
            continue

        fecha_str = parse_fecha(row[0])
        if not fecha_str:
            rows_skip += 1
            continue

        staff = row[2].strip() if len(row) > 2 else ''
        servicio = row[3].strip() if len(row) > 3 else ''
        if not staff or not servicio:
            rows_skip += 1
            continue

        total_cobrado = parse_num(row[5]) if len(row) > 5 else 0
        medio_pago = row[7].strip() if len(row) > 7 else ''
        if not medio_pago:
            medio_pago = 'Otro'

        propina = parse_num(row[6]) if len(row) > 6 else 0
        moneda = row[4].strip() if len(row) > 4 else 'MXN'
        if not moneda:
            moneda = 'MXN'
        notas = row[8].strip() if len(row) > 8 else ''
        cliente = row[1].strip() if len(row) > 1 else 'Walk in'
        if not cliente:
            cliente = 'Walk in'

        tc = parse_num(row[10]) if len(row) > 10 else 1
        if tc == 0:
            tc = 1

        total_mxn = parse_num(row[11]) if len(row) > 11 else round(total_cobrado * tc, 2)
        propina_mxn = parse_num(row[12]) if len(row) > 12 else round(propina * tc, 2)
        neto_mxn = parse_num(row[13]) if len(row) > 13 else round((total_cobrado - propina) * tc, 2)
        mes_col = row[14].strip() if len(row) > 14 else ''
        semana_col = row[15].strip() if len(row) > 15 else ''
        quincena_col = row[16].strip() if len(row) > 16 else ''

        semana, mes, quincena = get_week_quincena(fecha_str)
        if mes_col and re.match(r'\d{4}-\d{2}', mes_col):
            mes = mes_col
        if semana_col:
            try:
                semana = int(semana_col)
            except:
                pass
        if quincena_col and '-Q' in quincena_col:
            quincena = quincena_col

        batch.append({
            'fecha': fecha_str,
            'cliente': cliente[:200],
            'staff': staff[:100],
            'servicio': servicio[:100],
            'moneda': moneda[:10],
            'total_cobrado': total_cobrado,
            'propina': propina,
            'medio_pago': medio_pago[:50],
            'notas': notas[:500],
            'venta_neta': round(total_cobrado - propina, 2),
            'tc': tc,
            'total_mxn': total_mxn,
            'propina_mxn': propina_mxn,
            'neto_mxn': neto_mxn,
            'mes': mes,
            'semana': semana,
            'quincena': quincena,
        })

        if len(batch) >= 100:
            sb.table('cortes').insert(batch).execute()
            rows_ok += len(batch)
            print(f'  Insertadas {rows_ok} filas...')
            batch = []

    if batch:
        sb.table('cortes').insert(batch).execute()
        rows_ok += len(batch)

    print(f'CORTES: {rows_ok} insertadas, {rows_skip} omitidas.')

def migrate_gastos(sb, filepath):
    print(f'\nMigrando GASTOS desde {filepath}...')
    rows_ok = 0
    rows_skip = 0

    with open(filepath, encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    # Find header row
    data_start = 0
    for i, row in enumerate(all_rows):
        if row and 'Fecha' in row[0] and len(row) > 1 and ('ategor' in row[1] or 'Categor' in row[1]):
            data_start = i + 1
            break

    batch = []
    for row in all_rows[data_start:]:
        if len(row) < 7:
            continue

        fecha_str = parse_fecha(row[0])
        if not fecha_str:
            rows_skip += 1
            continue

        categoria = row[1].strip() if len(row) > 1 else ''
        importe = parse_num(row[6]) if len(row) > 6 else 0
        medio_pago = row[7].strip() if len(row) > 7 else ''
        if not medio_pago:
            medio_pago = 'Otro'

        subcategoria = row[2].strip() if len(row) > 2 else ''
        proveedor = row[3].strip() if len(row) > 3 else ''
        descripcion = row[4].strip() if len(row) > 4 else ''
        moneda = row[5].strip() if len(row) > 5 else 'MXN'
        if not moneda:
            moneda = 'MXN'
        notas = row[8].strip() if len(row) > 8 else ''

        tc = parse_num(row[9]) if len(row) > 9 else 1
        if tc == 0:
            tc = 1

        importe_mxn = parse_num(row[10]) if len(row) > 10 else round(importe * tc, 2)
        mes_col = row[11].strip() if len(row) > 11 else ''
        semana_col = row[12].strip() if len(row) > 12 else ''
        quincena_col = row[13].strip() if len(row) > 13 else ''

        semana, mes, quincena = get_week_quincena(fecha_str)
        if mes_col and re.match(r'\d{4}-\d{2}', mes_col):
            mes = mes_col
        if semana_col:
            try:
                semana = int(semana_col)
            except:
                pass
        if quincena_col and '-Q' in quincena_col:
            quincena = quincena_col

        batch.append({
            'fecha': fecha_str,
            'categoria': (categoria or 'Otros')[:100],
            'subcategoria': subcategoria[:200],
            'proveedor': proveedor[:200],
            'descripcion': descripcion[:500],
            'moneda': moneda[:10],
            'importe': importe,
            'medio_pago': medio_pago[:50],
            'notas': notas[:500],
            'tc': tc,
            'importe_mxn': importe_mxn,
            'mes': mes,
            'semana': semana,
            'quincena': quincena,
        })

        if len(batch) >= 100:
            sb.table('gastos').insert(batch).execute()
            rows_ok += len(batch)
            print(f'  Insertadas {rows_ok} filas...')
            batch = []

    if batch:
        sb.table('gastos').insert(batch).execute()
        rows_ok += len(batch)

    print(f'GASTOS: {rows_ok} insertadas, {rows_skip} omitidas.')

if __name__ == '__main__':
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    cortes_csv = 'MaruNails_Dashboard 2026 - INPUT_CORTES.csv'
    gastos_csv = 'MaruNails_Dashboard 2026 - INPUT_GASTOS.csv'

    migrate_cortes(sb, cortes_csv)
    migrate_gastos(sb, gastos_csv)

    print('\nMigracion completada.')
