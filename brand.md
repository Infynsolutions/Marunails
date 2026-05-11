# INFYN — Sistema de diseño

## Colores

| Token           | Hex       | Uso                              |
|-----------------|-----------|----------------------------------|
| Verde principal | `#0F7B53` | Botones, links, acentos en claro |
| Verde oscuro    | `#0A3F2C` | Nav, footer, fondos              |
| Verde acento    | `#2ED47A` | Highlights en dark, CTA primario |
| Fondo oscuro    | `#060D09` | Base de todas las secciones dark |
| Gris claro      | `#F5F7F6` | Fondo secciones claras, cards    |
| Blanco          | `#FFFFFF` | Texto en dark, fondos            |

---

## Tipografía

**Inter** (Google Fonts)

| Uso       | Weight |
|-----------|--------|
| Títulos   | 800    |
| Subtítulos| 700    |
| Cuerpo    | 400    |
| Labels    | 600–700, letter-spacing: 2–3px, uppercase |

---

## Efecto Aurora Verde

El efecto de identidad visual principal. Luz ambiental verde difusa sobre fondo muy oscuro.

**Implementación CSS:**
```css
.aurora-bg {
  background: #060D09;
  position: relative;
  overflow: hidden;
}

/* Glow diagonal — para hero y resultados */
.aurora-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 65% 75% at 72% 65%, rgba(26,138,74,0.60) 0%, rgba(10,63,44,0.30) 35%, transparent 70%),
    radial-gradient(ellipse 40% 40% at 30% 20%,  rgba(10,63,44,0.20) 0%, transparent 60%);
  filter: blur(50px);
  pointer-events: none;
  z-index: 0;
}

/* Variante centrada — para quote / CTA oscuro */
.aurora-center::after {
  background:
    radial-gradient(ellipse 70% 60% at 50% 60%, rgba(26,138,74,0.55) 0%, rgba(10,63,44,0.25) 40%, transparent 70%);
  filter: blur(70px);
}

/* Variante sutil — para método / pasos */
.aurora-subtle::after {
  background:
    radial-gradient(ellipse 60% 50% at 80% 50%, rgba(15,123,83,0.25) 0%, transparent 65%),
    radial-gradient(ellipse 40% 40% at 20% 80%, rgba(10,63,44,0.15) 0%, transparent 60%);
  filter: blur(60px);
}
```

**Reglas:**
- Siempre sobre fondo `#060D09`, nunca sobre verde medio
- El glow no debe dominar el contenido, es ambiental
- Todo el contenido de la sección lleva `position: relative; z-index: 1`

---

## Grid sutil de fondo

Para secciones dark que necesitan estructura visual sin peso extra.

```css
.grid-bg::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.028) 1px, transparent 1px);
  background-size: 56px 56px;
  pointer-events: none;
  z-index: 0;
}
```

---

## Layouts

| Layout              | Fondo       | Uso                              |
|---------------------|-------------|----------------------------------|
| Dark + Aurora       | `#060D09`   | Hero, resultados, quote          |
| Dark + Aurora sutil | `#060D09`   | Método / pasos                   |
| Dark + Grid         | `#060D09`   | Método (combinar con aurora)     |
| Blanco + Cards      | `#FFFFFF`   | Problema, claridad               |
| Gris + Form         | `#F5F7F6`   | CTA, contacto                    |

---

## Logo

Símbolo infinito (∞) con flecha integrada hacia arriba-derecha.

- Trazo exterior: `#2ED47A` (verde acento)
- Trazo interior: `#0F7B53` (verde principal)
- Flecha: `#2ED47A`

**Versiones:**
1. Color sobre oscuro (versión principal)
2. Blanco sobre verde oscuro
3. Monocromático (fallback)

**Regla:** debe funcionar en 1 color.

---

## Tono de comunicación

Directo. Claro. Sin humo.

❌ "Transformamos tu negocio con soluciones innovadoras"
✅ "Tu negocio no necesita más ventas. Necesita orden."

---

## Principio

> **Estructura > estética**
> Todo legible en 3 segundos. Menos es más.
