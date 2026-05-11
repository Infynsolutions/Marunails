import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Package, AlertTriangle, Plus, RefreshCw, History } from 'lucide-react';
import { api } from '../lib/api';
import { formatDate, formatTime } from '../lib/format';

const TABS = [
  { label: 'Productos', value: 'productos' },
  { label: 'Historial de movimientos', value: 'historial' },
];

const MOVEMENT_LABELS = {
  entrada: { label: 'Entrada', color: 'text-green-600 bg-green-500/10' },
  salida:  { label: 'Salida',  color: 'text-red-500 bg-red-500/10' },
  venta:   { label: 'Venta',   color: 'text-blue-600 bg-blue-500/10' },
  ajuste:  { label: 'Ajuste',  color: 'text-amber-600 bg-amber-500/10' },
};

export default function StockPage() {
  const [data, setData] = useState(null);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('productos');

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const [stockResult, movResult] = await Promise.allSettled([
        api.getStock(),
        api.getStockMovements(),
      ]);
      if (stockResult.status === 'fulfilled') setData(stockResult.value);
      else throw new Error(stockResult.reason?.message);
      if (movResult.status === 'fulfilled') setMovements(movResult.value);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-surface-400">
          <RefreshCw size={20} className="animate-spin" />
          <span className="text-sm">Cargando stock...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
        <p className="text-red-400 font-medium mb-2">Error cargando el stock</p>
        <p className="text-red-500/70 text-sm mb-4">{error}</p>
        <button onClick={load} className="text-sm font-medium text-red-400 hover:text-red-300 underline">
          Reintentar
        </button>
      </div>
    );
  }

  const products = data?.products || [];
  const lowStock = products.filter(p => p.current_stock <= p.min_threshold);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Stock</h1>
          <p className="text-xs text-surface-400 mt-1">{products.length} productos · {lowStock.length} con bajo stock</p>
        </div>
        <div className="flex gap-2">
          <Link
            to="/stock/ingresar"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors"
          >
            <Package size={14} />
            Ingresé stock
          </Link>
          <Link
            to="/productos/nuevo"
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-surface-100 border border-surface-200 rounded-xl hover:bg-surface-200 transition-colors text-surface-700"
          >
            <Plus size={14} />
            Nuevo producto
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-5">
        {TABS.map(t => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-sm font-medium transition-colors ${
              tab === t.value
                ? 'bg-argos-600 text-white'
                : 'bg-surface-100 border border-surface-200 text-surface-600 hover:bg-surface-200'
            }`}
          >
            {t.value === 'historial' && <History size={13} />}
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'historial' ? (
        <div className="bg-surface-100 border border-surface-200 rounded-2xl overflow-hidden">
          {movements.length === 0 ? (
            <p className="text-center py-12 text-surface-400 text-sm">Sin movimientos registrados</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-200">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Fecha</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Producto</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Tipo</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Cantidad</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Nota</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((m, i) => {
                  const meta = MOVEMENT_LABELS[m.type] || { label: m.type, color: 'text-surface-600 bg-surface-200' };
                  const isOut = ['salida', 'venta'].includes(m.type) || (m.type === 'ajuste' && m.quantity < 0);
                  return (
                    <tr key={m.id} className={`border-b border-surface-200 last:border-0 ${i % 2 === 0 ? '' : 'bg-surface-50/50'}`}>
                      <td className="px-5 py-3 text-surface-500 whitespace-nowrap">
                        <span className="block">{formatDate(m.date)}</span>
                        <span className="text-[10px] text-surface-400">{formatTime(m.date)}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="font-medium text-surface-800">{m.product_name}</span>
                        <span className="block text-[10px] text-surface-400 font-mono">{m.product_sku}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wide ${meta.color}`}>
                          {meta.label}
                        </span>
                      </td>
                      <td className={`px-5 py-3 text-right font-bold ${isOut ? 'text-red-500' : 'text-green-600'}`}>
                        {isOut ? '-' : '+'}{Math.abs(m.quantity)}
                      </td>
                      <td className="px-5 py-3 text-surface-400 text-xs">{m.note || '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      ) : null}

      {tab === 'productos' && lowStock.length > 0 && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 mb-5 flex items-start gap-3">
          <AlertTriangle size={16} className="text-amber-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-700">
              {lowStock.length} producto{lowStock.length > 1 ? 's' : ''} con bajo stock
            </p>
            <p className="text-xs text-amber-600 mt-0.5">
              {lowStock.map(p => p.name).join(', ')}
            </p>
          </div>
        </div>
      )}

      {tab === 'productos' && (
        products.length === 0 ? (
          <div className="bg-surface-100 border border-surface-200 rounded-2xl p-10 text-center">
            <Package size={32} className="text-surface-300 mx-auto mb-3" />
            <p className="text-surface-500 font-medium mb-1">Sin productos todavía</p>
            <p className="text-surface-400 text-sm mb-4">Agregá tu primer producto para empezar a controlar el stock.</p>
            <Link
              to="/productos/nuevo"
              className="inline-flex items-center gap-2 px-4 py-2 bg-argos-600 text-white rounded-xl text-sm font-medium hover:bg-argos-700 transition-colors"
            >
              <Plus size={14} />
              Agregar producto
            </Link>
          </div>
        ) : (
          <div className="bg-surface-100 border border-surface-200 rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-200">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Producto</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">SKU</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Stock</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Precio</th>
                  <th className="text-right px-5 py-3 text-xs font-semibold text-surface-500 uppercase tracking-wide">Estado</th>
                </tr>
              </thead>
              <tbody>
                {products.map((p, i) => {
                  const isLow = p.current_stock <= p.min_threshold;
                  return (
                    <tr key={p.id} className={`border-b border-surface-200 last:border-0 ${i % 2 === 0 ? '' : 'bg-surface-50/50'}`}>
                      <td className="px-5 py-3 font-medium text-surface-800">{p.name}</td>
                      <td className="px-5 py-3 text-surface-400 font-mono text-xs">{p.sku}</td>
                      <td className="px-5 py-3 text-right font-bold">
                        <span className={isLow ? 'text-red-500' : 'text-surface-800'}>
                          {p.current_stock}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right text-surface-600">
                        ${p.unit_price.toLocaleString('es-AR')}
                      </td>
                      <td className="px-5 py-3 text-right">
                        {isLow ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500/10 text-red-500 rounded-full text-[10px] font-semibold uppercase tracking-wide">
                            <AlertTriangle size={10} /> Bajo stock
                          </span>
                        ) : (
                          <span className="inline-flex px-2 py-0.5 bg-green-500/10 text-green-600 rounded-full text-[10px] font-semibold uppercase tracking-wide">
                            OK
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      )}
    </div>
  );
}
