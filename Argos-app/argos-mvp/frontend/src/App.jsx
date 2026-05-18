import { useState } from 'react';
import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
import { Menu, Eye } from 'lucide-react';
import Sidebar from './components/Sidebar';
import DashboardPage from './pages/Dashboard';
import ChatPage from './pages/Chat';
import AgentsPage from './pages/Agents';
import AlertsPage from './pages/Alerts';
import ReportsPage from './pages/Reports';
import ConfigPage from './pages/Config';
import NuevaVentaPage from './pages/NuevaVenta';
import IngresarStockPage from './pages/IngresarStock';
import NuevoGastoPage from './pages/NuevoGasto';
import StockPage from './pages/Stock';
import NuevoProductoPage from './pages/NuevoProducto';

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-surface-50 text-surface-900">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="flex-1 lg:ml-60 flex flex-col min-h-screen">
        {/* Mobile top bar */}
        <div className="flex items-center h-14 px-4 bg-surface-100 border-b border-surface-200 lg:hidden sticky top-0 z-30">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-surface-200 text-surface-600"
          >
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2 ml-3">
            <div className="w-7 h-7 bg-argos-600 rounded-lg flex items-center justify-center">
              <Eye size={14} className="text-white" />
            </div>
            <span className="font-bold text-surface-900">Argos</span>
          </div>
        </div>

        <div className="flex-1 p-4 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/agentes" element={<AgentsPage />} />
          <Route path="/alertas" element={<AlertsPage />} />
          <Route path="/reportes" element={<ReportsPage />} />
          <Route path="/config" element={<ConfigPage />} />
          <Route path="/venta/nueva" element={<NuevaVentaPage />} />
          <Route path="/stock/ingresar" element={<IngresarStockPage />} />
          <Route path="/gasto/nuevo" element={<NuevoGastoPage />} />
          <Route path="/stock" element={<StockPage />} />
          <Route path="/productos/nuevo" element={<NuevoProductoPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
