import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Receipt, CheckCircle, AlertCircle } from 'lucide-react';
import { useApi } from '../lib/useApi';

const today = () => new Date().toISOString().slice(0, 16);

const CATEGORIES = [
  'Alquiler', 'Servicios', 'Sueldos', 'Proveedores',
  'Marketing', 'Logística', 'Impuestos', 'Otros',
];

export default function NuevoGastoPage() {
  const api = useApi();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    category: '',
    amount: '',
    description: '',
    date: today(),
    status: 'pagado',
  });

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.category || !form.amount) return;
    setLoading(true);
    setError(null);
    try {
      await api.createTransaction({
        type: 'gasto',
        category: form.category,
        amount: parseFloat(form.amount),
        description: form.description,
        date: new Date(form.date).toISOString(),
        status: form.status,
      });
      setSuccess(true);
      setTimeout(() => navigate('/'), 1500);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <CheckCircle size={40} className="text-green-500" />
        <p className="text-surface-700 font-medium">Gasto registrado</p>
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 bg-red-500/10 rounded-xl flex items-center justify-center">
          <Receipt size={18} className="text-red-500" />
        </div>
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Nuevo gasto</h1>
          <p className="text-xs text-surface-400 mt-0.5">Registrá un gasto operativo</p>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-xl p-3 mb-4 text-sm text-red-400">
          <AlertCircle size={14} />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-surface-100 border border-surface-200 rounded-2xl p-6 space-y-4">
        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            Categoría
          </label>
          <select
            name="category"
            value={form.category}
            onChange={handleChange}
            required
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          >
            <option value="">Seleccioná una categoría</option>
            {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            Monto ($)
          </label>
          <input
            type="number"
            name="amount"
            value={form.amount}
            onChange={handleChange}
            min="0"
            step="0.01"
            required
            placeholder="0"
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            Descripción
          </label>
          <input
            type="text"
            name="description"
            value={form.description}
            onChange={handleChange}
            placeholder="Ej: alquiler enero, pago a proveedor"
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
              Fecha
            </label>
            <input
              type="datetime-local"
              name="date"
              value={form.date}
              onChange={handleChange}
              required
              className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
              Estado
            </label>
            <select
              name="status"
              value={form.status}
              onChange={handleChange}
              className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
            >
              <option value="pagado">Pagado</option>
              <option value="pendiente">Pendiente</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
        >
          {loading ? 'Guardando...' : 'Registrar gasto'}
        </button>
      </form>
    </div>
  );
}
