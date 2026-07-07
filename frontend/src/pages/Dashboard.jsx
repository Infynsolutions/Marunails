import { useState, useEffect } from 'react';
import { RefreshCw, Clock, AlertTriangle, Package, ShoppingCart, Receipt } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { timeAgo } from '../lib/format';
import KPICard from '../components/KPICard';
import RevenueChart from '../components/RevenueChart';
import CategoryChart from '../components/CategoryChart';
import TransactionsTable from '../components/TransactionsTable';

const kpiColors = ['green', 'red', 'green', 'amber'];

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [stock, setStock] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadDashboard() {
    try {
      setLoading(true);
      setError(null);
      const [dash, stockData] = await Promise.allSettled([
        api.getDashboard(),
        api.getStock(),
      ]);
      if (dash.status === 'fulfilled') setData(dash.value);
      else throw new Error(dash.reason?.message);
      if (stockData.status === 'fulfilled') setStock(stockData.value);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadDashboard(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center gap-3 text-surface-400">
          <RefreshCw size={20} className="animate-spin" />
          <span className="text-sm">Cargando dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-2xl p-6 text-center">
        <p className="text-red-400 font-medium mb-2">Error cargando el dashboard</p>
        <p className="text-red-500/70 text-sm mb-4">{error}</p>
        <button
          onClick={loadDashboard}
          className="text-sm font-medium text-red-400 hover:text-red-300 underline"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Dashboard</h1>
          {data.last_sync && (
            <p className="text-xs text-surface-400 mt-1 flex items-center gap-1">
              <Clock size={12} />
              Última actividad {timeAgo(data.last_sync)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Link to="/venta/nueva" className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors">
            <ShoppingCart size={14} />
            Venta
          </Link>
          <Link to="/gasto/nuevo" className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-red-500 text-white rounded-xl hover:bg-red-600 transition-colors">
            <Receipt size={14} />
            Gasto
          </Link>
          <button onClick={loadDashboard} className="flex items-center gap-2 px-3 py-2 text-sm font-medium bg-surface-100 border border-surface-200 rounded-xl hover:bg-surface-200 transition-colors text-surface-700">
            <RefreshCw size={14} />
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {data.kpis.map((kpi, i) => (
          <KPICard
            key={i}
            label={kpi.label}
            formatted={kpi.formatted}
            changePct={kpi.change_pct}
            changeLabel={kpi.change_label}
            trend={kpi.trend}
            sparkline={kpi.sparkline}
            color={kpiColors[i]}
          />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 mb-6">
        <div className="lg:col-span-3 bg-surface-100 rounded-2xl border border-surface-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="font-sans text-sm font-bold text-surface-800">Ingresos vs Gastos</h2>
              <p className="text-xs text-surface-400 mt-0.5">Últimos 7 meses</p>
            </div>
          </div>
          <RevenueChart data={data.monthly_chart} />
        </div>
        <div className="lg:col-span-2 bg-surface-100 rounded-2xl border border-surface-200 p-5">
          <div className="mb-4">
            <h2 className="font-sans text-sm font-bold text-surface-800">Distribución</h2>
            <p className="text-xs text-surface-400 mt-0.5">Por categoría</p>
          </div>
          <CategoryChart data={data.category_breakdown} />
        </div>
      </div>

      {/* Stock section */}
      {stock && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-sans text-sm font-bold text-surface-800">Stock</h2>
            <Link to="/stock" className="text-xs text-argos-400 hover:text-argos-500 font-medium">
              Ver todo →
            </Link>
          </div>
          {stock.low_stock_count > 0 && (
            <Link to="/stock" className="flex items-center gap-3 bg-amber-500/10 border border-amber-500/30 rounded-xl p-3 mb-3 hover:bg-amber-500/15 transition-colors">
              <AlertTriangle size={15} className="text-amber-500 flex-shrink-0" />
              <span className="text-sm text-amber-700 font-medium">
                {stock.low_stock_count} producto{stock.low_stock_count > 1 ? 's' : ''} con bajo stock
              </span>
            </Link>
          )}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
            {stock.products.slice(0, 5).map(p => {
              const isLow = p.current_stock <= p.min_threshold;
              return (
                <div key={p.id} className="bg-surface-100 border border-surface-200 rounded-xl p-3">
                  <p className="text-xs text-surface-500 truncate mb-1">{p.name}</p>
                  <p className={`text-xl font-bold ${isLow ? 'text-red-500' : 'text-surface-900'}`}>
                    {p.current_stock}
                  </p>
                  <p className="text-[10px] text-surface-400 mt-0.5">unidades</p>
                  {isLow && (
                    <span className="inline-flex items-center gap-0.5 mt-1.5 px-1.5 py-0.5 bg-red-500/10 text-red-500 rounded text-[9px] font-semibold uppercase tracking-wide">
                      <AlertTriangle size={8} /> Bajo
                    </span>
                  )}
                </div>
              );
            })}
            {stock.products.length === 0 && (
              <Link to="/productos/nuevo" className="col-span-full flex items-center gap-2 bg-surface-100 border border-dashed border-surface-300 rounded-xl p-4 text-sm text-surface-400 hover:text-surface-600 hover:border-surface-400 transition-colors">
                <Package size={16} />
                Agregar primer producto
              </Link>
            )}
          </div>
        </div>
      )}

      {/* Transactions */}
      <div className="bg-surface-100 rounded-2xl border border-surface-200 p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-sans text-sm font-bold text-surface-800">Últimas transacciones</h2>
        </div>
        <TransactionsTable transactions={data.recent_transactions} />
      </div>
    </div>
  );
}
