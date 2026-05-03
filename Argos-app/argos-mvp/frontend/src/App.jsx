import { BrowserRouter, Routes, Route, Outlet } from 'react-router-dom';
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
  return (
    <div className="flex min-h-screen bg-surface-50 text-surface-900">
      <Sidebar />
      <main className="ml-60 flex-1 p-8 max-w-6xl">
        <Outlet />
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
