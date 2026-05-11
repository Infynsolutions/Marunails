import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { formatARS } from '../lib/format';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  return (
    <div style={{ background: '#0C1812', border: '1px solid #162818' }} className="rounded-xl shadow-lg px-4 py-3">
      <p className="text-xs font-medium text-surface-500 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="text-sm font-semibold" style={{ color: entry.color }}>
          {entry.name}: {formatARS(entry.value)}
        </p>
      ))}
    </div>
  );
};

export default function RevenueChart({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-surface-400 text-sm">
        Sin datos de gráfico
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barGap={4}>
        <XAxis
          dataKey="month"
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#527A62', fontSize: 12 }}
        />
        <YAxis
          axisLine={false}
          tickLine={false}
          tick={{ fill: '#527A62', fontSize: 11 }}
          tickFormatter={(v) => `${(v / 1000000).toFixed(1)}M`}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(46,212,122,0.04)' }} />
        <Legend
          wrapperStyle={{ fontSize: 12, paddingTop: 8, color: '#7A9A88' }}
          iconType="square"
          iconSize={10}
        />
        <Bar dataKey="ingresos" name="Ingresos" fill="#2ED47A" radius={[6, 6, 0, 0]} />
        <Bar dataKey="gastos" name="Gastos" fill="#1E3824" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
