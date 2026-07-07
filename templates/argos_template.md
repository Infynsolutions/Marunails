# 📗 Argos — Plantilla Google Sheets

## Estructura Universal de Datos

Esta plantilla funciona para cualquier tipo de negocio. La clave está en que
cada fila representa **un movimiento financiero** (ingreso o gasto).

## Columnas Requeridas

| Columna | Tipo | Ejemplo | Obligatoria |
|---------|------|---------|-------------|
| **Fecha** | Fecha (DD/MM/YYYY) | 15/03/2026 | ✅ Sí |
| **Monto** | Número | 320000 | ✅ Sí |
| **Tipo** | Texto: `Ingreso` o `Gasto` | Ingreso | ✅ Sí |
| **Categoría** | Texto libre | Ventas mayoristas | ✅ Sí |
| **Descripción** | Texto libre | Venta a Hotel Palermo | ✅ Sí |
| **Estado** | Texto: `Cobrado`, `Pagado`, `Pendiente` | Cobrado | Recomendada |
| **Referencia** | Texto libre (N° factura, recibo) | FA-1042 | Opcional |

## Reglas Importantes

1. **Una fila = un movimiento**. No agrupar varios pagos en una fila.
2. **Montos siempre positivos**. El campo "Tipo" define si es ingreso o gasto.
3. **Fechas consistentes**. Usar siempre DD/MM/YYYY.
4. **Categorías consistentes**. Usar siempre los mismos nombres (ejemplo: "Logística", no a veces "Logistica" y a veces "Flete").
5. **No dejar filas vacías** entre registros.
6. **La fila 1 son los encabezados**. Los datos empiezan en fila 2.

## Categorías Sugeridas por Industria

### Gastronomía / Café (Café Aruba)
**Ingresos:** Ventas mayoristas, Ventas minoristas, Ventas e-commerce, Servicios, Catering
**Gastos:** Materia prima, Logística, Sueldos, Alquiler, Marketing, Servicios, Impuestos

### Logística (Green Trip)
**Ingresos:** Alquiler equipos, Suscripciones, Servicios corporativos
**Gastos:** Mantenimiento flota, Seguros, Sueldos, Combustible, Marketing, Tecnología

### Consultoría (Stannum)
**Ingresos:** Honorarios consultoría, Workshops, Retainers mensuales
**Gastos:** Sueldos, Software, Viáticos, Marketing, Oficina, Capacitación

## Cómo Configurar

1. Crear un Google Sheet nuevo o copiar la plantilla
2. Escribir los encabezados exactos en la fila 1
3. Compartir el Sheet con la service account de Argos (solo lectura)
4. Copiar el ID del Sheet (la parte larga de la URL)
5. Agregarlo en la configuración del tenant en Supabase

### ¿Dónde está el ID del Sheet?

En la URL: `https://docs.google.com/spreadsheets/d/`**`ESTE_ES_EL_ID`**`/edit`

## Ejemplo de Datos (Café Aruba)

| Fecha | Monto | Tipo | Categoría | Descripción | Estado | Referencia |
|-------|-------|------|-----------|-------------|--------|------------|
| 12/03/2026 | 320000 | Ingreso | Ventas mayoristas | Venta a Hotel Palermo | Cobrado | FA-1042 |
| 11/03/2026 | 85000 | Gasto | Logística | LogísticaExpress mensual | Pagado | OC-2031 |
| 10/03/2026 | 145000 | Ingreso | Ventas mayoristas | Venta a Café Central | Pendiente | FA-1041 |
| 10/03/2026 | 120000 | Gasto | Alquiler | Alquiler depósito Barracas | Pagado | - |
| 09/03/2026 | 210000 | Ingreso | Ventas e-commerce | Pedidos MercadoLibre | Cobrado | FA-1040 |
