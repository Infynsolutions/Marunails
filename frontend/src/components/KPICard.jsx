import { TrendingUp, TrendingDown } from 'lucide-react';

const colorMap = {
  green: {
    border: 'border-argos-400',
    text: 'text-argos-400',
    badge: 'bg-argos-400/15 text-argos-300',
  },
  red: {
    border: 'border-red-500',
    text: 'text-red-500',
    badge: 'bg-red-500/15 text-red-400',
  },
  amber: {
    border: 'border-amber-500',
    text: 'text-amber-500',
    badge: 'bg-amber-500/15 text-amber-400',
  },
  blue: {
    border: 'border-blue-400',
    text: 'text-blue-400',
    badge: 'bg-blue-400/15 text-blue-300',
  },
};

export default function KPICard({ label, formatted, changeLabel, trend, sparkline, color = 'green' }) {
  const c = colorMap[color] || colorMap.green;
  const isUp = trend === 'up';

  return (
    <div className={`bg-surface-100 rounded-2xl border ${c.border}/25 p-5 hover:border-opacity-50 transition-all relative overflow-hidden group`}>
      {/* Top accent line */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${c.border} opacity-50`} />

      <p className="text-[11px] font-semibold text-surface-400 uppercase tracking-wider mb-2">{label}</p>

      <p className="font-sans text-2xl font-bold text-surface-900 mb-2">{formatted}</p>

      {changeLabel && (
        <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${c.badge}`}>
          {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {changeLabel}
        </span>
      )}

      {/* Sparkline */}
      {sparkline && sparkline.length > 0 && (
        <div className="flex items-end gap-0.5 h-8 mt-3">
          {sparkline.map((val, i) => (
            <div
              key={i}
              className={`flex-1 rounded-t opacity-30 group-hover:opacity-60 transition-opacity ${c.border}`}
              style={{ height: `${Math.max(val, 5)}%`, backgroundColor: 'currentColor' }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
