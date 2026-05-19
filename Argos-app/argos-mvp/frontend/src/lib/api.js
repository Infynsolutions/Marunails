/**
 * Argos API Client
 * Uses Supabase session JWT for auth. All calls are scoped to the
 * authenticated user's tenant (resolved server-side via RLS + user_tenants).
 */

import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL ?? '';

async function getToken() {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

async function request(path, options = {}) {
  const token = await getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { headers, ...options });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Error de conexión' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// tenantId is passed by the caller (from useAuth().tenantId) so the URL matches
// what the backend expects. The server verifies it against the JWT's tenant.
export function makeApi(tenantId) {
  return {
    // Dashboard
    getDashboard: () => request(`/api/v1/dashboard/${tenantId}`),

    // Transactions
    getTransactions: (limit = 50, offset = 0) =>
      request(`/api/v1/transactions/${tenantId}?limit=${limit}&offset=${offset}`),

    createTransaction: (data) =>
      request(`/api/v1/transactions/${tenantId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    // Products
    getProducts: () => request(`/api/v1/products/${tenantId}`),
    getProduct:  (sku) => request(`/api/v1/products/${tenantId}/${sku}`),
    createProduct: (data) =>
      request(`/api/v1/products/${tenantId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    // Stock
    getStock: () => request(`/api/v1/stock/${tenantId}`),
    addStockMovement: (data) =>
      request(`/api/v1/stock-movement/${tenantId}`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    // Chat
    sendMessage: (message, sessionId = null) =>
      request(`/api/v1/chat/${tenantId}`, {
        method: 'POST',
        body: JSON.stringify({ message, session_id: sessionId }),
      }),

    // Alerts
    getAlerts: () => request(`/api/v1/alerts/${tenantId}`),
    resolveAlert: (alertId) =>
      request(`/api/v1/alerts/${tenantId}/${alertId}/resolve`, { method: 'POST' }),

    // Reports
    getReport: (year, month) => {
      const params = new URLSearchParams();
      if (year)  params.append('year', year);
      if (month) params.append('month', month);
      const qs = params.toString() ? `?${params}` : '';
      return request(`/api/v1/report/${tenantId}${qs}`);
    },

    // Collections
    getCollections: () => request(`/api/v1/collections/${tenantId}`),
  };
}

// Public endpoints (no tenant needed)
export const publicApi = {
  health: () => request('/api/v1/health'),
  me:     () => request('/api/v1/me'),
};
