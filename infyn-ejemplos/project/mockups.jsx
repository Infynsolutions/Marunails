/* global React */
const { useState, useMemo } = React;

// ============================================================
// SHARED PRIMITIVES
// ============================================================

const BrowserChrome = ({ url, theme = "dark", children, scale = 1 }) => {
  const isLight = theme === "light";
  return (
    <div
      style={{
        width: "100%",
        background: isLight ? "#f5f5f7" : "#0b0f0e",
        borderRadius: 12,
        overflow: "hidden",
        boxShadow:
          "0 30px 80px -20px rgba(0,0,0,.6), 0 0 0 1px rgba(255,255,255,.06)",
        border: "1px solid rgba(255,255,255,.06)",
      }}
    >
      {/* tab bar */}
      <div
        style={{
          height: 36,
          background: isLight ? "#e7e7ea" : "#0e1413",
          display: "flex",
          alignItems: "center",
          padding: "0 12px",
          gap: 8,
          borderBottom: `1px solid ${isLight ? "rgba(0,0,0,.08)" : "rgba(255,255,255,.06)"}`,
        }}
      >
        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#ff5f57" }} />
        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#febc2e" }} />
        <span style={{ width: 11, height: 11, borderRadius: 99, background: "#28c840" }} />
        <div
          style={{
            marginLeft: 16,
            flex: 1,
            maxWidth: 360,
            height: 22,
            background: isLight ? "#fff" : "#1a201e",
            borderRadius: 6,
            display: "flex",
            alignItems: "center",
            padding: "0 10px",
            fontSize: 11,
            color: isLight ? "#555" : "rgba(255,255,255,.55)",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          }}
        >
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" style={{ marginRight: 6, opacity: 0.6 }}>
            <path d="M12 2 4 5v6c0 5 3.5 9.7 8 11 4.5-1.3 8-6 8-11V5l-8-3z" stroke="currentColor" strokeWidth="2" />
          </svg>
          {url}
        </div>
      </div>
      {children}
    </div>
  );
};

const Sidebar = ({ brand, brandSub, items, activeIndex, theme = "dark" }) => {
  const isLight = theme === "light";
  return (
    <div
      style={{
        width: 168,
        flexShrink: 0,
        background: isLight ? "#1a2332" : "#0d1311",
        color: isLight ? "rgba(255,255,255,.85)" : "rgba(255,255,255,.78)",
        padding: "14px 0",
        fontSize: 11,
        fontFamily: "system-ui, -apple-system, sans-serif",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <div style={{ padding: "0 14px 12px" }}>
        <div style={{ fontWeight: 800, fontSize: 13, letterSpacing: 0.5, color: brand.color }}>
          {brand.name}
        </div>
        <div style={{ fontSize: 9, opacity: 0.5, letterSpacing: 1, marginTop: 2 }}>{brandSub}</div>
      </div>
      {items.map((it, i) =>
        it.section ? (
          <div
            key={i}
            style={{
              padding: "10px 14px 4px",
              fontSize: 8,
              opacity: 0.4,
              letterSpacing: 1.5,
              fontWeight: 600,
            }}
          >
            {it.section}
          </div>
        ) : (
          <div
            key={i}
            style={{
              padding: "6px 14px",
              display: "flex",
              alignItems: "center",
              gap: 8,
              background:
                i === activeIndex
                  ? isLight
                    ? "linear-gradient(90deg, rgba(229,72,77,.18), transparent)"
                    : "rgba(34,211,238,.08)"
                  : "transparent",
              borderLeft:
                i === activeIndex
                  ? `2px solid ${isLight ? "#e5484d" : "#22d3ee"}`
                  : "2px solid transparent",
              color:
                i === activeIndex
                  ? isLight
                    ? "#fff"
                    : "#22d3ee"
                  : "inherit",
            }}
          >
            <span style={{ width: 10, height: 10, opacity: 0.7 }}>{it.icon}</span>
            <span>{it.label}</span>
            {it.badge && (
              <span
                style={{
                  marginLeft: "auto",
                  background: "#22d3ee",
                  color: "#08272d",
                  fontSize: 8,
                  fontWeight: 700,
                  padding: "1px 5px",
                  borderRadius: 99,
                }}
              >
                {it.badge}
              </span>
            )}
          </div>
        )
      )}
    </div>
  );
};

const dot = (color) => (
  <span
    style={{
      display: "inline-block",
      width: 6,
      height: 6,
      borderRadius: 99,
      background: color,
      marginRight: 5,
      verticalAlign: "middle",
    }}
  />
);

// ============================================================
// MOCKUP 1: FINANCE DASHBOARD (Stannum-style)
// ============================================================

const FinanceMockup = () => {
  const navItems = [
    { icon: "▣", label: "Panel" },
    { icon: "▤", label: "Resumen" },
    { icon: "▦", label: "Semana" },
    { icon: "✦", label: "Asistente" },
    { section: "OPERACIÓN" },
    { icon: "◎", label: "Objetivos", badge: "3" },
    { icon: "≡", label: "Movimientos" },
    { icon: "♢", label: "Ventas" },
    { icon: "◈", label: "Clientes" },
    { icon: "▢", label: "Proveedores" },
    { icon: "▢", label: "Facturas" },
    { section: "FINANZAS" },
    { icon: "▤", label: "Cuentas" },
    { icon: "▤", label: "Resultados" },
    { icon: "▤", label: "Impuestos" },
  ];

  const months = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

  return (
    <div style={{ display: "flex", background: "#0b0f0e", color: "rgba(255,255,255,.92)", fontFamily: "system-ui, -apple-system, sans-serif", height: 540 }}>
      <Sidebar
        brand={{ name: "EMPRESA", color: "#22d3ee" }}
        brandSub="ADFIN"
        items={navItems}
        activeIndex={0}
      />
      <div style={{ flex: 1, padding: 18, overflow: "hidden" }}>
        {/* header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600 }}>Estado Financiero</div>
          </div>
          <div style={{ fontSize: 10, opacity: 0.5 }}>martes, 28 de abr de 2026</div>
        </div>

        {/* months tabs */}
        <div style={{ display: "flex", gap: 4, fontSize: 10, marginBottom: 14, color: "rgba(255,255,255,.5)" }}>
          {months.map((m, i) => (
            <div
              key={m}
              style={{
                padding: "3px 8px",
                borderRadius: 99,
                background: i === 3 ? "#22d3ee" : "transparent",
                color: i === 3 ? "#08272d" : "inherit",
                fontWeight: i === 3 ? 700 : 400,
              }}
            >
              {m}
            </div>
          ))}
          <div style={{ padding: "3px 10px", borderRadius: 99, background: "#1a201e", marginLeft: 6 }}>2026</div>
          <div style={{ padding: "3px 10px", borderRadius: 99, background: "#1a201e" }}>Rango</div>
        </div>

        {/* KPI cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 12 }}>
          {[
            { label: "SALDO DE CAJA TOTAL", value: "$3,110", sub: "Final del período +$6,099", color: "#22d3ee" },
            { label: "INGRESOS DEL MES", value: "$38,469", sub: "+52% vs Mar", color: "#22c55e" },
            { label: "EGRESOS DEL MES", value: "$32,409", sub: "+28% vs Mar", color: "#f59e0b" },
            { label: "COBROS PENDIENTES", value: "$80,367", sub: "5 vencidos · 46 planificados", color: "#ef4444" },
          ].map((k) => (
            <div
              key={k.label}
              style={{
                background: "#11181a",
                border: "1px solid rgba(255,255,255,.06)",
                borderRadius: 8,
                padding: 12,
              }}
            >
              <div style={{ fontSize: 8, opacity: 0.5, letterSpacing: 1, marginBottom: 6 }}>{k.label}</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: k.color, fontFamily: "ui-monospace, monospace" }}>
                {k.value}
              </div>
              <div style={{ fontSize: 9, opacity: 0.5, marginTop: 4 }}>{k.sub}</div>
            </div>
          ))}
        </div>

        {/* status badges */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 12 }}>
          {[
            { label: "Runway", sub: "53 días al burn rate actual", color: "#ef4444" },
            { label: "Cobranzas", sub: "5 cuotas vencidas", color: "#ef4444" },
            { label: "Flujo Neto", sub: "Positivo en el período", color: "#22c55e" },
          ].map((b) => (
            <div
              key={b.label}
              style={{
                background: "#11181a",
                border: "1px solid rgba(255,255,255,.06)",
                borderRadius: 8,
                padding: "10px 12px",
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 10,
              }}
            >
              {dot(b.color)}
              <div>
                <div style={{ fontWeight: 600 }}>{b.label}</div>
                <div style={{ opacity: 0.55, fontSize: 9 }}>{b.sub}</div>
              </div>
            </div>
          ))}
        </div>

        {/* progress bars */}
        <div
          style={{
            background: "#11181a",
            border: "1px solid rgba(255,255,255,.06)",
            borderRadius: 8,
            padding: 14,
            marginBottom: 10,
          }}
        >
          <div style={{ fontSize: 10, fontWeight: 600, marginBottom: 10 }}>Progreso vs Objetivo — Abr 2026</div>
          {[
            { label: "Facturación", pct: 72, color: "#22d3ee" },
            { label: "Cobrado (percibido)", pct: 50, color: "#22d3ee" },
            { label: "Saldo de caja — objetivo 3 meses operativos", pct: 8, color: "#a78bfa" },
          ].map((p, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, opacity: 0.7, marginBottom: 4 }}>
                <span>{p.label}</span>
                <span>{["$77,621 / $108,333", "$48,469 / $108,165", "$3,110 / $99,000"][i]}</span>
              </div>
              <div style={{ height: 4, background: "rgba(255,255,255,.06)", borderRadius: 99 }}>
                <div style={{ width: `${p.pct}%`, height: "100%", background: p.color, borderRadius: 99 }} />
              </div>
            </div>
          ))}
        </div>

        {/* bottom row: bar chart + ventas */}
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 10 }}>
          <div style={{ background: "#11181a", border: "1px solid rgba(255,255,255,.06)", borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 600, marginBottom: 8 }}>Flujo de Caja — Abr 2026</div>
            <svg width="100%" height="100" viewBox="0 0 400 100" preserveAspectRatio="none">
              {Array.from({ length: 30 }).map((_, i) => {
                const isIncome = Math.sin(i * 1.7) > -0.2 && i % 3 !== 0;
                const h = 15 + Math.abs(Math.sin(i * 0.9 + i * 0.3)) * 70;
                return (
                  <rect
                    key={i}
                    x={i * 13 + 4}
                    y={100 - h}
                    width={9}
                    height={h}
                    fill={isIncome ? "#22d3ee" : "#ef4444"}
                    opacity={0.85}
                  />
                );
              })}
            </svg>
          </div>
          <div style={{ background: "#11181a", border: "1px solid rgba(255,255,255,.06)", borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 10, fontWeight: 600, marginBottom: 8 }}>Ventas — Abr 2026</div>
            {[
              { label: "PRODUCTO A", val: "$64,899", n: 5, w: 90 },
              { label: "PRODUCTO B", val: "$9,600", n: 18, w: 14 },
              { label: "Servicios", val: "$2,511", n: 1, w: 4 },
              { label: "EVENTOS", val: "$896", n: 1, w: 2 },
            ].map((v) => (
              <div key={v.label} style={{ marginBottom: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, opacity: 0.7 }}>
                  <span>{v.label}</span>
                  <span style={{ fontFamily: "ui-monospace, monospace", color: "#22d3ee" }}>{v.val}</span>
                </div>
                <div style={{ height: 3, background: "rgba(255,255,255,.06)", borderRadius: 99, marginTop: 3 }}>
                  <div style={{ width: `${v.w}%`, height: "100%", background: "#22d3ee" }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// MOCKUP 2: DISTRIBUCIÓN / RUTAS (Café Aruba-style)
// ============================================================

const DistribucionMockup = () => {
  const navItems = [
    { icon: "▣", label: "Panel" },
    { icon: "📋", label: "Reporte del Día" },
    { icon: "👥", label: "Clientes" },
    { icon: "👤", label: "Vendedores" },
    { icon: "📦", label: "Depósito" },
    { icon: "💰", label: "Caja" },
    { icon: "🛠", label: "Service" },
    { icon: "📦", label: "Productos" },
  ];

  return (
    <div style={{ display: "flex", background: "#f5f5f7", height: 540, color: "#1a2332", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <Sidebar
        brand={{ name: "EMPRESA", color: "#fff" }}
        brandSub="GERENCIA"
        items={navItems}
        activeIndex={0}
        theme="light"
      />
      <div style={{ flex: 1, padding: 18, overflow: "hidden", background: "#f5f5f7" }}>
        {/* header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>Panel</div>
            <div style={{ fontSize: 10, opacity: 0.55 }}>Vista gerencial</div>
          </div>
          <div style={{ display: "flex", gap: 4, background: "#1a2332", padding: 3, borderRadius: 6, fontSize: 10 }}>
            <div style={{ padding: "4px 10px", background: "#fff", color: "#1a2332", borderRadius: 4, fontWeight: 600 }}>Hoy</div>
            <div style={{ padding: "4px 10px", color: "rgba(255,255,255,.7)" }}>Mes</div>
          </div>
        </div>

        {/* KPI cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 14 }}>
          {[
            { label: "VENDIDO", val: "$182,400", sub: "248.5 kg", color: "#1a2332" },
            { label: "COBRADO", val: "$94,720", sub: "32 clientes", color: "#1a2332" },
            { label: "DEUDA TOTAL", val: "$54.0M", sub: "118 de 180 deben", color: "#e5484d" },
            { label: "STOCK DEPÓSITO", val: "1,957 kg", sub: "5/7 cerrados", color: "#1a2332" },
          ].map((k) => (
            <div
              key={k.label}
              style={{
                background: "#fff",
                borderRadius: 10,
                padding: 12,
                boxShadow: "0 1px 3px rgba(0,0,0,.04)",
                border: "1px solid rgba(0,0,0,.04)",
              }}
            >
              <div style={{ fontSize: 8, opacity: 0.5, letterSpacing: 1, marginBottom: 6, fontWeight: 600 }}>{k.label}</div>
              <div style={{ fontSize: 18, fontWeight: 800, color: k.color, fontFamily: "ui-monospace, monospace" }}>
                {k.val}
              </div>
              <div style={{ fontSize: 9, opacity: 0.5, marginTop: 4 }}>{k.sub}</div>
            </div>
          ))}
        </div>

        {/* alerts */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 9, opacity: 0.55, letterSpacing: 1.5, marginBottom: 6, fontWeight: 600 }}>ALERTAS</div>
          {[
            { type: "red", title: "11 clientes sin pagar hace +30 días", sub: "CLIENTE A, CLIENTE B, CLIENTE C" },
            { type: "red", title: "Stock crítico: 1,957 kg en depósito", sub: "Acción urgente" },
            { type: "yellow", title: "5 tickets de service abiertos", sub: "Clientes esperando reparación" },
            { type: "yellow", title: "6 vendedores sin carga hoy", sub: "Vendedor A, Vendedor B, Vendedor C" },
          ].map((a, i) => (
            <div
              key={i}
              style={{
                background: a.type === "red" ? "#fff1f0" : "#fffbeb",
                borderRadius: 8,
                padding: "8px 12px",
                marginBottom: 4,
                fontSize: 10,
                display: "flex",
                gap: 8,
                alignItems: "flex-start",
                border: `1px solid ${a.type === "red" ? "rgba(229,72,77,.15)" : "rgba(245,158,11,.15)"}`,
              }}
            >
              <span style={{ marginTop: 4 }}>{dot(a.type === "red" ? "#e5484d" : "#f59e0b")}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, color: a.type === "red" ? "#c5343a" : "#a16207" }}>{a.title}</div>
                <div style={{ opacity: 0.6, fontSize: 9, marginTop: 1 }}>{a.sub}</div>
              </div>
              <span style={{ fontSize: 9, opacity: 0.5 }}>ver →</span>
            </div>
          ))}
        </div>

        {/* chart */}
        <div style={{ background: "#fff", borderRadius: 10, padding: 14, boxShadow: "0 1px 3px rgba(0,0,0,.04)", border: "1px solid rgba(0,0,0,.04)" }}>
          <div style={{ fontSize: 10, fontWeight: 600, marginBottom: 10 }}>ÚLTIMOS 7 DÍAS</div>
          <svg width="100%" height="120" viewBox="0 0 500 120" preserveAspectRatio="none">
            {["Vie", "Sáb", "Dom", "Lun", "Mar", "Mié", "Jue"].map((d, i) => {
              const h1 = [70, 50, 15, 25, 60, 80, 75][i];
              const h2 = [50, 30, 10, 55, 40, 50, 95][i];
              return (
                <g key={d}>
                  <rect x={i * 70 + 24} y={120 - h1} width={20} height={h1} fill="#3b82f6" opacity="0.85" />
                  <rect x={i * 70 + 46} y={120 - h2} width={20} height={h2} fill="#22c55e" opacity="0.85" />
                  <text x={i * 70 + 44} y={115} fontSize="10" fill="#666" textAnchor="middle">
                    {d}
                  </text>
                </g>
              );
            })}
          </svg>
          <div style={{ display: "flex", gap: 12, fontSize: 9, opacity: 0.65, marginTop: 4, justifyContent: "center" }}>
            <span>{dot("#3b82f6")} Vendido</span>
            <span>{dot("#22c55e")} Cobrado</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================
// MOCKUP 3: VENTAS / RANKING
// ============================================================

const VentasMockup = () => {
  const navItems = [
    { icon: "▣", label: "Panel" },
    { icon: "▤", label: "Resumen" },
    { icon: "✦", label: "Asistente" },
    { section: "OPERACIÓN" },
    { icon: "◎", label: "Objetivos" },
    { icon: "♢", label: "Ventas" },
    { icon: "◈", label: "Clientes" },
    { icon: "👤", label: "Vendedores" },
    { section: "REPORTES" },
    { icon: "▤", label: "Ranking" },
    { icon: "▤", label: "Comisiones" },
  ];

  return (
    <div style={{ display: "flex", background: "#0b0f0e", color: "rgba(255,255,255,.92)", fontFamily: "system-ui, -apple-system, sans-serif", height: 540 }}>
      <Sidebar
        brand={{ name: "EMPRESA", color: "#22d3ee" }}
        brandSub="VENTAS"
        items={navItems}
        activeIndex={5}
      />
      <div style={{ flex: 1, padding: 18, overflow: "hidden" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ color: "#22d3ee" }}>♢</span> Ventas
            </div>
            <div style={{ fontSize: 10, opacity: 0.5 }}>Top vendedores y comisiones</div>
          </div>
          <button
            style={{
              background: "transparent",
              border: "1px solid rgba(255,255,255,.15)",
              color: "rgba(255,255,255,.8)",
              padding: "5px 12px",
              fontSize: 10,
              borderRadius: 6,
            }}
          >
            ⤓ Exportar
          </button>
        </div>

        {/* sub-tabs */}
        <div style={{ display: "flex", gap: 12, fontSize: 11, marginBottom: 12, borderBottom: "1px solid rgba(255,255,255,.06)", paddingBottom: 6 }}>
          <span style={{ opacity: 0.5 }}>Lista</span>
          <span style={{ color: "#22d3ee", fontWeight: 600, paddingBottom: 4, borderBottom: "2px solid #22d3ee" }}>Ranking</span>
          <span style={{ opacity: 0.5 }}>Cobranzas</span>
        </div>

        {/* months tabs */}
        <div style={{ display: "flex", gap: 4, fontSize: 10, marginBottom: 14, color: "rgba(255,255,255,.5)" }}>
          {["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"].map((m, i) => (
            <div
              key={m}
              style={{
                padding: "3px 8px",
                borderRadius: 99,
                background: i === 3 ? "#22d3ee" : "transparent",
                color: i === 3 ? "#08272d" : "inherit",
                fontWeight: i === 3 ? 700 : 400,
              }}
            >
              {m}
            </div>
          ))}
        </div>

        {/* totals */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10, marginBottom: 14 }}>
          <div style={{ background: "#11181a", border: "1px solid rgba(255,255,255,.06)", borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 8, opacity: 0.5, letterSpacing: 1, marginBottom: 4 }}>TOTAL VENDIDO</div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "ui-monospace, monospace" }}>$77,621</div>
          </div>
          <div style={{ background: "#11181a", border: "1px solid rgba(255,255,255,.06)", borderRadius: 8, padding: 12 }}>
            <div style={{ fontSize: 8, opacity: 0.5, letterSpacing: 1, marginBottom: 4 }}>TOTAL COBRADO</div>
            <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "ui-monospace, monospace", color: "#22d3ee" }}>
              $22,343
            </div>
          </div>
        </div>

        {/* ranking */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600, marginBottom: 8 }}>
          🏆 Ranking
        </div>

        {[
          { rank: 1, name: "Vendedor A", vendido: "$57,000", cobrado: "$10,000", pct: 18, comision: "$5,700", w: 95 },
          { rank: 2, name: "Vendedor B", vendido: "$9,400", cobrado: "$7,800", pct: 83, comision: "$940", w: 18 },
          { rank: 3, name: "Vendedor C", vendido: "$5,200", cobrado: "$3,400", pct: 65, comision: "$520", w: 10 },
        ].map((r) => (
          <div
            key={r.rank}
            style={{
              background: "#11181a",
              border: "1px solid rgba(255,255,255,.06)",
              borderRadius: 8,
              padding: 12,
              marginBottom: 8,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <span
                style={{
                  width: 18,
                  height: 18,
                  borderRadius: 99,
                  background: r.rank === 1 ? "#22d3ee" : "rgba(255,255,255,.1)",
                  color: r.rank === 1 ? "#08272d" : "#fff",
                  fontSize: 10,
                  fontWeight: 700,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {r.rank}
              </span>
              <span style={{ fontSize: 12, fontWeight: 600 }}>{r.name}</span>
              <span style={{ fontSize: 8, padding: "1px 6px", borderRadius: 99, background: "rgba(34,211,238,.15)", color: "#22d3ee" }}>
                jugador
              </span>
            </div>
            <div style={{ height: 3, background: "rgba(255,255,255,.06)", borderRadius: 99, marginBottom: 8 }}>
              <div style={{ width: `${r.w}%`, height: "100%", background: "#22d3ee", borderRadius: 99 }} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, fontSize: 9 }}>
              <div>
                <div style={{ opacity: 0.5 }}>Vendido</div>
                <div style={{ fontFamily: "ui-monospace, monospace", fontSize: 11 }}>{r.vendido}</div>
              </div>
              <div>
                <div style={{ opacity: 0.5 }}>Cobrado</div>
                <div style={{ fontFamily: "ui-monospace, monospace", fontSize: 11, color: "#22d3ee" }}>{r.cobrado}</div>
              </div>
              <div>
                <div style={{ opacity: 0.5 }}>% cobro</div>
                <div style={{ fontSize: 11 }}>{r.pct}%</div>
              </div>
              <div>
                <div style={{ opacity: 0.5 }}>Comisión</div>
                <div style={{ fontFamily: "ui-monospace, monospace", fontSize: 11, color: "#f59e0b" }}>{r.comision}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ============================================================
// MOCKUP 4: STOCK / DISTRIBUCIÓN VENDEDORES
// ============================================================

const StockMockup = () => {
  const navItems = [
    { icon: "▣", label: "Panel" },
    { icon: "📋", label: "Reporte del Día" },
    { icon: "👥", label: "Clientes" },
    { icon: "👤", label: "Vendedores" },
    { icon: "📦", label: "Depósito" },
    { icon: "💰", label: "Caja" },
    { icon: "🛠", label: "Service" },
    { icon: "📦", label: "Productos" },
  ];

  return (
    <div style={{ display: "flex", background: "#f5f5f7", height: 540, color: "#1a2332", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      <Sidebar
        brand={{ name: "EMPRESA", color: "#fff" }}
        brandSub="GERENCIA"
        items={navItems}
        activeIndex={3}
        theme="light"
      />
      <div style={{ flex: 1, padding: 18, overflow: "hidden" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>Ranking Vendedores</div>
            <div style={{ fontSize: 10, opacity: 0.55 }}>Mes actual vs anterior</div>
          </div>
          <div style={{ width: 140, height: 24, background: "#fff", borderRadius: 6, fontSize: 10, padding: "0 8px", display: "flex", alignItems: "center", color: "#999", border: "1px solid rgba(0,0,0,.06)" }}>
            🔍 Buscar vendedor...
          </div>
        </div>

        {/* category tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 14, fontSize: 10 }}>
          {[
            { label: "Venta ($)", active: true },
            { label: "Kilos" },
            { label: "Cobranza ($)" },
            { label: "Clientes" },
            { label: "Operaciones" },
          ].map((t) => (
            <div
              key={t.label}
              style={{
                padding: "5px 10px",
                background: t.active ? "#1a2332" : "#fff",
                color: t.active ? "#fff" : "#1a2332",
                borderRadius: 6,
                fontWeight: t.active ? 600 : 400,
                border: "1px solid rgba(0,0,0,.06)",
              }}
            >
              {t.label}
            </div>
          ))}
        </div>

        {/* total */}
        <div style={{ background: "#fff", borderRadius: 10, padding: 14, marginBottom: 12, boxShadow: "0 1px 3px rgba(0,0,0,.04)", border: "1px solid rgba(0,0,0,.04)" }}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: 8, opacity: 0.5, letterSpacing: 1, fontWeight: 600 }}>TOTAL VENTA ($)</div>
              <div style={{ fontSize: 22, fontWeight: 800, fontFamily: "ui-monospace, monospace", marginTop: 4 }}>$81,031,000</div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 9, opacity: 0.5 }}>Mes anterior</div>
              <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>$42,150,000</div>
              <div style={{ fontSize: 9, color: "#22c55e", marginTop: 2 }}>↑ 92%</div>
            </div>
          </div>
        </div>

        {/* charts */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
          <div style={{ background: "#fff", borderRadius: 10, padding: 12, boxShadow: "0 1px 3px rgba(0,0,0,.04)", border: "1px solid rgba(0,0,0,.04)" }}>
            <div style={{ fontSize: 8, letterSpacing: 1, opacity: 0.55, fontWeight: 600, marginBottom: 6 }}>MES ACTUAL VS ANTERIOR</div>
            <svg width="100%" height="100" viewBox="0 0 220 100" preserveAspectRatio="none">
              {[80, 65, 45, 28, 18, 5].map((h, i) => (
                <rect key={i} x={i * 35 + 6} y={100 - h} width={26} height={h} fill="#e5484d" opacity="0.85" />
              ))}
            </svg>
          </div>
          <div style={{ background: "#fff", borderRadius: 10, padding: 12, boxShadow: "0 1px 3px rgba(0,0,0,.04)", border: "1px solid rgba(0,0,0,.04)" }}>
            <div style={{ fontSize: 8, letterSpacing: 1, opacity: 0.55, fontWeight: 600, marginBottom: 6 }}>DISTRIBUCIÓN VENTA ($)</div>
            <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
              <svg width="86" height="86" viewBox="0 0 86 86">
                <circle cx="43" cy="43" r="32" fill="none" stroke="#e5484d" strokeWidth="14" strokeDasharray="84 200" />
                <circle cx="43" cy="43" r="32" fill="none" stroke="#f59e0b" strokeWidth="14" strokeDasharray="54 200" strokeDashoffset="-84" />
                <circle cx="43" cy="43" r="32" fill="none" stroke="#3b82f6" strokeWidth="14" strokeDasharray="36 200" strokeDashoffset="-138" />
                <circle cx="43" cy="43" r="32" fill="none" stroke="#22c55e" strokeWidth="14" strokeDasharray="26 200" strokeDashoffset="-174" />
              </svg>
              <div style={{ fontSize: 9, lineHeight: 1.6 }}>
                <div>{dot("#e5484d")} Vendedor A 42%</div>
                <div>{dot("#f59e0b")} Vendedor B 27%</div>
                <div>{dot("#3b82f6")} Vendedor C 18%</div>
                <div>{dot("#22c55e")} Vendedor D 13%</div>
              </div>
            </div>
          </div>
        </div>

        {/* ranking rows */}
        {[
          { name: "Vendedor A", pct: 42, val: "$33,864,000", w: 95, color: "#e5484d", icon: "🥇" },
          { name: "Vendedor B", pct: 27, val: "$22,096,000", w: 60, color: "#f59e0b", icon: "🥈" },
          { name: "Vendedor C", pct: 18, val: "$14,648,000", w: 40, color: "#3b82f6", icon: "🥉" },
        ].map((r, i) => (
          <div
            key={i}
            style={{
              background: "#fff",
              borderRadius: 10,
              padding: "10px 12px",
              marginBottom: 6,
              display: "flex",
              alignItems: "center",
              gap: 10,
              boxShadow: "0 1px 3px rgba(0,0,0,.04)",
              border: "1px solid rgba(0,0,0,.04)",
            }}
          >
            <span style={{ fontSize: 14 }}>{r.icon}</span>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, marginBottom: 4 }}>
                <span style={{ fontWeight: 600 }}>{r.name} <span style={{ color: r.color, fontWeight: 400, marginLeft: 4 }}>{r.pct}%</span></span>
                <span style={{ fontFamily: "ui-monospace, monospace", fontWeight: 700 }}>{r.val}</span>
              </div>
              <div style={{ height: 4, background: "rgba(0,0,0,.04)", borderRadius: 99 }}>
                <div style={{ width: `${r.w}%`, height: "100%", background: r.color, borderRadius: 99 }} />
              </div>
            </div>
            <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 4, background: "#f5f5f7", color: "#666" }}>↑ 100%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

window.FinanceMockup = FinanceMockup;
window.DistribucionMockup = DistribucionMockup;
window.VentasMockup = VentasMockup;
window.StockMockup = StockMockup;
window.BrowserChrome = BrowserChrome;
