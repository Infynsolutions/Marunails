import { formatARS, formatDate } from '../lib/format';

const statusStyles = {
  cobrado: 'bg-argos-400/15 text-argos-300',
  pagado: 'bg-argos-400/15 text-argos-300',
  pendiente: 'bg-amber-500/15 text-amber-400',
};

const statusLabels = {
  cobrado: '● Cobrado',
  pagado: '● Pagado',
  pendiente: '⏳ Pendiente',
};

const categoryColors = {
  'ventas mayoristas': 'bg-argos-400/15 text-argos-300',
  'ventas minoristas': 'bg-argos-400/10 text-argos-400',
  'ventas e-commerce': 'bg-blue-500/15 text-blue-400',
  'servicios': 'bg-blue-500/10 text-blue-400',
  'materia prima': 'bg-red-500/15 text-red-400',
  'logística': 'bg-amber-500/15 text-amber-400',
  'sueldos': 'bg-purple-500/15 text-purple-400',
  'alquiler': 'bg-red-500/20 text-red-400',
  'marketing': 'bg-orange-500/15 text-orange-400',
};

function getCatStyle(category) {
  const key = (category || '').toLowerCase();
  return categoryColors[key] || 'bg-surface-200 text-surface-500';
}

export default function TransactionsTable({ transactions }) {
  if (!transactions || transactions.length === 0) {
    return (
      <div className="text-center py-12 text-surface-400 text-sm">
        No hay transacciones para mostrar
      </div>
    );
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-surface-200">
              <th className="text-left py-3 px-4 text-xs font-semibold text-surface-400 uppercase tracking-wider">Descripción</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-surface-400 uppercase tracking-wider">Fecha</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-surface-400 uppercase tracking-wider">Categoría</th>
              <th className="text-left py-3 px-4 text-xs font-semibold text-surface-400 uppercase tracking-wider">Estado</th>
              <th className="text-right py-3 px-4 text-xs font-semibold text-surface-400 uppercase tracking-wider">Monto</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, i) => (
              <tr key={tx.id || i} className="border-b border-surface-200 hover:bg-surface-200/50 transition-colors">
                <td className="py-3.5 px-4">
                  <p className="font-semibold text-sm text-surface-800">{tx.description}</p>
                  {tx.reference && (
                    <p className="text-xs text-surface-400 mt-0.5">{tx.reference}</p>
                  )}
                </td>
                <td className="py-3.5 px-4 text-sm text-surface-500">{formatDate(tx.date)}</td>
                <td className="py-3.5 px-4">
                  <span className={`inline-block text-xs font-medium px-2.5 py-0.5 rounded-full ${getCatStyle(tx.category)}`}>
                    {tx.category}
                  </span>
                </td>
                <td className="py-3.5 px-4">
                  <span className={`inline-block text-xs font-medium px-2.5 py-0.5 rounded-full ${statusStyles[tx.status] || 'bg-surface-200 text-surface-500'}`}>
                    {statusLabels[tx.status] || tx.status}
                  </span>
                </td>
                <td className="py-3.5 px-4 text-right">
                  <span className={`font-sans font-bold text-sm ${tx.type === 'ingreso' ? 'text-argos-400' : 'text-red-400'}`}>
                    {tx.type === 'ingreso' ? '+' : '-'}{formatARS(tx.amount)}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
