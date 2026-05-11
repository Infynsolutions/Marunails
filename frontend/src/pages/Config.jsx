import { useState } from 'react';

function Toggle({ initial = true }) {
  const [on, setOn] = useState(initial);
  return (
    <button
      onClick={() => setOn(!on)}
      className={`w-11 h-6 rounded-full relative transition-colors ${on ? 'bg-argos-600' : 'bg-surface-300'}`}
    >
      <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-transform ${on ? 'left-6' : 'left-1'}`} />
    </button>
  );
}

function ConfigRow({ label, sub, children }) {
  return (
    <div className="flex items-center justify-between py-3.5 border-b border-surface-200 last:border-b-0">
      <div>
        <p className="text-sm font-medium text-surface-800">{label}</p>
        {sub && <p className="text-xs text-surface-400 mt-0.5">{sub}</p>}
      </div>
      {children}
    </div>
  );
}

export default function ConfigPage() {
  return (
    <div>
      <h1 className="font-sans text-xl font-bold text-surface-900 mb-6">Configuración</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left column */}
        <div className="space-y-4">
          {/* Data sources */}
          <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
            <h2 className="font-sans text-sm font-bold text-surface-800 mb-4 pb-3 border-b border-surface-200">
              Fuentes de datos
            </h2>
            {[
              { name: 'Ventas 2026', meta: '847 filas · Sync cada 15 min' },
              { name: 'Gastos operativos', meta: '412 filas · Sync cada hora' },
              { name: 'Cuentas a cobrar', meta: '156 filas · Sync cada hora' },
            ].map((sheet, i) => (
              <div key={i} className="flex items-center gap-3 py-3 border-b border-surface-200 last:border-b-0">
                <span className="text-xl">📗</span>
                <div className="flex-1">
                  <p className="text-sm font-medium text-surface-800">{sheet.name}</p>
                  <p className="text-xs text-surface-400 mt-0.5">{sheet.meta}</p>
                </div>
                <span className="text-[10px] font-medium bg-argos-400/15 text-argos-300 px-2 py-0.5 rounded-full">● Activa</span>
              </div>
            ))}
            <button className="w-full mt-3 text-sm font-medium text-surface-500 border border-surface-200 py-2.5 rounded-xl hover:bg-surface-200 transition-colors">
              + Conectar nueva hoja
            </button>
          </div>

          {/* Notifications */}
          <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
            <h2 className="font-sans text-sm font-bold text-surface-800 mb-4 pb-3 border-b border-surface-200">
              Notificaciones
            </h2>
            <ConfigRow label="Alertas por WhatsApp" sub="Alertas críticas en tu celular">
              <Toggle />
            </ConfigRow>
            <ConfigRow label="Reporte semanal por email" sub="Lunes a las 8:00 AM">
              <Toggle />
            </ConfigRow>
            <ConfigRow label="Alertas de anomalías" sub="Cuando Argos detecta algo inusual">
              <Toggle />
            </ConfigRow>
            <ConfigRow label="Insights proactivos" sub="Argos te avisa antes de que preguntes">
              <Toggle />
            </ConfigRow>
          </div>
        </div>

        {/* Right column */}
        <div className="space-y-4">
          {/* Account */}
          <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
            <h2 className="font-sans text-sm font-bold text-surface-800 mb-4 pb-3 border-b border-surface-200">
              Mi cuenta
            </h2>
            <ConfigRow label="Plan actual" sub="Argos Pro — todos los agentes">
              <span className="text-[10px] font-medium bg-argos-400/15 text-argos-300 px-2 py-0.5 rounded-full">Pro</span>
            </ConfigRow>
            <ConfigRow label="Empresa" sub="Café Aruba">
              <button className="text-xs text-surface-500 border border-surface-200 px-2.5 py-1 rounded-lg hover:bg-surface-200 transition-colors">Editar</button>
            </ConfigRow>
            <ConfigRow label="Zona horaria" sub="GMT-3 (Argentina)">
              <button className="text-xs text-surface-500 border border-surface-200 px-2.5 py-1 rounded-lg hover:bg-surface-200 transition-colors">Cambiar</button>
            </ConfigRow>
            <ConfigRow label="Moneda" sub="Peso argentino (ARS)">
              <button className="text-xs text-surface-500 border border-surface-200 px-2.5 py-1 rounded-lg hover:bg-surface-200 transition-colors">Cambiar</button>
            </ConfigRow>
          </div>

          {/* AI Config */}
          <div className="bg-surface-100 border border-surface-200 rounded-2xl p-5">
            <h2 className="font-sans text-sm font-bold text-surface-800 mb-4 pb-3 border-b border-surface-200">
              Argos — Configuración IA
            </h2>
            <ConfigRow label="Idioma" sub="Español (Argentina)">
              <button className="text-xs text-surface-500 border border-surface-200 px-2.5 py-1 rounded-lg hover:bg-surface-200 transition-colors">Cambiar</button>
            </ConfigRow>
            <ConfigRow label="Nivel de detalle" sub="Respuestas detalladas con datos">
              <button className="text-xs text-surface-500 border border-surface-200 px-2.5 py-1 rounded-lg hover:bg-surface-200 transition-colors">Ajustar</button>
            </ConfigRow>
            <ConfigRow label="Memoria de contexto" sub="Argos recuerda el historial">
              <Toggle />
            </ConfigRow>
          </div>
        </div>
      </div>
    </div>
  );
}
