import { useState, useEffect } from 'react';
import { Bot, Sparkles, RefreshCw, AlertCircle, Clock, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';
import { useApi } from '../lib/useApi';
import { formatARS, formatDate } from '../lib/format';

function BucketBadge({ bucket }) {
  const map = {
    al_dia:     { label: 'Al día',      cls: 'bg-green-500/15 text-green-600' },
    por_vencer: { label: 'Por vencer',  cls: 'bg-amber-500/15 text-amber-600' },
    vencida:    { label: 'Vencida',     cls: 'bg-red-500/15 text-red-500' },
  };
  const { label, cls } = map[bucket] || { label: bucket, cls: 'bg-surface-200 text-surface-500' };
  return <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${cls}`}>{label}</span>;
}

function CollectionsAgent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    api.getCollections()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  const allItems = data ? [...data.vencidas, ...data.por_vencer, ...data.al_dia] : [];

  return (
    <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5 hover:border-argos-400/30 transition-all">
      <div className="flex items-start justify-between mb-3">
        <span className="text-3xl">📬</span>
        <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-argos-400/15 text-argos-300">
          ● Activo
        </span>
      </div>

      <p className="font-sans font-bold text-surface-900">Cobrador de Facturas</p>
      <p className="text-[10px] text-argos-400 uppercase tracking-wider mt-0.5 font-semibold">Cobranzas · Argos</p>
      <p className="text-sm text-surface-500 mt-2 leading-relaxed">
        Monitorea facturas vencidas, prioriza cobranzas y genera alertas de aging.
      </p>

      {/* Real data summary */}
      {loading ? (
        <div className="flex items-center gap-2 mt-4 text-surface-400 text-xs">
          <RefreshCw size={12} className="animate-spin" />
          Analizando cobranzas...
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-3 gap-2 mt-4">
            <div className="bg-red-500/8 border border-red-500/20 rounded-xl p-2.5 text-center">
              <p className="font-bold text-red-500 text-lg">{data.vencidas.length}</p>
              <p className="text-[10px] text-surface-500">Vencidas</p>
            </div>
            <div className="bg-amber-500/8 border border-amber-500/20 rounded-xl p-2.5 text-center">
              <p className="font-bold text-amber-600 text-lg">{data.por_vencer.length}</p>
              <p className="text-[10px] text-surface-500">Por vencer</p>
            </div>
            <div className="bg-surface-200/50 border border-surface-200 rounded-xl p-2.5 text-center">
              <p className="font-bold text-surface-700 text-lg">{data.al_dia.length}</p>
              <p className="text-[10px] text-surface-500">Al día</p>
            </div>
          </div>

          <div className="border-t border-surface-200 mt-4 pt-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-surface-400">Total pendiente</p>
                <p className="font-sans font-bold text-lg text-surface-900">{data.formatted_total}</p>
              </div>
              {data.total_count > 0 && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="flex items-center gap-1 text-xs font-medium text-argos-400 hover:text-argos-500"
                >
                  {expanded ? 'Ocultar' : 'Ver detalle'}
                  {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                </button>
              )}
            </div>

            {expanded && allItems.length > 0 && (
              <div className="mt-3 space-y-1.5 max-h-60 overflow-y-auto">
                {allItems.map((item) => (
                  <div key={item.id} className="flex items-center gap-2 bg-surface-50 border border-surface-200 rounded-lg px-3 py-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-surface-800 truncate">{item.description || item.category || 'Sin descripción'}</p>
                      <p className="text-[10px] text-surface-400">{formatDate(item.date)} · {item.days_pending}d pendiente</p>
                    </div>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className="text-xs font-semibold text-surface-800">{item.formatted_amount}</span>
                      <BucketBadge bucket={item.bucket} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {data.total_count === 0 && (
              <div className="flex items-center gap-2 mt-2 text-green-600 text-xs">
                <CheckCircle2 size={12} />
                Sin cobranzas pendientes
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="flex items-center gap-2 mt-4 text-surface-400 text-xs">
          <AlertCircle size={12} />
          No se pudo cargar el análisis
        </div>
      )}
    </div>
  );
}

const staticAgents = [
  {
    emoji: '📊',
    name: 'Analista Financiero',
    role: 'Finanzas',
    desc: 'Analiza estados financieros, identifica tendencias y genera reportes ejecutivos automáticamente.',
    tags: ['P&L automático', 'Anomalías', 'Proyecciones'],
    status: 'active',
    analyses: 142,
  },
  {
    emoji: '💡',
    name: 'Optimizador de Gastos',
    role: 'Costos',
    desc: 'Identifica oportunidades de ahorro, detecta duplicados y sugiere renegociaciones.',
    tags: ['Análisis costos', 'Duplicados', 'Sugerencias'],
    status: 'idle',
    analyses: 34,
  },
];

export default function AgentsPage() {
  const api = useApi(); // eslint-disable-line no-unused-vars
  return (
    <div>
      <h1 className="font-sans text-xl font-bold text-surface-900 mb-6">Agentes</h1>

      {/* Argos highlight */}
      <div className="bg-argos-400/8 border border-argos-400/20 rounded-2xl p-6 flex items-center gap-5 mb-6">
        <div className="w-14 h-14 bg-gradient-to-br from-argos-400 to-argos-600 rounded-2xl flex items-center justify-center shadow-lg shadow-argos-600/25 flex-shrink-0">
          <Sparkles size={24} className="text-white" />
        </div>
        <div className="flex-1">
          <p className="font-sans font-bold text-lg text-surface-900">ARGOS — Tu Copiloto IA</p>
          <p className="text-sm text-surface-500 mt-1">Analiza tu operación en tiempo real y proactivamente te avisa antes de que preguntes</p>
        </div>
      </div>

      {/* Agent cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Real collections agent first */}
        <CollectionsAgent />

        {staticAgents.map((agent, i) => (
          <div key={i} className="bg-surface-100 border border-surface-200 rounded-2xl p-5 hover:border-argos-400/30 transition-all">
            <div className="flex items-start justify-between mb-3">
              <span className="text-3xl">{agent.emoji}</span>
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                agent.status === 'active' ? 'bg-argos-400/15 text-argos-300' : 'bg-surface-200 text-surface-500'
              }`}>
                {agent.status === 'active' ? '● Activo' : 'Inactivo'}
              </span>
            </div>
            <p className="font-sans font-bold text-surface-900">{agent.name}</p>
            <p className="text-[10px] text-argos-400 uppercase tracking-wider mt-0.5 font-semibold">{agent.role} · Argos</p>
            <p className="text-sm text-surface-500 mt-2 leading-relaxed">{agent.desc}</p>
            <div className="flex flex-wrap gap-1.5 mt-3">
              {agent.tags.map((tag, j) => (
                <span key={j} className="text-[10px] bg-surface-200 text-surface-500 px-2 py-0.5 rounded">
                  {tag}
                </span>
              ))}
            </div>
            <div className="border-t border-surface-200 mt-4 pt-3 flex items-center justify-between">
              <div>
                <span className="font-sans font-bold text-lg text-argos-400">{agent.analyses}</span>
                <span className="text-xs text-surface-400 ml-1">análisis</span>
              </div>
              <button className={`text-xs font-medium px-3 py-1.5 rounded-lg border transition-colors ${
                agent.status === 'active'
                  ? 'border-surface-200 text-surface-500 hover:bg-surface-200'
                  : 'bg-argos-600 text-white border-argos-600 hover:bg-argos-500'
              }`}>
                {agent.status === 'active' ? '⏸ Pausar' : '▶ Activar'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
