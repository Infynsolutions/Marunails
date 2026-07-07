import { Bot, Sparkles } from 'lucide-react';

const agents = [
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
    emoji: '📬',
    name: 'Cobrador de Facturas',
    role: 'Cobranzas',
    desc: 'Monitorea facturas vencidas, prioriza cobranzas y genera alertas de aging.',
    tags: ['Alertas +60 días', 'Priorización', 'Aging'],
    status: 'active',
    analyses: 89,
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
        {agents.map((agent, i) => (
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
