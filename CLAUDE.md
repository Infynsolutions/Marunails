# INFYN — Contexto del proyecto

## Qué es

Consultora estratégica para PyMEs latinoamericanas.  
Ayuda a negocios que crecen en caos a ordenarse con procesos, estructura y visión.

**Propuesta:** Convertimos complejidad en sistema.  
**Posicionamiento:** No somos una agencia ni una tech company. Somos una consultora moderna que también implementa.

---

## Archivos del proyecto

| Archivo       | Descripción                                      |
|---------------|--------------------------------------------------|
| `index.html`  | Sitio web completo (HTML + CSS inline, sin build) |
| `brand.md`    | Sistema de diseño: colores, tipografía, aurora CSS |

---

## Stack

- HTML + CSS puro en un solo archivo (`index.html`)
- Sin frameworks, sin build tools, sin dependencias
- Tipografía: **Inter** via Google Fonts
- Sin JavaScript (por ahora)

---

## Sistema de diseño

### Colores

```
Verde principal : #0F7B53
Verde oscuro    : #0A3F2C
Verde acento    : #2ED47A   ← highlights en dark, botón primario
Fondo oscuro    : #060D09   ← base de todas las secciones dark
Gris claro      : #F5F7F6
Blanco          : #FFFFFF
```

### Tipografía

Inter. Títulos `font-weight: 800`, cuerpo `400`. Labels en uppercase con `letter-spacing`.

### Efecto de marca: Aurora Verde

Gradiente radial difuso verde sobre fondo `#060D09`. Clases reutilizables:

- `.aurora-bg` — glow diagonal (hero, resultados)
- `.aurora-center` — glow centrado (quote)
- `.aurora-subtle` — glow sutil (método)
- `.grid-bg` — cuadrícula de fondo 56px (combinar con aurora)

Ver código completo en `brand.md`.

### Layouts por sección

| Sección   | Fondo       | Clases CSS                    |
|-----------|-------------|-------------------------------|
| Hero      | `#060D09`   | `aurora-bg`                   |
| Problema  | `#FFFFFF`   | —                             |
| Método    | `#060D09`   | `aurora-bg aurora-subtle grid-bg` |
| Resultados| `#060D09`   | `aurora-bg`                   |
| Quote     | `#060D09`   | `aurora-bg aurora-center`     |
| CTA       | `#F5F7F6`   | —                             |
| Footer    | `#060D09`   | —                             |

---

## Tono de comunicación

Directo. Claro. Sin humo.

❌ "Transformamos tu negocio con soluciones innovadoras"  
✅ "Tu negocio no necesita más ventas. Necesita orden."

**Palabras clave:** orden, sistema, procesos, estructura, resultados medibles, implementación real.

---

## Reglas de diseño

- Estructura > estética
- Todo legible en 3 segundos
- Mucho aire entre elementos
- No agregar decoración sin función
- No usar diseño "startup hype" ni estética cripto

---

## Negocio

**Servicios:**
1. Diagnóstico operacional (48–72 hs)
2. Diseño del sistema (1 semana)
3. Implementación real (2–6 semanas)
4. Seguimiento y métricas (30 días)

**Dolores del cliente:**
- Dependencia del dueño
- Falta de procesos
- Decisiones sin datos

**Mercado:** PyMEs de Argentina, Chile y México.

**CTA principal:** "Agendar diagnóstico" (primera conversación sin costo).
