# INFYN — Lecciones de proyecto

Lista de aprendizajes acumulados sesión a sesión. Revisar al inicio de cada sesión nueva.

---

## Marketing y copy

### Regla: No anti-positioning de competencia en la web pública
- **Por qué:** Sofia rechazó la versión con cards "Consultores que no ejecutan / Software factories que se van / Sistemas genéricos que no calzan". Quiere foco en dolores del cliente, no comparación con otros proveedores. El cliente PyME quiere sentirse entendido, no escuchar del mercado.
- **Cuándo aplica:** Toda copy de cara al cliente (web, landings, ads). El anti-positioning queda reservado para conversaciones uno-a-uno y materiales internos.

### Regla: Pulso vende preguntas estratégicas, no operativas
- **Por qué:** Las preguntas tipo "¿cómo cerré febrero comparado con enero?" hacen ver a Pulso como un dashboard más. Las preguntas tipo "¿conviene invertir $500K en una segunda sucursal?" o "¿cuál es mi cliente más rentable?" comunican co-pensador estratégico — categoría nueva. Es lo que un dueño piensa a las 11 PM y nadie le responde.
- **Cuándo aplica:** Cualquier mockup o copy de Pulso debe mostrar preguntas de director/dueño, no de empleado operativo.

### Regla: Positioning de INFYN = "agencia que implementa y se queda"
- **Por qué:** El gap real del mercado argentino (consultoras no ejecutan, software factories se van, SaaS genéricos no calzan) define la categoría que ocupa INFYN. Esto es la base de toda la comunicación, no solo una frase de pitch.
- **Cuándo aplica:** Siempre que se decida copy, mensajes, ads o materiales nuevos. El modelo de 3 capas (diagnóstico → sistema a medida → operación continua/retainer) es la IP del negocio.

---

## Diseño visual

### Regla: Tipografía B2B tech = peso primero, elegancia después
- **Por qué:** Probamos Instrument Serif sola (peso 400 regular) y se sintió "liviana, casi invitación de boda" para una agencia que vende IA + retainer + autoridad técnica. La fragilidad transmite lo opuesto al posicionamiento. Solución que funcionó: Bricolage Grotesque 800 (sans display con peso) para headline base + Instrument Serif italic solo en `.acento` (signature editorial).
- **Cuándo aplica:** Cualquier headline o título principal en cualquier landing/material. Mantener el contraste sans heavy + serif italic como signature.

### Regla: Si algo se siente "genérico", comparar contra referencias del sector
- **Por qué:** Cuando Sofia dijo "siento que falta más impacto, es una web genérica", la solución no era una intuición de diseñador — era investigar 6 sitios del sector (Linear, Vercel, Anthropic, Resend, Stripe, Cursor) y mapear gaps específicos (tipografía sin personalidad, headline no domina el fold, aurora muy sutil, hero simétrico predecible, verde overused).
- **Cuándo aplica:** Antes de proponer cambios visuales subjetivos. La comparación contra referencias da insights concretos en vez de opiniones.

### Regla: Verde acento de marca con criterio de escasez
- **Por qué:** El verde acento (`#2ED47A`) aparecía en ~8 lugares (eyebrows, .acento, botones, paso-num, paso-tiempo, hero-tag, live-dots, cards). Cuando todo es verde, nada es verde. Reducirlo a 3-4 lugares clave (botón primario, .acento italic, aurora background, live signals) hace que cada aparición se sienta intencional.
- **Cuándo aplica:** Al sumar elementos nuevos, preguntarse: "¿este lugar NECESITA verde acento o sirve con neutro?". Default a neutro, verde solo cuando es decisión consciente.

---

## Workflow

### Regla: Pivots grandes se validan con preguntas concretas antes de tocar código
- **Por qué:** Al repositionar INFYN de "consultora pura" a "agencia híbrida con Pulso", se hicieron 4 preguntas concretas (servicio hero, role de Pulso, pricing público, casos) antes de implementar. Esto evitó rehacer trabajo y permitió a Sofia tomar decisiones de negocio en vez de aprobar implementaciones.
- **Cuándo aplica:** Cuando un cambio toca el posicionamiento o copy estructural. AskUserQuestion antes de Edit.

### Regla: Deployar siempre al terminar cambios visuales
- **Por qué:** Sofia valida en su browser real (Chrome, retina, su resolución). Los screenshots locales son aproximaciones — el feedback útil viene de ver en producción.
- **Cuándo aplica:** Siempre después de cambios al sitio. `vercel --prod` y avisar la URL.

### Regla: Verificar `vercel whoami` antes de deployar
- **Por qué:** El CLI puede quedar logueado con una cuenta incorrecta (contacto-9286 en vez de sofiafbravo). El proyecto `infyn-web` vive en `sofiafbravos-projects`. Si el `orgId` en `.vercel/project.json` no matchea la cuenta activa, el deploy falla o va al proyecto equivocado.
- **Cuándo aplica:** Al inicio de cualquier sesión que incluya deploy. Si `vercel whoami` no dice `sofiafbravo`, hacer `vercel logout` + `vercel login` + `vercel link --project infyn-web --scope sofiafbravos-projects --yes`.

### Regla: `cleanUrls: true` en vercel.json para rutas sin extensión
- **Por qué:** Sin esta config, Vercel sirve `ejemplos.html` en `/ejemplos.html` pero devuelve 404 en `/ejemplos`. El nav linkea a `/ejemplos`, así que sin `cleanUrls` la página es inaccesible desde el sitio.
- **Cuándo aplica:** Cualquier página nueva que se agregue al proyecto (diagnostico.html, ejemplos.html, etc.). El `vercel.json` ya tiene `cleanUrls: true` desde 2026-05-22, no volver a sacarlo.

### Regla: En conflictos de merge, si el remote es la verdad, usar `git checkout --theirs`
- **Por qué:** Al hacer pull con conflictos en `index.html` (20+ marcadores), resolver a mano es lento y propenso a errores. Si Sofia confirma que el remote es la versión correcta, `git checkout --theirs <archivo>` resuelve todo en un comando.
- **Cuándo aplica:** Cuando hay conflictos y el usuario dice "lo que vale es lo del github" o equivalente.

### Regla: Para revisar en local idéntico a prod, levantar un server (no abrir con `file://`)
- **Por qué:** El logo usa ruta absoluta (`<img src="/Logo Infyn.png">`) y `vercel.json` tiene `cleanUrls`. Abriendo el `index.html` directo (protocolo `file://`) el logo se ve roto y las rutas absolutas/`/ejemplos` no resuelven — parece un bug del sitio cuando no lo es. Levantando `python3 -m http.server 8000` desde la carpeta del proyecto y abriendo `http://localhost:8000`, las rutas absolutas resuelven igual que en Vercel.
- **Cuándo aplica:** Cuando Sofia quiere ver cambios en local antes de deployar. Nunca diagnosticar "logo roto / 404" sobre un render `file://`.

### Regla: En el repo `Marunails` conviven varias apps — la de producción la define `vercel.json`
- **Por qué:** El repo tiene mezclados el sistema de Maru (`marunails/app.py`, Flask+Supabase), un proyecto Argos (`app.py` en raíz + `backend/` FastAPI + `frontend/` React + `argos-v4b.html`), un `inventario/` y los HTML de INFYN. El `CLAUDE.md` del repo describe solo el sitio estático de INFYN, así que leerlo lleva a la app equivocada. `vercel.json` apunta a `marunails/app.py` — esa es la que está en producción.
- **Cuándo aplica:** Al empezar cualquier sesión sobre este repo. Confirmar el entrypoint con `vercel.json` antes de creer al README o al CLAUDE.md.

---

## Producto y pricing (SaaS)

### Regla: El alcance de una v1 se define contra lo que el mercado YA paga, no contra lo que el sistema ya tiene construido
- **Por qué:** Para Clara se decidió primero "v1 = turnos + reservas" porque era la parte más armada del sistema de Maru. La evidencia de mercado lo desarmó: los salones **ya pagan** Fresha/Calendly justamente por turnos. Salir por ahí es pelear en el terreno del incumbente (que además tiene marketplace y tuvo plan gratis) y dejar sin atender el dolor que ellos mismos nombran. El tell decisivo: **siguen usando Excel para la plata aunque ya pagan Fresha** — si el software que pagan les resolviera el dinero, ese Excel no existiría.
- **Cuándo aplica:** Al definir el alcance de cualquier producto nuevo. Preguntar "¿por qué cosa ya están pagando?" antes de "¿qué tengo hecho?". Lo que ya pagan está resuelto; el wedge está en lo que siguen haciendo a mano.

### Regla: Los precios de un competidor se verifican en la página del país, no traducidos del dólar
- **Por qué:** Fresha cobra USD 19,95 / 14,95 por miembro en EEUU pero **8.000 / 5.300 ARS** en Argentina. Hace precio regional. Todo el modelo de precios de Clara se armó primero sobre el ancla en dólares (que daba ~USD 75-85 por salón) y hubo que recalcularlo entero al ver `fresha.com/es/pricing`. Además apareció el mejor argumento de venta ahí: el add-on de reportes se cobra **por miembro** (4.500 ARS cada uno).
- **Cuándo aplica:** Cualquier análisis de pricing competitivo en LATAM. Buscar la página localizada del competidor y un SaaS local comparable (NutriPass sirvió de ancla real para Argentina) antes de fijar precio.

### Regla: Nombrar el producto con la palabra exacta que usó el cliente para describir lo que le falta
- **Por qué:** El mercado dijo *"a fin de mes no tenemos **claridad**"*. De ahí salió **Clara** — que además es nombre de mujer (rubro de dueñas) y habilita gratis una asistente con IA ("mandale la foto a Clara"), movimiento que una marca-producto como Fresha no puede hacer. Se descartaron nombres tipo Turnia/Turnero por la regla de arriba: un nombre que dice "agenda" te encasilla en lo que el competidor ya hace.
- **Cuándo aplica:** Al nombrar productos. Buscar primero la transcripción de lo que dijo el cliente. Y chequear que el nombre no describa la parte del producto que NO es el diferencial.

### Regla: Un sub-producto lleva nombre propio adelante y la marca madre como firma
- **Por qué:** INFYN tiene prestigio ante clientes de consultoría, no ante dueñas de peluquería — nunca escucharon el nombre. "INFYN Salón" no le suma nada a esa compradora. El aval sirve al portfolio, no a la venta.
- **Cuándo aplica:** Cualquier sub-producto de INFYN. Nombre propio + "un producto de INFYN" en footer/about/propuestas.

### Regla: Los `.com` de una palabra corta y pronunciable están todos tomados — no gastar vueltas
- **Por qué:** Se verificaron 20 nombres inventados de 5-7 letras (claria, brilla, tersa, esmera, clario, salonia, nitia, lucira, sumia…) en `.com`, `.app`, `.io` y `.co`: **cero disponibles**. Lo que sí queda libre son los compuestos (`claragestion.com`, `clarasistema.com` a USD 11,25).
- **Cuándo aplica:** Al buscar dominio. Ir directo a compuesto + el TLD local del mercado objetivo. Para Argentina, `.com.ar` se saca en **nic.ar** con CUIT — Vercel no maneja `.ar` (ni lo devuelve en el chequeo) y además el dominio local pesa como señal de confianza y SEO frente a un competidor extranjero.

### Regla: El sistema hecho a medida que se quiere replicar suele tener adentro el problema que el SaaS promete resolver
- **Por qué:** Clara se vende como "el turno y la plata en un solo lugar". Pero en el sistema de Maru, `cortes` y `turnos` son **dos mundos desconectados**: `cortes.staff` y `cortes.servicio` son texto libre, sin foreign key ni relación con `turnos`. Copiar el sistema tal cual habría copiado la fragmentación. En Clara el `cortes.turno_id` **es** el producto, no una optimización.
- **Cuándo aplica:** Antes de "duplicar y mejorar" cualquier sistema. Revisar si la propuesta de valor del producto nuevo ya está violada en el modelo de datos del viejo.

### Regla: En Argentina, un reporte mes a mes en pesos nominales miente
- **Por qué:** Un gráfico de facturación en ARS muestra "crecí 8%" cuando en realidad se perdió poder de compra. Mostrar la serie deflactada por IPC (INDEC) es una feature chica, de alto impacto, que un producto traducido del inglés no tiene. Corolario comercial: el precio de lista se revisa cada 3 meses y **"precio congelado 6 meses" se vende como beneficio**, no se esconde.
- **Cuándo aplica:** Cualquier dashboard financiero con series temporales para mercado argentino. Y cualquier pricing en ARS.
