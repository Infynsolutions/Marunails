import { useState, useEffect } from 'react';
import { RefreshCw, TrendingUp, TrendingDown, Wallet } from 'lucide-react';
import { api } from '../lib/api';
import { formatARS, formatDate, formatTime } from '../lib/format';

const FILTERS = [
  { label: 'Todos', value: 'todos' },
  { label: 'Ingresos', value: 'ingreso' },
  { label: 'Gastos', value: 'gasto' },
];

export default function CajaPage() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('todos');

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getTransactions(500);
      setTransactions(result.transactions || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const totalIngresos = transactions
    .filter(t => t.type === 'ingreso' && t.status !== 'pendiente')
    .reduce((s, t) => s + t.amount, 0);

  const totalGastos = transactions
    .filter(t => t.type === 'gasto' && t.status !== 'pendiente')
    .reduce((s, t) => s + t.amount, 0);

  const saldo = totalIngresos - totalGastos;

  const pendientes = transactions
    .filter(t => t.type === 'ingreso' && t.status === 'pendiente')
    .reduce((s, t) => s + t.amount, 0);

  const filtered = filter === 'todos'
    ? transactions
    : transactions.filter(t => t.type === filter);

  // Running balance (newest first, so we compute from oldest)
  const sorted = [...filtered].sort((a, b) => new Date(a.date) - new Date(b.date));
  let running = 0;
  const withBalance = sorted.map(t => {
    if (t.status !== 'pendiente') {
      running += t.type === 'ingreso' ? t.amount : -t.amount;
    }
    return { ...t, balance: running };
  }).reverse();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-surface-400">
          <RefreshCw size={20} className="animate-spin" />
          <span className="text-sm">Cargando caja...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
        <p className="text-red-400 font-medium mb-2">Error cargando caja</p>
        <p className="text-red-500/70 text-sm mb-4">{error}</p>
        <button onClick={load} className="text-sm font-medium text-red-400 hover:text-red-300 underline">Reintentar</button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-sans text-xl font-bold text-surface-900">Caja</h1>
        <button onClick={load} className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-surface-100 border border-surface-200 rounded-xl hover:bg-surface-200 transition-colors text-surface-700">
          <RefreshCw size={14} />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className={`rounded-2xl border p-5 ${saldo >= 0 ? 'bg-green-500/5 border-green-500/20' : 'bg-red-500/5 border-red-500/20'}`}>
          <div className="flex items-center gap-2 mb-2">
            <Wallet size={15} className={saldo >= 0 ? 'text-green-500' : 'text-red-500'} />
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Saldo de caja</p>
          </div>
          <p className={`text-2xl font-bold ${saldo >= 0 ? 'text-green-600' : 'text-red-500'}`}>
            {formatARS(saldo)}
          </p>
        </div>

        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={15} className="text-green-500" />
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Total ingresos</p>
          </div>
          <p className="text-2xl font-bold text-surface-900">{formatARS(totalIngresos)}</p>
        </div>

        <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown size={15} className="text-red-500" />
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Total gastos</p>
          </div>
          <p className="text-2xl font-bold text-surface-900">{formatARS(totalGastos)}</p>
          {pendientes > 0 && (
            <p className="text-xs text-amber-500 mt-1">{formatARS(pendientes)} pendiente de cobro</p>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {FILTERS.map(f => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-1.5 rounded-xl text-sm font-medium transition-colors ${
              filter === f.value
                ? 'bg-argos-600 text-white'
                : 'bg-surface-100 border border-surface-200 text-surface-600 hover:bg-surface-200'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Movements table */}
      <div className="bg-surface-100 border border-surface-200 rounded-2xl overflow-hidden">
        {withBalance.length === 0 ? (
          <p className="text-center py-12 text-surface-400 text-sm">Sin movimientos registrados</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-200">
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Fecha</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Descripción</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Categoría</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Estado</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Monto</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Saldo</th>
              </tr>
            </thead>
            <tbody>
              {withBalance.map((t, i) => (
                <tr key={t.id} className={`border-b border-surface-200 last:border-0 ${i % 2 === 0 ? '' : 'bg-surface-50/50'}`}>
                  <td className="px-5 py-3 text-surface-500 whitespace-nowrap">
                    <span className="block">{formatDate(t.date)}</span>
                    <span className="text-[10px] text-surface-400">{formatTime(t.date)}</span>
                  </td>
                  <td className="px-5 py-3 text-surface-700 max-w-[200px] truncate">{t.description}</td>
                  <td className="px-5 py-3 text-surface-500">{t.category}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${
                      t.status === 'pendiente'
                        ? 'bg-amber-500/10 text-amber-600'
                        : 'bg-green-500/10 text-green-600'
                    }`}>
                      {t.status}
                    </span>
                  </td>
                  <td className={`px-5 py-3 text-right font-semibold ${t.type === 'ingreso' ? 'text-green-600' : 'text-red-500'}`}>
                    {t.type === 'ingreso' ? '+' : '-'}{formatARS(t.amount)}
                  </td>
                  <td className="px-5 py-3 text-right font-bold text-surface-800">
                    {t.status === 'pendiente' ? '—' : formatARS(t.balance)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
