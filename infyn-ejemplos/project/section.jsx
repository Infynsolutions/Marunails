/* global React, FinanceMockup, DistribucionMockup, VentasMockup, StockMockup, BrowserChrome, useTweaks, TweaksPanel, TweakSection, TweakToggle, TweakRadio, TweakSlider */
const { useState, useEffect, useRef } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "showMetrics": true,
  "showTags": true,
  "columns": "2",
  "accentHue": 145,
  "interactivity": "tabs"
}/*EDITMODE-END*/;

const SYSTEMS = [
  {
    id: "finanzas",
    name: "Sistema de Gestión Financiera",
    short: "Finanzas",
    tag: "ERP · Dashboard financiero",
    desc: "Visualización en tiempo real del estado financiero. Saldo de caja, runway, cobranzas, flujo proyectado y progreso vs objetivo — todo en una sola pantalla.",
    metrics: [
      { value: "+32%", label: "visibilidad de caja" },
      { value: "-25%", label: "tiempo de cierre mensual" },
      { value: "+40%", label: "decisiones basadas en datos" },
    ],
    features: ["Estado financiero en vivo", "Proyección de flujo", "Cobranzas y vencimientos", "Asistente IA"],
    Component: () => window.FinanceMockup ? <window.FinanceMockup /> : null,
    url: "tunegocio.app/panel/finanzas",
  },
  {
    id: "distribucion",
    name: "Sistema de Distribución y Logística",
    short: "Distribución",
    tag: "Operaciones · Multi-rol",
    desc: "Pensado para empresas con vendedores en la calle. Vista gerencial con alertas, vista vendedor para registrar entregas y cobros, control de stock y deudas en tiempo real.",
    metrics: [
      { value: "+50%", label: "carga diaria de vendedores" },
      { value: "-60%", label: "errores de cobro" },
      { value: "100%", label: "trazabilidad por cliente" },
    ],
    features: ["Vista gerencial con alertas", "App de vendedor en ruta", "Control de stock", "Reporte del día"],
    Component: () => window.DistribucionMockup ? <window.DistribucionMockup /> : null,
    url: "tunegocio.app/panel/distribucion",
  },
  {
    id: "ventas",
    name: "Sistema de Ventas y Comisiones",
    short: "Ventas",
    tag: "CRM · Ranking de equipo",
    desc: "Ranking automático de vendedores, cálculo de comisiones, seguimiento de cobranzas y estado de cada venta. Tu equipo compite con datos reales, no con planillas.",
    metrics: [
      { value: "+45%", label: "ventas cobradas a tiempo" },
      { value: "0", label: "planillas de Excel" },
      { value: "100%", label: "comisiones automatizadas" },
    ],
    features: ["Ranking en vivo", "Comisiones por programa", "Estado de cobro por venta", "Exportable"],
    Component: () => window.VentasMockup ? <window.VentasMockup /> : null,
    url: "tunegocio.app/panel/ventas",
  },
  {
    id: "stock",
    name: "Panel Comercial Multi-Producto",
    short: "Comercial",
    tag: "BI · Reportes ejecutivos",
    desc: "Comparativas mes a mes, distribución de ventas por vendedor, ranking por venta/kilos/cobranza/clientes. Para decisiones rápidas en reuniones de gerencia.",
    metrics: [
      { value: "+38%", label: "agilidad en reportes" },
      { value: "5×", label: "más cruces de datos" },
      { value: "Real-time", label: "sin esperar al cierre" },
    ],
    features: ["Comparativa mes vs mes", "Ranking multi-criterio", "Distribución porcentual", "Búsqueda instantánea"],
    Component: () => window.StockMockup ? <window.StockMockup /> : null,
    url: "tunegocio.app/panel/comercial",
  },
];

const InfynLogo = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 16, fontWeight: 700, color: "#fff" }}>
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M3 12c0-3 3-5 6-5s4 2 6 5 3 5 6 5" stroke="#22c55e" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M3 12c0 3 3 5 6 5s4-2 6-5 3-5 6-5" stroke="#22c55e" strokeWidth="2.2" strokeLinecap="round" opacity="0.5" />
    </svg>
    <span>INFYN</span>
  </div>
);

const ExamplesSection = () => {
  const [tweaks, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [active, setActive] = useState(0);
  const [lightbox, setLightbox] = useState(null);
  const sys = SYSTEMS[active];

  const accent = `oklch(0.72 0.18 ${tweaks.accentHue})`;
  const accentDim = `oklch(0.72 0.18 ${tweaks.accentHue} / 0.15)`;

  // ESC closes lightbox
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape") setLightbox(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div style={{ background: "#000", minHeight: "100vh", color: "#fff", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      {/* fake nav of the actual site so it feels like part of infynsolutions.com */}
      <header style={{ position: "sticky", top: 0, zIndex: 50, background: "rgba(0,0,0,.85)", backdropFilter: "blur(12px)", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "16px 32px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <InfynLogo />
          <nav style={{ display: "flex", gap: 28, fontSize: 13, color: "rgba(255,255,255,.7)" }}>
            <span>Servicios</span>
            <span>Proceso</span>
            <span style={{ color: accent }}>Ejemplos</span>
            <span>Contacto</span>
          </nav>
          <button style={{ background: accent, color: "#000", padding: "8px 16px", borderRadius: 8, fontSize: 12, fontWeight: 600, border: "none" }}>
            Agendar reunión
          </button>
        </div>
      </header>

      {/* SECTION HEADER */}
      <section style={{ padding: "80px 32px 40px", maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, letterSpacing: 2, color: accent, fontWeight: 600, marginBottom: 16 }}>
          <span style={{ width: 24, height: 1, background: accent }} />
          EJEMPLOS REALES
        </div>
        <h2 style={{ fontSize: 48, lineHeight: 1.1, fontWeight: 800, margin: 0, maxWidth: 800 }}>
          Esto es lo que <span style={{ color: accent }}>podés tener</span><br />
          funcionando en tu negocio.
        </h2>
        <p style={{ fontSize: 17, color: "rgba(255,255,255,.6)", maxWidth: 640, marginTop: 20, lineHeight: 1.5 }}>
          No vendemos plantillas. Cada sistema lo diseñamos a medida del flujo real de tu empresa. Acá tenés ejemplos de los que ya están funcionando — con datos genéricos para proteger a nuestros clientes.
        </p>
      </section>

      {/* TABS */}
      <section style={{ maxWidth: 1200, margin: "0 auto", padding: "0 32px" }}>
        <div style={{ display: "flex", gap: 4, borderBottom: "1px solid rgba(255,255,255,.08)", marginBottom: 32, overflowX: "auto" }}>
          {SYSTEMS.map((s, i) => (
            <button
              key={s.id}
              onClick={() => setActive(i)}
              style={{
                background: "transparent",
                border: "none",
                color: i === active ? accent : "rgba(255,255,255,.55)",
                fontSize: 13,
                fontWeight: i === active ? 600 : 500,
                padding: "16px 20px",
                cursor: "pointer",
                borderBottom: `2px solid ${i === active ? accent : "transparent"}`,
                marginBottom: -1,
                whiteSpace: "nowrap",
                fontFamily: "inherit",
                transition: "color .2s",
              }}
            >
              <span style={{ opacity: 0.5, marginRight: 8, fontVariantNumeric: "tabular-nums" }}>0{i + 1}</span>
              {s.short}
            </button>
          ))}
        </div>

        {/* CONTENT */}
        <div style={{ display: "grid", gridTemplateColumns: tweaks.columns === "2" ? "1fr 360px" : "1fr", gap: 32, marginBottom: 40 }}>
          {/* MOCKUP */}
          <div style={{ order: 1 }}>
            <div
              onClick={() => setLightbox(active)}
              style={{ cursor: "zoom-in", position: "relative", transition: "transform .3s" }}
              onMouseEnter={(e) => (e.currentTarget.style.transform = "translateY(-2px)")}
              onMouseLeave={(e) => (e.currentTarget.style.transform = "translateY(0)")}
            >
              <BrowserChrome url={sys.url}>
                <sys.Component />
              </BrowserChrome>
              <div style={{ position: "absolute", top: 12, right: 12, background: "rgba(0,0,0,.7)", color: "#fff", padding: "4px 10px", borderRadius: 99, fontSize: 10, fontWeight: 600, backdropFilter: "blur(8px)", border: "1px solid rgba(255,255,255,.1)" }}>
                ⤢ Click para ampliar
              </div>
            </div>

            {/* mockup caption */}
            <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, color: "rgba(255,255,255,.45)" }}>
              <span>Captura recreada · Datos genéricos por privacidad del cliente</span>
              <span style={{ display: "flex", gap: 8 }}>
                {SYSTEMS.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActive(i)}
                    style={{
                      width: i === active ? 20 : 6,
                      height: 6,
                      borderRadius: 99,
                      background: i === active ? accent : "rgba(255,255,255,.2)",
                      border: "none",
                      transition: "all .3s",
                      cursor: "pointer",
                      padding: 0,
                    }}
                  />
                ))}
              </span>
            </div>
          </div>

          {/* INFO PANEL */}
          <div style={{ order: tweaks.columns === "2" ? 2 : 0 }}>
            {tweaks.showTags && (
              <div style={{ display: "inline-block", padding: "4px 10px", borderRadius: 99, background: accentDim, color: accent, fontSize: 10, fontWeight: 600, letterSpacing: 1, marginBottom: 16 }}>
                {sys.tag.toUpperCase()}
              </div>
            )}
            <h3 style={{ fontSize: 24, fontWeight: 700, margin: 0, lineHeight: 1.2 }}>{sys.name}</h3>
            <p style={{ color: "rgba(255,255,255,.6)", fontSize: 14, lineHeight: 1.55, marginTop: 12 }}>{sys.desc}</p>

            {/* features */}
            <div style={{ marginTop: 20, display: "flex", flexDirection: "column", gap: 8 }}>
              {sys.features.map((f) => (
                <div key={f} style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 13, color: "rgba(255,255,255,.8)" }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                    <path d="M5 13l4 4L19 7" stroke={accent} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                  {f}
                </div>
              ))}
            </div>

            {/* metrics */}
            {tweaks.showMetrics && (
              <div style={{ marginTop: 28, display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                {sys.metrics.map((m, i) => (
                  <div
                    key={i}
                    style={{
                      background: "rgba(255,255,255,.03)",
                      border: "1px solid rgba(255,255,255,.06)",
                      borderRadius: 10,
                      padding: "14px 12px",
                    }}
                  >
                    <div style={{ fontSize: 20, fontWeight: 800, color: accent, fontFamily: "ui-monospace, monospace" }}>
                      {m.value}
                    </div>
                    <div style={{ fontSize: 10, color: "rgba(255,255,255,.55)", marginTop: 4, lineHeight: 1.3 }}>{m.label}</div>
                  </div>
                ))}
              </div>
            )}

            <button
              style={{
                marginTop: 24,
                background: accent,
                color: "#000",
                border: "none",
                padding: "12px 20px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                width: "100%",
                fontFamily: "inherit",
              }}
            >
              Quiero algo así para mi negocio →
            </button>
          </div>
        </div>

        {/* ALL SYSTEMS GRID PEEK */}
        <div style={{ marginTop: 64, paddingTop: 48, borderTop: "1px solid rgba(255,255,255,.06)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 24 }}>
            <h3 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Todos los sistemas en un vistazo</h3>
            <span style={{ fontSize: 12, color: "rgba(255,255,255,.5)" }}>Click para abrir</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
            {SYSTEMS.map((s, i) => (
              <div
                key={s.id}
                onClick={() => setActive(i)}
                style={{
                  background: "rgba(255,255,255,.02)",
                  border: `1px solid ${i === active ? accent : "rgba(255,255,255,.06)"}`,
                  borderRadius: 12,
                  padding: 14,
                  cursor: "pointer",
                  transition: "all .25s",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,.04)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "rgba(255,255,255,.02)";
                }}
              >
                <div style={{ borderRadius: 8, overflow: "hidden", marginBottom: 12, transform: "scale(0.5)", transformOrigin: "top left", width: "200%", height: 270, pointerEvents: "none" }}>
                  <BrowserChrome url={s.url}>
                    <s.Component />
                  </BrowserChrome>
                </div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{s.name}</div>
                    <div style={{ fontSize: 11, color: "rgba(255,255,255,.5)", marginTop: 2 }}>{s.tag}</div>
                  </div>
                  <span style={{ color: accent, fontSize: 18 }}>→</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div style={{ marginTop: 80, marginBottom: 80, padding: "48px 40px", background: `linear-gradient(135deg, ${accentDim}, transparent)`, border: `1px solid ${accent}33`, borderRadius: 16, textAlign: "center" }}>
          <h3 style={{ fontSize: 32, fontWeight: 800, margin: 0, lineHeight: 1.2 }}>
            Tu negocio merece un sistema <span style={{ color: accent }}>hecho a medida</span>.
          </h3>
          <p style={{ fontSize: 15, color: "rgba(255,255,255,.65)", marginTop: 14, maxWidth: 560, marginLeft: "auto", marginRight: "auto" }}>
            Contános cómo trabajás. En 30 minutos te mostramos cómo se vería tu sistema.
          </p>
          <button
            style={{
              marginTop: 24,
              background: accent,
              color: "#000",
              border: "none",
              padding: "14px 28px",
              borderRadius: 10,
              fontSize: 14,
              fontWeight: 700,
              cursor: "pointer",
              fontFamily: "inherit",
            }}
          >
            Agendar una llamada →
          </button>
        </div>
      </section>

      {/* LIGHTBOX */}
      {lightbox !== null && (
        <div
          onClick={() => setLightbox(null)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,.92)",
            backdropFilter: "blur(8px)",
            zIndex: 100,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 32,
            cursor: "zoom-out",
          }}
        >
          <div style={{ width: "100%", maxWidth: 1280, cursor: "default" }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div>
                <div style={{ fontSize: 11, color: accent, letterSpacing: 1.5, fontWeight: 600 }}>{SYSTEMS[lightbox].tag.toUpperCase()}</div>
                <div style={{ fontSize: 20, fontWeight: 700, marginTop: 4 }}>{SYSTEMS[lightbox].name}</div>
              </div>
              <button onClick={() => setLightbox(null)} style={{ background: "rgba(255,255,255,.1)", border: "none", color: "#fff", width: 36, height: 36, borderRadius: 99, fontSize: 18, cursor: "pointer" }}>
                ×
              </button>
            </div>
            <BrowserChrome url={SYSTEMS[lightbox].url}>
              {(() => {
                const C = SYSTEMS[lightbox].Component;
                return <C />;
              })()}
            </BrowserChrome>
            <div style={{ marginTop: 16, display: "flex", justifyContent: "center", gap: 8 }}>
              {SYSTEMS.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setLightbox(i)}
                  style={{
                    width: i === lightbox ? 24 : 8,
                    height: 8,
                    borderRadius: 99,
                    background: i === lightbox ? accent : "rgba(255,255,255,.25)",
                    border: "none",
                    cursor: "pointer",
                    transition: "all .3s",
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TWEAKS PANEL */}
      <TweaksPanel title="Tweaks">
        <TweakSection title="Layout">
          <TweakRadio
            label="Columnas"
            value={tweaks.columns}
            options={[{ value: "2", label: "2 col" }, { value: "1", label: "1 col" }]}
            onChange={(v) => setTweak("columns", v)}
          />
        </TweakSection>
        <TweakSection title="Contenido">
          <TweakToggle label="Mostrar métricas" value={tweaks.showMetrics} onChange={(v) => setTweak("showMetrics", v)} />
          <TweakToggle label="Mostrar etiquetas" value={tweaks.showTags} onChange={(v) => setTweak("showTags", v)} />
        </TweakSection>
        <TweakSection title="Marca">
          <TweakSlider label="Tono del verde" min={120} max={180} step={1} value={tweaks.accentHue} onChange={(v) => setTweak("accentHue", v)} />
        </TweakSection>
      </TweaksPanel>
    </div>
  );
};

window.ExamplesSection = ExamplesSection;
