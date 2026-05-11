import { FileText } from 'lucide-react';

export default function ReportsPage() {
  return (
    <div>
      <h1 className="font-sans text-xl font-bold text-surface-900 mb-6">Reportes</h1>
      <div className="text-center py-20">
        <FileText size={48} className="text-surface-300 mx-auto mb-4" />
        <p className="font-sans text-lg font-bold text-surface-700">Reportes automáticos</p>
        <p className="text-sm text-surface-400 mt-2">
          Argos genera reportes ejecutivos semanales y mensuales.<br />
          Próximo reporte: <strong className="text-argos-600">Lunes 30 de marzo</strong>
        </p>
        <button className="mt-5 bg-argos-600 text-white text-sm font-medium px-5 py-2.5 rounded-xl hover:bg-argos-700 transition-colors">
          + Generar reporte ahora
        </button>
      </div>
    </div>
  );
}
