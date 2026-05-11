import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { formatARS } from '../lib/format';

// Paleta INFYN — verdes principales + colores de soporte en tono dark
const COLORS = ['#2ED47A', '#0F7B53', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export default function CategoryChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-surface-400 text-sm">
        Sin datos de categorías
      </div>
    );
  }

  const topCategory = data[0];

  return (
    <div className="flex items-center gap-5">
      {/* Donut */}
      <div className="relative w-32 h-32 flex-shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="amount"
              nameKey="category"
              cx="50%"
              cy="50%"
              innerRadius={38}
              outerRadius={58}
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-sans text-lg font-bold text-surface-900">
            {topCategory?.percentage?.toFixed(0)}%
          </span>
          <span className="text-[10px] text-surface-400">
            {topCategory?.category?.split(' ')[0]?.toLowerCase()}
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-col gap-2.5 flex-1">
        {data.map((item, i) => (
          <div key={i} className="flex items-center gap-2.5">
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: item.color || COLORS[i % COLORS.length] }}
            />
            <div className="flex-1 min-w-0">
              <p className="text-sm text-surface-700 truncate">{item.category}</p>
              <p className="text-xs text-surface-400">
                {item.percentage?.toFixed(0)}% · {formatARS(item.amount)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
