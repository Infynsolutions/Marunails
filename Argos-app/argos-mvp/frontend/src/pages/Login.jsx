import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye } from 'lucide-react';
import { useAuth } from '../lib/auth';

export default function LoginPage() {
  const { signIn } = useAuth();
  const navigate   = useNavigate();

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await signIn(email, password);
      navigate('/', { replace: true });
    } catch (err) {
      setError(err.message ?? 'Error al iniciar sesión');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mb-8 justify-center">
          <div className="w-9 h-9 bg-argos-600 rounded-xl flex items-center justify-center shadow-sm">
            <Eye size={18} className="text-white" />
          </div>
          <span className="text-2xl font-bold text-surface-900">Argos</span>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-surface-200 p-8">
          <h1 className="text-xl font-semibold text-surface-900 mb-1">Bienvenido</h1>
          <p className="text-sm text-surface-500 mb-6">Ingresá a tu cuenta para continuar</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-surface-700 mb-1.5">
                Email
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="vos@tuempresa.com"
                className="w-full px-3.5 py-2.5 rounded-lg border border-surface-300 text-sm
                           focus:outline-none focus:ring-2 focus:ring-argos-500 focus:border-transparent
                           bg-white text-surface-900 placeholder-surface-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-surface-700 mb-1.5">
                Contraseña
              </label>
              <input
                type="password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-3.5 py-2.5 rounded-lg border border-surface-300 text-sm
                           focus:outline-none focus:ring-2 focus:ring-argos-500 focus:border-transparent
                           bg-white text-surface-900 placeholder-surface-400"
              />
            </div>

            {error && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-argos-600 hover:bg-argos-700 disabled:opacity-60
                         text-white text-sm font-medium rounded-lg transition-colors"
            >
              {loading ? 'Ingresando…' : 'Ingresar'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-surface-400 mt-6">
          ¿No tenés cuenta?{' '}
          <a href="mailto:hola@infyn.com" className="text-argos-600 hover:underline">
            Contactanos
          </a>
        </p>
      </div>
    </div>
  );
}
