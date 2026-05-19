import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, CheckCircle, AlertCircle } from 'lucide-react';
import { useApi } from '../lib/useApi';

const today = () => new Date().toISOString().slice(0, 16);

const MOVEMENT_TYPES = [
  { value: 'entrada', label: 'Entrada — llegó mercadería' },
  { value: 'salida',  label: 'Salida — entregué sin venta' },
  { value: 'ajuste',  label: 'Ajuste — corrección de inventario' },
];

export default function IngresarStockPage() {
  const api = useApi();
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    product_id: '',
    type: 'entrada',
    quantity: '',
    note: '',
    date: today(),
  });

  useEffect(() => {
    api.getProducts().then(setProducts).catch(() => {});
  }, []);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm(f => ({ ...f, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.product_id || !form.quantity) return;
    setLoading(true);
    setError(null);

    const qty = parseInt(form.quantity, 10);
    const signedQty = form.type === 'ajuste' ? qty : Math.abs(qty);

    try {
      await api.addStockMovement({
        product_id: form.product_id,
        type: form.type,
        quantity: signedQty,
        note: form.note || null,
        date: new Date(form.date).toISOString(),
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
        <p className="text-surface-700 font-medium">Stock actualizado</p>
      </div>
    );
  }

  const isAjuste = form.type === 'ajuste';

  return (
    <div className="max-w-lg">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 bg-blue-500/10 rounded-xl flex items-center justify-center">
          <Package size={18} className="text-blue-600" />
        </div>
        <div>
          <h1 className="font-sans text-xl font-bold text-surface-900">Ingresé stock</h1>
          <p className="text-xs text-surface-400 mt-0.5">Registrá entradas, salidas y ajustes de inventario</p>
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
            Tipo de movimiento
          </label>
          <select
            name="type"
            value={form.type}
            onChange={handleChange}
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          >
            {MOVEMENT_TYPES.map(t => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

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
                {p.name} — Stock actual: {p.current_stock}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            Cantidad {isAjuste && <span className="text-surface-400 normal-case font-normal">(negativo para pérdida, positivo para reposición)</span>}
          </label>
          <input
            type="number"
            name="quantity"
            value={form.quantity}
            onChange={handleChange}
            required
            placeholder={isAjuste ? 'Ej: -3 o +5' : '1'}
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-surface-600 uppercase tracking-wide mb-1.5">
            Nota (opcional)
          </label>
          <input
            type="text"
            name="note"
            value={form.note}
            onChange={handleChange}
            placeholder="Ej: compra a proveedor X, pérdida por daño"
            className="w-full bg-white border border-surface-200 rounded-xl px-3 py-2.5 text-sm text-surface-800 focus:outline-none focus:ring-2 focus:ring-argos-400/40"
          />
        </div>

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

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl text-sm transition-colors"
        >
          {loading ? 'Guardando...' : 'Guardar movimiento'}
        </button>
      </form>
    </div>
  );
}
