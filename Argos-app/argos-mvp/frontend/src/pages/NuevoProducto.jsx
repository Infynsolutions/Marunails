import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tag, CheckCircle, AlertCircle } from 'lucide-react';
import { useApi } from '../lib/useApi';

export default function NuevoProductoPage() {
  const api = useApi();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    name: '',
    sku: '',
    unit_price: '',
    min_threshold: '3',
  });

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.createProduct({
        name: form.name,
        sku: form.sku.toUpperCase(),
        unit_price: parseFloat(form.unit_price),
        min_threshold: parseInt(form.min_threshold, 10),
      });
      setSuccess(true);
      setTimeout(() => navigate('/stock'), 1500);
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
        <p className="text-surface-700 font-medium">Producto creado</p>
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 bg-argos-600/10 rounded-xl flex items-center justify-center">
          <Tag size={18} className="text-argos-600" />
        </div>
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Nuevo producto</h1>
          <p className="text-xs text-surface-400 mt-0.5">Agregá un producto al catálogo</p>
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
            Nombre del producto
          </label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            placeholder="Ej: Remera manga corta azul"
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            SKU
          </label>
          <input
            type="text"
            name="sku"
            value={form.sku}
            onChange={handleChange}
            required
            placeholder="Ej: RMC-AZ-001"
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 font-mono focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
              Precio de venta ($)
            </label>
            <input
              type="number"
              name="unit_price"
              value={form.unit_price}
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
              Alerta de bajo stock
            </label>
            <input
              type="number"
              name="min_threshold"
              value={form.min_threshold}
              onChange={handleChange}
              min="0"
              required
              placeholder="3"
              className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
            />
            <p className="text-[10px] text-surface-400 mt-1">Unidades mínimas antes de alertar</p>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-argos-600 hover:bg-argos-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
        >
          {loading ? 'Creando...' : 'Crear producto'}
        </button>
      </form>
    </div>
  );
}
