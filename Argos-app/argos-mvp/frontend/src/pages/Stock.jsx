import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Package, AlertTriangle, Plus, RefreshCw } from 'lucide-react';
import { useApi } from '../lib/useApi';

export default function StockPage() {
  const api = useApi();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function load() {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getStock();
      setData(result);
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

      {lowStock.length > 0 && (
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

      {products.length === 0 ? (
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
      )}
    </div>
  );
}
