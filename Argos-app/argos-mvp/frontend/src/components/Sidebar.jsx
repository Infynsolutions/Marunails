import { NavLink } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Bot, Bell, FileText, Settings, Eye, ShoppingCart, Package, Receipt, X } from 'lucide-react';

const navItems = [
  { section: 'Principal', items: [
    { to: '/chat', icon: MessageSquare, label: 'Chat con Argos', accent: true },
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  ]},
  { section: 'Carga', items: [
    { to: '/venta/nueva', icon: ShoppingCart, label: 'Nueva venta' },
    { to: '/stock/ingresar', icon: Package, label: 'Ingresé stock' },
    { to: '/gasto/nuevo', icon: Receipt, label: 'Nuevo gasto' },
  ]},
  { section: 'Inventario', items: [
    { to: '/stock', icon: Package, label: 'Stock' },
    { to: '/alertas', icon: Bell, label: 'Alertas', badgeColor: 'red' },
  ]},
  { section: 'Análisis', items: [
    { to: '/reportes', icon: FileText, label: 'Reportes' },
    { to: '/agentes', icon: Bot, label: 'Agentes' },
  ]},
  { section: 'Sistema', items: [
    { to: '/config', icon: Settings, label: 'Configuración' },
  ]},
];

export default function Sidebar({ open, onClose }) {
  return (
    <>
      {/* Mobile overlay */}
      <div
        className={`fixed inset-0 bg-black/50 z-40 lg:hidden transition-opacity duration-200 ${
          open ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />

      <aside className={`w-60 bg-surface-100 border-r border-surface-200 fixed top-0 left-0 bottom-0 z-50 flex flex-col transition-transform duration-200 ease-in-out
        ${open ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0`}>

        {/* Logo */}
        <div className="px-5 py-6 border-b border-surface-200 aurora-sidebar flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-argos-600 rounded-xl flex items-center justify-center shadow-sm shadow-argos-600/30">
              <Eye size={18} className="text-white" />
            </div>
            <div>
              <p className="font-sans font-bold text-lg text-surface-900 leading-none tracking-tight">Argos</p>
              <p className="text-[10px] text-argos-400 uppercase tracking-[1.5px] mt-0.5 font-medium">by INFYN</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1.5 rounded-lg hover:bg-surface-200 text-surface-500"
          >
            <X size={16} />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 overflow-y-auto">
          {navItems.map((section) => (
            <div key={section.section} className="mb-5">
              <p className="text-[10px] font-semibold text-surface-400 uppercase tracking-[1.5px] px-3 mb-1.5">
                {section.section}
              </p>
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/'}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all mb-0.5 ${
                      isActive
                        ? item.accent
                          ? 'bg-argos-600 text-white shadow-sm shadow-argos-600/30'
                          : 'bg-argos-400/10 text-argos-400 border border-argos-400/25'
                        : 'text-surface-500 hover:bg-surface-200 hover:text-surface-700 border border-transparent'
                    }`
                  }
                >
                  <item.icon size={16} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                      item.badgeColor === 'red' ? 'bg-red-500 text-white' : 'bg-argos-600 text-white'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>

        {/* User card */}
        <div className="p-3 border-t border-surface-200">
          <div className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-surface-50">
            <div className="w-8 h-8 bg-gradient-to-br from-argos-400 to-argos-600 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
              LP
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-surface-800 truncate">La Percha</p>
              <p className="text-xs text-surface-500">Plan Pro</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
