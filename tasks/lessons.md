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
