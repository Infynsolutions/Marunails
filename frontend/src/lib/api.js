/**
 * Argos API Client
 * All backend communication goes through here.
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TENANT_ID = import.meta.env.VITE_TENANT_ID || '00000000-0000-0000-0000-000000000001';

async function request(path, options = {}) {
  const url = `${API_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Error de conexión' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Dashboard
  getDashboard: () => request(`/api/v1/dashboard/${TENANT_ID}`),

  // Transactions
  getTransactions: (limit = 50, offset = 0) =>
    request(`/api/v1/transactions/${TENANT_ID}?limit=${limit}&offset=${offset}`),

  createTransaction: (data) =>
    request(`/api/v1/transactions/${TENANT_ID}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Products
  getProducts: () => request(`/api/v1/products/${TENANT_ID}`),

  getProduct: (sku) => request(`/api/v1/products/${TENANT_ID}/${sku}`),

  createProduct: (data) =>
    request(`/api/v1/products/${TENANT_ID}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Stock
  getStock: () => request(`/api/v1/stock/${TENANT_ID}`),

  addStockMovement: (data) =>
    request(`/api/v1/stock-movement/${TENANT_ID}`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Chat
  sendMessage: (message, sessionId = null) =>
    request(`/api/v1/chat/${TENANT_ID}`, {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  // Alerts
  getAlerts: () => request(`/api/v1/alerts/${TENANT_ID}`),

  resolveAlert: (alertId) =>
    request(`/api/v1/alerts/${TENANT_ID}/${alertId}/resolve`, { method: 'POST' }),

  // Stock movements history
  getStockMovements: (limit = 100) => request(`/api/v1/stock-movements/${TENANT_ID}?limit=${limit}`),

  // Health
  health: () => request('/api/v1/health'),
};

export { TENANT_ID };
