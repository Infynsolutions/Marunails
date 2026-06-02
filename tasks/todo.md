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

## Backlog (próximas sesiones)

- [ ] WhatsApp como escalón blando además de "agendar diagnóstico"
- [ ] Animaciones de scroll-trigger: entrada con stagger en secciones
- [ ] Sumar Café Aruba como caso con nombre (cuando haya permiso del cliente)
- [ ] Posible landing dedicada a Pulso/Ciro si se quiere llevarlo como producto comprable
- [ ] Considerar segunda línea de data en el ambient chart para más densidad
- [ ] Auditar si el footer necesita información de contacto/email visible
