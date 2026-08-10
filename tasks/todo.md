# INFYN — Tareas en curso y review de sesiones

## Sesión 2026-05-11 — Rediseño completo (cerrada)

### Hecho
- [x] Audit UX/UI inicial del sitio (10 hallazgos críticos detectados)
- [x] Repositioning: "agencia que implementa y se queda" (hero, problema, modelo)
- [x] Modelo de 4 pasos → 3 capas (Diagnóstico → Sistema → Operación continua)
- [x] Pulso renombrado (era Argos) y posicionado como diferencial central
- [x] Pulso reemplaza al chart genérico en el hero
- [x] Chat de Pulso reescrito con preguntas estratégicas de director
- [x] Bloque problema reescrito con dolores del cliente (sin anti-positioning)
- [x] Tipografía: Bricolage Grotesque 800 (headlines) + Instrument Serif italic (.acento)
- [x] Hero asimétrico 1.2/0.8 + headline más grande + beam de luz diagonal
- [x] Verde acento reducido (eyebrows, hero-tag, paso-tiempo a neutro)
- [x] Corner marks `+` verde como signature decoración en secciones dark
- [x] Resultados con casos por industria anonimizados (+30% / −70% / 6 sem)
- [x] CTA con incentivo "diagnóstico se descuenta del proyecto"
- [x] Ambient chart de fondo detrás del Pulso card en hero (data 24/7)
- [x] Deploy a Vercel — live en infyn-web.vercel.app

### Review
La web pasó de SaaS dark genérica (Inter + chart + cards verdes simétricas) a editorial-tech distintiva (Bricolage 800 + acento serif italic + Pulso protagonista + corner marks + beam diagonal).

Cambio más importante: **Pulso pasó de mockup decorativo a diferencial central**. Esto cambia toda la narrativa — vendemos un co-pensador estratégico, no un dashboard. El chat en el hero comunica esto desde el primer segundo, sin que el visitante tenga que leer copy.

Cambio más sutil pero crítico: **el bloque problema sin anti-positioning**. Sofia notó que comparar contra competencia rompe conexión emocional. Los dolores del cliente (dependencia del dueño / datos en mil lugares / decisiones con miedo) mapean 1:1 a la solución y crean narrativa cerrada.

Cambio de mayor impacto visual: **la tipografía híbrida**. Sans heavy para autoridad + serif italic para signature editorial. Es lo que separa a INFYN del resto del mercado argentino (casi nadie usa serifs editoriales en agencias tech).

## Sesión 2026-05-22 — Git sync + Vercel fix (cerrada)

### Hecho
- [x] Commit y push de `index.html` + `.gitignore` al repo
- [x] Resolución de conflicto de merge (remote tenía copy actualizado: Ciro, headline reducido)
- [x] Fix cuenta Vercel: re-login como `sofiafbravo`, link a `sofiafbravos-projects/infyn-web`
- [x] Deploy exitoso a producción (infynsolutions.com)
- [x] Diagnóstico de `/ejemplos` → 404 por falta de cleanUrls
- [x] Agregado `vercel.json` con `cleanUrls: true`
- [x] Re-deploy y verificación: `/ejemplos` resuelve con 200

### Review
Sesión de mantenimiento/ops. El cambio más importante fue el `vercel.json` con `cleanUrls` — sin eso, el link del nav a `/ejemplos` daba 404 para todos los visitantes. También quedó fija la cuenta de Vercel para próximas sesiones.

## Sesión 2026-06-02 — Refinamiento del hero (cerrada)

### Hecho
- [x] Diagnóstico del hero actual (columna izq top-heavy, `.hero-sub` perdido en markup pero CSS huérfano, tarjeta compitiendo con titular)
- [x] Decisión de dirección: refinar y completar (no reinventar) — recomendado y aprobado
- [x] Subline recuperado en tono INFYN ("Convertimos el caos en sistema…") con max-width y ritmo
- [x] Barra fina de prueba al pie del fold (48–72hs · sin costo · 2–6 semanas) con punto verde acento por ítem
- [x] Ritmo vertical reequilibrado (headline → subline → CTAs → barra)
- [x] Headline un toque más grande (clamp tope 76→82px) para dominar el fold
- [x] Verificado desktop + mobile (390px) con screenshots
- [x] Deploy a producción (infynsolutions.com), READY, verificado en vivo

### Review
Sesión de refinamiento puntual del hero. El problema no era estético sino estructural: la columna izquierda quedaba vacía debajo de los botones y el subline se había perdido en un merge previo (el CSS lo seguía estilando). Se resolvió completando el bloque en vez de reinventarlo, respetando toda la intención acumulada (Bricolage+Instrument, aurora, corner marks, tarjeta Ciro, decisión de reducir verde). El acento verde volvió solo en los puntos de la barra de prueba — escasez intencional, no decoración. Gotcha capturado: revisar en local con server, no `file://` (logo roto / 404 falsos).

## Sesión 2026-08-10 — CLARA: diseño del SaaS para estéticas (cerrada, continúa)

### Hecho
- [x] Relevamiento completo del sistema de Maru Nails (`marunails/app.py`, 1.906 líneas, 15 templates, 3 migraciones)
- [x] Diagnóstico: 5 bloqueantes para vender a terceros + riesgo de seguridad (credenciales commiteadas)
- [x] Decisión: **producto nuevo y separado**, Maru Nails NO se toca (queda sin suscripción, es el caso fundador)
- [x] Stack definido: Next.js 16 + Supabase (Auth + RLS) + Tailwind → Vercel/INFYN
- [x] Multi-tenancy: base única, `salon_id` en todas las tablas, RLS por salón, tenant desde el perfil (nunca de la URL)
- [x] Roles: dueño + recepción. Estaciones configurables por salón. Moneda/timezone por salón
- [x] Revisión de plan con office-hours → **wedge corregido**: v1 pasa de "turnos+reservas" a "agenda + caja + cierre de mes"
- [x] Investigación de precios de Fresha (USA y Argentina) + NutriPass como ancla local
- [x] Mercado: **Argentina primero**. Precios en ARS: 14.900 promo → 22.900 / 34.900 lista, 30 días gratis
- [x] Ajuste por inflación definido: regla comercial (revisión trimestral IPC + congelado 6 meses) **y** feature de producto (reportes deflactados)
- [x] Nombre: **CLARA** — un producto de INFYN. Dominios chequeados (20 nombres, 4 tandas)
- [x] Spec de la v1 escrito: `docs/superpowers/specs/2026-08-10-clara-v1-design.md`
- [x] Memoria del proyecto + lecciones actualizadas

### Pendiente (retomar acá)
- [ ] **Correr `/plan-ceo-review` sobre el spec** ← se interrumpió justo al arrancar, es el próximo paso
- [ ] Después: `/plan-eng-review` y de ahí el plan de implementación
- [ ] Registrar `clara.com.ar` en nic.ar (CUIT de INFYN) + `claragestion.com` de respaldo
- [ ] Ronda de demos: mostrar el sistema de Maru a 2-3 dueños argentinos, pedir número o pre-compromiso
- [ ] Crear repo nuevo de Clara y mover el spec ahí

### Review
Sesión de diseño de producto, sin código. El giro que define todo: el pedido original era "duplicar el sistema de Maru y venderlo por suscripción", y el relevamiento + la evidencia de mercado lo convirtieron en algo distinto y mejor.

**El hallazgo que cambió el plan:** se había acordado v1 = turnos + reservas (era la parte más armada del sistema). Cuando Sofia contó que los salones **ya pagan** Fresha/Calendly para turnos y llevan la contabilidad en otro Excel, el alcance quedó invertido — construir turnos era competir de frente con el incumbente y dejar sin atender el dolor que ellos nombran. El tell decisivo: siguen usando Excel para la plata *aunque ya pagan Fresha*.

**El hallazgo técnico que más vale:** el sistema de Maru tiene adentro exactamente la fragmentación que Clara promete resolver. `cortes` y `turnos` son dos mundos desconectados (`cortes.staff` y `cortes.servicio` son texto libre, sin FK). Copiarlo tal cual habría copiado el problema. En Clara el `cortes.turno_id` es el producto.

**Sobre pricing:** verificar la página en español de Fresha cambió el modelo entero — hace precio regional (5.300 ARS por miembro vs USD 14,95). Y ahí apareció el mejor argumento de venta: el add-on de reportes se cobra **por cabeza**, así que un salón de 5 paga 22.500 ARS solo para ver sus números. Clara los incluye.

**Riesgo abierto:** nadie pidió comprar Clara todavía. La ronda de demos es prerrequisito comercial, no técnico — se puede hacer en paralelo al desarrollo, pero tiene que arrancar ya.

## Backlog (próximas sesiones)

- [ ] WhatsApp como escalón blando además de "agendar diagnóstico"
- [ ] Animaciones de scroll-trigger: entrada con stagger en secciones
- [ ] Sumar Café Aruba como caso con nombre (cuando haya permiso del cliente)
- [ ] Posible landing dedicada a Pulso/Ciro si se quiere llevarlo como producto comprable
- [ ] Considerar segunda línea de data en el ambient chart para más densidad
- [ ] Auditar si el footer necesita información de contacto/email visible
