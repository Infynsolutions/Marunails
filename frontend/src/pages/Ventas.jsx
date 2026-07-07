import { useState, useEffect } from 'react';
import { RefreshCw, ShoppingCart, Clock, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { formatARS, formatDate, formatTime } from '../lib/format';

const STATUS_FILTERS = [
  { label: 'Todas', value: 'todas' },
  { label: 'Cobradas', value: 'cobrado' },
  { label: 'Pendientes', value: 'pendiente' },
];

export default function VentasPage() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('todas');

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getTransactions(500);
      const ventas = (result.transactions || []).filter(t => t.type === 'ingreso');
      setTransactions(ventas);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const totalCobrado = transactions
    .filter(t => t.status === 'cobrado')
    .reduce((s, t) => s + t.amount, 0);

  const totalPendiente = transactions
    .filter(t => t.status === 'pendiente')
    .reduce((s, t) => s + t.amount, 0);

  const filtered = statusFilter === 'todas'
    ? transactions
    : transactions.filter(t => t.status === statusFilter);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-surface-400">
          <RefreshCw size={20} className="animate-spin" />
          <span className="text-sm">Cargando ventas...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
        <p className="text-red-400 font-medium mb-2">Error cargando ventas</p>
        <p className="text-red-500/70 text-sm mb-4">{error}</p>
        <button onClick={load} className="text-sm font-medium text-red-400 hover:text-red-300 underline">Reintentar</button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Historial de ventas</h1>
          <p className="text-xs text-surface-400 mt-1">{transactions.length} ventas registradas</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/venta/nueva"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors"
          >
            <ShoppingCart size={14} />
            Nueva venta
          </Link>
          <button onClick={load} className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-surface-100 border border-surface-200 rounded-xl hover:bg-surface-200 transition-colors text-surface-700">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div className="bg-green-500/5 border border-green-500/20 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle size={15} className="text-green-500" />
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Cobrado</p>
          </div>
          <p className="text-2xl font-bold text-green-600">{formatARS(totalCobrado)}</p>
          <p className="text-xs text-surface-400 mt-1">
            {transactions.filter(t => t.status === 'cobrado').length} ventas
          </p>
        </div>
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-5">
          <div className="flex items-center gap-2 mb-2">
            <Clock size={15} className="text-amber-500" />
            <p className="text-xs font-semibold text-surface-500 uppercase tracking-wide">Pendiente de cobro</p>
          </div>
          <p className="text-2xl font-bold text-amber-600">{formatARS(totalPendiente)}</p>
          <p className="text-xs text-surface-400 mt-1">
            {transactions.filter(t => t.status === 'pendiente').length} ventas
          </p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        {STATUS_FILTERS.map(f => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={`px-4 py-1.5 rounded-xl text-sm font-medium transition-colors ${
              statusFilter === f.value
                ? 'bg-argos-600 text-white'
                : 'bg-surface-100 border border-surface-200 text-surface-600 hover:bg-surface-200'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-surface-100 border border-surface-200 rounded-2xl overflow-hidden">
        {filtered.length === 0 ? (
          <div className="text-center py-12">
            <ShoppingCart size={32} className="text-surface-300 mx-auto mb-3" />
            <p className="text-surface-500 font-medium mb-1">Sin ventas registradas</p>
            <Link to="/venta/nueva" className="text-sm text-argos-400 hover:text-argos-500 font-medium">
              Registrar primera venta →
            </Link>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-200">
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Fecha</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Descripción</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Categoría</th>
                <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Estado</th>
                <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Monto</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t, i) => (
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
                  <td className="px-5 py-3 text-right font-semibold text-green-600">
                    +{formatARS(t.amount)}
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
