import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import { timeAgo } from '../lib/format';

const severityStyles = {
  critica: {
    bg: 'bg-red-500/8',
    border: 'border-red-500/25',
    dot: 'bg-red-500',
    badge: 'bg-red-500/15 text-red-400',
    icon: XCircle,
  },
  advertencia: {
    bg: 'bg-amber-500/8',
    border: 'border-amber-500/25',
    dot: 'bg-amber-500',
    badge: 'bg-amber-500/15 text-amber-400',
    icon: AlertTriangle,
  },
  info: {
    bg: 'bg-blue-500/8',
    border: 'border-blue-500/25',
    dot: 'bg-blue-400',
    badge: 'bg-blue-500/15 text-blue-400',
    icon: AlertTriangle,
  },
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState([]);
  const [counts, setCounts] = useState({});
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  async function loadAlerts() {
    try {
      setLoading(true);
      const res = await api.getAlerts();
      setAlerts(res.alerts || []);
      setCounts(res.counts || {});
    } catch (err) {
      console.error('Error loading alerts:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleResolve(alertId) {
    try {
      await api.resolveAlert(alertId);
      await loadAlerts();
    } catch (err) {
      console.error('Error resolving alert:', err);
    }
  }

  useEffect(() => { loadAlerts(); }, []);

  const filteredAlerts = filter === 'all'
    ? alerts.filter((a) => a.status === 'activa')
    : alerts.filter((a) => a.severity === filter && a.status === 'activa');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-surface-400">
        <RefreshCw size={20} className="animate-spin mr-2" />
        Cargando alertas...
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-sans text-xl font-bold text-surface-900 mb-6">Alertas</h1>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`text-xs font-medium px-4 py-2 rounded-xl border transition-colors ${
            filter === 'all'
              ? 'bg-argos-600 text-white border-argos-600'
              : 'bg-surface-100 text-surface-500 border-surface-200 hover:bg-surface-200'
          }`}
        >
          Todas ({(counts.critica || 0) + (counts.advertencia || 0)})
        </button>
        <button
          onClick={() => setFilter('critica')}
          className={`text-xs font-medium px-4 py-2 rounded-xl border transition-colors ${
            filter === 'critica'
              ? 'bg-red-600 text-white border-red-600'
              : 'bg-surface-100 text-surface-500 border-surface-200 hover:bg-red-500/10'
          }`}
        >
          🔴 Críticas ({counts.critica || 0})
        </button>
        <button
          onClick={() => setFilter('advertencia')}
          className={`text-xs font-medium px-4 py-2 rounded-xl border transition-colors ${
            filter === 'advertencia'
              ? 'bg-amber-500 text-white border-amber-500'
              : 'bg-surface-100 text-surface-500 border-surface-200 hover:bg-amber-500/10'
          }`}
        >
          ⚠️ Advertencias ({counts.advertencia || 0})
        </button>
      </div>

      {/* Alert list */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-16">
            <CheckCircle size={40} className="text-argos-400 mx-auto mb-3" />
            <p className="font-sans font-bold text-surface-700">Todo tranquilo</p>
            <p className="text-sm text-surface-400 mt-1">No hay alertas activas en esta categoría</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const style = severityStyles[alert.severity] || severityStyles.info;
            return (
              <div key={alert.id} className={`${style.bg} border ${style.border} rounded-2xl p-5 flex gap-4`}>
                <div className={`w-3 h-3 ${style.dot} rounded-full flex-shrink-0 mt-1`} />
                <div className="flex-1">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-sm text-surface-800">{alert.title}</p>
                      <p className="text-sm text-surface-500 mt-1 leading-relaxed">{alert.body}</p>
                    </div>
                    <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${style.badge}`}>
                      {alert.severity}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-3">
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="text-xs font-medium text-surface-500 border border-surface-200 bg-surface-100 px-3 py-1.5 rounded-lg hover:bg-surface-200 transition-colors"
                    >
                      ✓ Marcar resuelta
                    </button>
                    <span className="text-xs text-surface-400">{timeAgo(alert.created_at)}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
