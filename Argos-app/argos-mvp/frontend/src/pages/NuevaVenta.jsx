import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShoppingCart, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../lib/api';

const today = () => new Date().toISOString().slice(0, 16);

export default function NuevaVentaPage() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    product_id: '',
    quantity: '',
    amount: '',
    description: '',
    date: today(),
    status: 'cobrado',
  });

  useEffect(() => {
    api.getProducts().then(setProducts).catch(() => {});
  }, []);

  const selectedProduct = products.find(p => p.id === form.product_id);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.product_id || !form.quantity || !form.amount) return;
    setLoading(true);
    setError(null);
    try {
      await api.createTransaction({
        type: 'ingreso',
        category: 'Ventas',
        product_id: form.product_id,
        quantity: parseInt(form.quantity, 10),
        amount: parseFloat(form.amount),
        description: form.description || `Venta — ${selectedProduct?.name || ''}`,
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
        <p className="text-surface-700 font-medium">Venta registrada</p>
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 bg-green-500/10 rounded-xl flex items-center justify-center">
          <ShoppingCart size={18} className="text-green-600" />
        </div>
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Nueva venta</h1>
          <p className="text-xs text-surface-400 mt-0.5">Registrá una venta y actualizá el stock</p>
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
            Producto
          </label>
          <select
            name="product_id"
            value={form.product_id}
            onChange={handleChange}
            required
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          >
            <option value="">Seleccioná un producto</option>
            {products.map(p => (
              <option key={p.id} value={p.id}>
                {p.name} — Stock: {p.current_stock}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
              Cantidad
            </label>
            <input
              type="number"
              name="quantity"
              value={form.quantity}
              onChange={handleChange}
              min="1"
              required
              placeholder="1"
              className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
              Precio total ($)
            </label>
            <input
              type="number"
              name="amount"
              value={form.amount}
              onChange={handleChange}
              min="0"
              step="0.01"
              required
              placeholder={selectedProduct ? String(selectedProduct.unit_price) : '0'}
              className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            Descripción (opcional)
          </label>
          <input
            type="text"
            name="description"
            value={form.description}
            onChange={handleChange}
            placeholder="Ej: venta a Juan, FA-1234"
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
              <option value="cobrado">Cobrado</option>
              <option value="pendiente">Pendiente</option>
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
        >
          {loading ? 'Registrando...' : 'Registrar venta'}
        </button>
      </form>
    </div>
  );
}
