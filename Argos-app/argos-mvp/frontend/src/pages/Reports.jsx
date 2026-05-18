import { useState, useEffect } from 'react';
import { RefreshCw, Printer, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { api } from '../lib/api';
import { formatARS, formatDate } from '../lib/format';

const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
];

function buildMonthOptions() {
  const now = new Date();
  const options = [];
  for (let i = 0; i < 6; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    options.push({ year: d.getFullYear(), month: d.getMonth() + 1, label: `${MESES[d.getMonth()]} ${d.getFullYear()}` });
  }
  return options;
}

function ChangeChip({ value, suffix = '%', inverse = false }) {
  if (value == null) return null;
  const positive = inverse ? value < 0 : value >= 0;
  const sign = value >= 0 ? '+' : '';
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${positive ? 'text-green-600' : 'text-red-500'}`}>
      {positive ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
      {sign}{value.toFixed(1)}{suffix} vs mes ant.
    </span>
  );
}

function CategoryBar({ label, amount, percentage, color }) {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="w-28 sm:w-36 text-xs text-surface-600 truncate flex-shrink-0">{label}</div>
      <div className="flex-1 h-1.5 bg-surface-200 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${percentage}%`, backgroundColor: color }} />
      </div>
      <div className="text-right w-20 flex-shrink-0">
        <span className="text-xs font-semibold text-surface-800">{formatARS(amount)}</span>
        <span className="text-[10px] text-surface-400 ml-1">{percentage}%</span>
      </div>
    </div>
  );
}

const EXPENSE_COLORS = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#06b6d4', '#8b5cf6', '#ec4899'];
const INCOME_COLORS  = ['#16a34a', '#22c55e', '#4ade80', '#059669', '#10b981', '#34d399'];

export default function ReportsPage() {
  const monthOptions = buildMonthOptions();
  const [selected, setSelected] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load(idx) {
    const { year, month } = monthOptions[idx];
    try {
      setLoading(true);
      setError(null);
      const result = await api.getReport(year, month);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(selected); }, [selected]);

  function handleMonthChange(e) {
    const idx = Number(e.target.value);
    setSelected(idx);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-surface-400">
          <RefreshCw size={20} className="animate-spin" />
          <span className="text-sm">Generando reporte...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
        <p className="text-red-400 font-medium mb-2">Error cargando el reporte</p>
        <p className="text-red-500/70 text-sm mb-4">{error}</p>
        <button onClick={() => load(selected)} className="text-sm font-medium text-red-400 hover:text-red-300 underline">
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) return null;

  const saldoPositivo = data.saldo >= 0;

  return (
    <div className="print:p-0">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6 print:mb-4">
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Reporte mensual</h1>
          <p className="text-xs text-surface-400 mt-0.5">Estado de resultados · {data.month_label}</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selected}
            onChange={handleMonthChange}
            className="text-sm border border-surface-200 rounded-xl px-3 py-2 bg-surface-100 text-surface-700 focus:outline-none focus:ring-2 focus:ring-argos-400/30 print:hidden"
          >
            {monthOptions.map((opt, i) => (
              <option key={i} value={i}>{opt.label}</option>
            ))}
          </select>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-surface-100 border border-surface-200 rounded-xl hover:bg-surface-200 transition-colors text-surface-700 print:hidden"
          >
            <Printer size={14} />
            Imprimir
          </button>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {/* Ingresos */}
        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-4">
          <p className="text-xs text-surface-400 font-medium uppercase tracking-wide mb-1">Ingresos</p>
          <p className="font-sans text-xl font-bold text-green-600">{data.formatted_ingresos}</p>
          <div className="mt-1">
            <ChangeChip value={data.ingresos_change} />
          </div>
        </div>

        {/* Gastos */}
        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-4">
          <p className="text-xs text-surface-400 font-medium uppercase tracking-wide mb-1">Gastos</p>
          <p className="font-sans text-xl font-bold text-red-500">{data.formatted_gastos}</p>
          <div className="mt-1">
            <ChangeChip value={data.gastos_change} inverse />
          </div>
        </div>

        {/* Margen */}
        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-4">
          <p className="text-xs text-surface-400 font-medium uppercase tracking-wide mb-1">Margen bruto</p>
          <p className="font-sans text-xl font-bold text-surface-900">{data.margen.toFixed(1)}%</p>
          <div className="mt-1">
            <ChangeChip value={data.margen - data.margen_prev} suffix="pp" />
          </div>
        </div>

        {/* Saldo */}
        <div className={`rounded-2xl p-4 border ${saldoPositivo ? 'bg-green-500/8 border-green-500/20' : 'bg-red-500/8 border-red-500/20'}`}>
          <p className="text-xs text-surface-400 font-medium uppercase tracking-wide mb-1">Saldo neto</p>
          <p className={`font-sans text-xl font-bold ${saldoPositivo ? 'text-green-600' : 'text-red-500'}`}>
            {data.formatted_saldo}
          </p>
          <p className="text-[10px] text-surface-400 mt-1">
            {saldoPositivo ? 'El negocio generó ganancia' : 'El negocio operó en pérdida'}
          </p>
        </div>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
        {/* Gastos por categoría */}
        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
          <h2 className="font-sans text-sm font-bold text-surface-800 mb-1">Gastos por categoría</h2>
          <p className="text-xs text-surface-400 mb-4">Total: {data.formatted_gastos}</p>
          {data.gastos_por_categoria.length === 0 ? (
            <p className="text-sm text-surface-400 py-4 text-center">Sin gastos este mes</p>
          ) : (
            <div className="divide-y divide-surface-200">
              {data.gastos_por_categoria.map((cat, i) => (
                <CategoryBar
                  key={cat.category}
                  label={cat.category}
                  amount={cat.amount}
                  percentage={cat.percentage}
                  color={EXPENSE_COLORS[i % EXPENSE_COLORS.length]}
                />
              ))}
            </div>
          )}
        </div>

        {/* Ingresos por categoría */}
        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
          <h2 className="font-sans text-sm font-bold text-surface-800 mb-1">Ingresos por categoría</h2>
          <p className="text-xs text-surface-400 mb-4">Total: {data.formatted_ingresos}</p>
          {data.ingresos_por_categoria.length === 0 ? (
            <p className="text-sm text-surface-400 py-4 text-center">Sin ingresos este mes</p>
          ) : (
            <div className="divide-y divide-surface-200">
              {data.ingresos_por_categoria.map((cat, i) => (
                <CategoryBar
                  key={cat.category}
                  label={cat.category}
                  amount={cat.amount}
                  percentage={cat.percentage}
                  color={INCOME_COLORS[i % INCOME_COLORS.length]}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Transactions table */}
      <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
        <h2 className="font-sans text-sm font-bold text-surface-800 mb-4">
          Transacciones de {data.month_label}
          <span className="ml-2 text-xs font-normal text-surface-400">({data.transacciones.length} registros)</span>
        </h2>

        {data.transacciones.length === 0 ? (
          <p className="text-sm text-surface-400 py-8 text-center">No hay transacciones este mes</p>
        ) : (
          <div className="overflow-x-auto -mx-1">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-200">
                  <th className="text-left text-xs text-surface-400 font-medium pb-2 pr-4">Fecha</th>
                  <th className="text-left text-xs text-surface-400 font-medium pb-2 pr-4">Descripción</th>
                  <th className="text-left text-xs text-surface-400 font-medium pb-2 pr-4 hidden sm:table-cell">Categoría</th>
                  <th className="text-right text-xs text-surface-400 font-medium pb-2 pr-4">Monto</th>
                  <th className="text-left text-xs text-surface-400 font-medium pb-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {data.transacciones.map((tx, i) => {
                  const isIngreso = tx.type === 'ingreso';
                  const isPending = tx.status === 'pendiente';
                  return (
                    <tr key={tx.id || i} className="border-b border-surface-200/50 hover:bg-surface-200/30">
                      <td className="py-2.5 pr-4 text-xs text-surface-500 whitespace-nowrap">
                        {formatDate(tx.date)}
                      </td>
                      <td className="py-2.5 pr-4 text-surface-700 max-w-[180px] truncate">
                        {tx.description || '—'}
                      </td>
                      <td className="py-2.5 pr-4 text-xs text-surface-500 hidden sm:table-cell">
                        {tx.category || '—'}
                      </td>
                      <td className={`py-2.5 pr-4 text-right font-semibold whitespace-nowrap ${isIngreso ? 'text-green-600' : 'text-red-500'}`}>
                        {isIngreso ? '+' : '-'}{formatARS(tx.amount)}
                      </td>
                      <td className="py-2.5">
                        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                          isPending
                            ? 'bg-amber-500/15 text-amber-600'
                            : 'bg-green-500/15 text-green-600'
                        }`}>
                          {isPending ? 'Pendiente' : isIngreso ? 'Cobrado' : 'Pagado'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Print footer */}
      <div className="hidden print:block mt-8 pt-4 border-t border-surface-200 text-xs text-surface-400 text-center">
        Reporte generado por Argos · {data.month_label}
      </div>
    </div>
  );
}
