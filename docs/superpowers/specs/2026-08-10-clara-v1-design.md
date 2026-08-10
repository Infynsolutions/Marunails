# Diseño: CLARA v1 — SaaS de gestión para peluquerías y centros de estética

Generado el 2026-08-10 · Estado: DRAFT
Producto de INFYN · Mercado inicial: Argentina

> ⚠️ Este spec vive temporalmente en el repo `Marunails` porque es donde se hizo el
> relevamiento. Al crear el repo de Clara, mover este archivo allí.

---

## 1. Qué es Clara

Software de gestión para peluquerías, centros de estética, barberías y salones de uñas.
Un solo lugar donde **el turno y la plata viven juntos**.

**Eslogan:** *A fin de mes, sabé exactamente cuánto ganaste.*

**Arquitectura de marca:** nombre propio adelante, "un producto de INFYN" como firma.
INFYN tiene prestigio ante clientes de consultoría, no ante dueñas de salón; el aval
suma al portfolio pero no vende el producto.

**Por qué "Clara":** es literal la palabra que usó el mercado al describir su problema
("a fin de mes no tenemos **claridad**"). Es cálido para un rubro mayoritariamente de
dueñas. Y al ser nombre de persona, habilita una asistente con IA ("mandale la foto a
Clara") — un movimiento que una marca-producto como Fresha no puede hacer.

---

## 2. Problema y evidencia

**Evidencia de mercado** (salones relevados por Sofia, 2026-08):

- Ya **pagan** suscripción de Fresha o Calendly para turnos → existe presupuesto y hábito de pagar software.
- Llevan los turnos en un Excel y la parte contable en **otro** Excel.
- *"A fin de mes no tienen claridad ni centralización de datos."* ← palabras del mercado.

**El tell que define el producto:** siguen usando Excel para lo contable **aunque ya
pagan Fresha**. Si el software que pagan les resolviera la plata, ese Excel no
existiría. No lo resuelve, porque la realidad de un salón argentino es efectivo,
propinas, comisión por colaboradora, alquiler de sillón, retiros del dueño — nada de
eso lo modela un producto pensado en inglés.

**El competidor real no es Fresha: es el Excel y la falta de claridad a fin de mes.**

**Momento de entrada:** Fresha eliminó su plan gratuito a principios de 2025. Hay
salones recién forzados a pagar por primera vez, mirando alternativas.

**Ángulos de ataque verificados (2026-08-10):**

| Fresha Argentina | Precio |
|---|---|
| Plan Independiente | 8.000 ARS/mes |
| Plan Equipo | 5.300 ARS/mes **por miembro** |
| Add-on Insights (reportes) | 4.500 ARS/mes **por miembro** ⚠️ |
| Comisión cliente nuevo del marketplace | 20% (mín. USD 6) |
| Procesamiento de tarjeta | 2,19%–3,30% + fijo |

Los reportes se cobran **por cabeza**: un salón de 5 paga 22.500 ARS/mes solo para ver
sus números. Ese es el mensaje de venta más fuerte que tiene Clara.

**Lo que todavía NO está validado:** nadie pidió comprar Clara. La ronda de demos
(ver §10) es prerrequisito comercial, no del desarrollo.

---

## 3. Precio

| Concepto | Precio (ARS/mes) |
|---|---|
| **Promo fundador** (primeros 5 salones) | **14.900**, congelado 6 meses |
| Lista — salón chico (1-3 colaboradoras) | 22.900 |
| Lista — salón (4+ colaboradoras) | 34.900 |
| Prueba | 30 días gratis, sin tarjeta |

Dos escalones planos, no por colaboradora: simple de explicar, simple de facturar a
mano, y no castiga al salón grande (que es el mejor cliente). Reportes incluidos
siempre — es el contraste directo con Fresha.

**Referencia de mercado:** NutriPass (SaaS vertical para nutricionistas argentinos)
cobra 24.499 ARS promo → 34.999 lista, plan único, 60 días gratis.

### Ajuste por inflación (regla comercial)

1. Precio de lista se revisa **cada 3 meses**, atado a la variación del IPC (INDEC).
2. Clientes en promo fundador: **congelado 6 meses**, sin excepción. Se comunica como
   beneficio de venta, no se esconde.
3. Cualquier ajuste se avisa con **30 días de anticipación**.
4. Nunca se ajusta retroactivamente.

---

## 4. Alcance de la v1

**Adentro — el circuito mínimo completo:**

```
turno → atención → cobro (corte) → caja → cierre de mes
```

| Módulo | Qué incluye |
|---|---|
| **Agenda** | Vista diaria/semanal, crear y editar turnos, estados, walk-ins |
| **Caja / Cortes** | Registrar el cobro de cada servicio: total, propina, medio de pago |
| **Gastos** | Registro con categoría, proveedor, medio de pago |
| **Cierre de mes** | Facturación, propinas, ticket promedio, ranking por colaboradora, comisiones, gastos, resultado — **y evolución en términos reales** (§6) |
| **Import por foto (IA)** | Foto de la planilla de papel → filas de corte precargadas para revisar y confirmar |
| **Config** | Colaboradoras, servicios, estaciones, horarios, bloqueos, categorías de gasto, medios de pago |
| **Auth + roles** | Dueño y recepción |

**Afuera (v2 o después), y por qué:**

- **Reservas online públicas + web pública del salón** (`/[slug]`) → es lo que Fresha ya hace bien; entrar por ahí es pelear en el terreno del rival. Cuando esté, el salón puede cancelar Fresha y Clara captura el gasto completo.
- **Clientes derivados de cortes, retención, cashflow caja/banco** → analítica fina, no es el dolor de entrada.
- **Billing automático (MercadoPago)** → etapa 2. En v1 el alta y el cobro son manuales.
- **Landing de venta de INFYN** → etapa 3.
- **Auto-registro público** → llega con el billing. Menos superficie que asegurar ahora.

---

## 5. Arquitectura

**Stack:** Next.js 16 (App Router) + React 19 + TypeScript · Supabase (Auth + Postgres
+ RLS) · Tailwind v4 + shadcn/@base-ui · Vercel, team INFYN (`infyn-s-projects`).

Variante A del stack de Sofia (Supabase directo, sin ORM): el modelo de datos es CRUD
con relaciones claras, no necesita Prisma.

### Multi-tenancy: base única + RLS

Una sola base. Tabla `salones` donde cada fila es un negocio suscripto. **Todas** las
tablas de negocio llevan `salon_id`. Encima, políticas de Row Level Security de
Postgres que garantizan **a nivel de base** que un salón no puede leer ni escribir
filas de otro — aunque haya un bug en el código de la app.

El `salon_id` se resuelve **desde el perfil del usuario logueado**, nunca desde la URL.
Un usuario *pertenece* a un salón; no lo elige.

*Descartado:* base o schema por salón. Aislamiento físico total pero migraciones ×N y
provisioning por alta. No se justifica a esta escala.

### Estructura del repo (feature-first)

```
src/
  app/
    (auth)/login/
    app/                    → panel: agenda, caja, gastos, cierre, config
    api/                    → endpoints (import IA, etc.)
  features/
    agenda/                 → turnos, slots, disponibilidad
    caja/                   → cortes, gastos
    cierre/                 → agregaciones y reportes
    import-ia/              → foto de planilla → filas
    salon/                  → config: servicios, colaboradoras, estaciones, horarios
    onboarding/             → alta de salón + plantilla semilla
  lib/
    supabase/               → clientes server/browser + helper de tenant
    auth/                   → sesión, roles, guards
    inflacion/              → índice IPC y deflactado
```

Sin barrel files. Constantes compartidas server+client en `src/lib/*-constants.ts`.

---

## 6. Modelo de datos

Todas las tablas de negocio: `salon_id BIGINT NOT NULL REFERENCES salones(id)` + índice
+ política RLS. Se omite abajo por brevedad.

```
salones            id, nombre, slug, timezone, moneda, plan, activo, created_at
perfiles           id (FK auth.users), salon_id, rol('dueño'|'recepcion'), nombre
colaboradoras      id, nombre, rol, foto_url, activa, comision,
                   modelo_retribucion('comision'|'alquiler_sillon'|'sueldo')
estaciones         id, nombre, capacidad                    ← configurable por salón
servicios          id, nombre, categoria, descripcion, precio_desde, precio_hasta,
                   duracion_min, estacion_id, activo, orden
colaboradora_servicios   colaboradora_id, servicio_id
disponibilidad     id, colaboradora_id, dia_semana, hora_inicio, hora_fin
bloqueos           id, colaboradora_id, fecha, hora_inicio, hora_fin, motivo, todo_el_dia
clientes           id, nombre, apellido, telefono, email, notas, alergias,
                   bloqueado, motivo_bloqueo        UNIQUE(salon_id, telefono)
turnos             id, cliente_id, colaboradora_id, servicio_id, fecha,
                   hora_inicio, hora_fin, estado, precio, notas, canal
cortes             id, turno_id?, cliente_id?, colaboradora_id, servicio_id, fecha,
                   total_cobrado, propina, medio_pago, moneda, notas, mes, semana
gastos             id, fecha, categoria, subcategoria, proveedor, descripcion,
                   importe, medio_pago, notas, mes, semana
categorias_gasto   id, nombre, orden                  ← configurable por salón
medios_pago        id, nombre, es_efectivo, orden      ← configurable por salón
```

Tabla **global** (sin `salon_id`, lectura pública, escritura solo service role):

```
indices_inflacion  mes (YYYY-MM, PK), indice numeric, fuente
```

### 🔑 La decisión de modelo más importante: `cortes.turno_id`

En el sistema actual de Maru Nails, `cortes` y `turnos` son **dos mundos
desconectados**: `cortes.staff` y `cortes.servicio` son texto libre, sin foreign key,
sin ninguna relación con la tabla `turnos`. El sistema que Clara copia **tiene adentro
exactamente el problema de fragmentación que Clara promete resolver.**

En Clara: el turno se marca como atendido y de ahí se genera el corte, ya con
`colaboradora_id` y `servicio_id` como FK reales. Una sola carga, dos vistas. Eso
**es** el producto, no una optimización.

`turno_id`, `cliente_id` quedan nullables para soportar walk-ins y el import por foto,
donde no hay turno previo.

### Reportes en términos reales

`indices_inflacion` guarda el IPC mensual del INDEC. El cierre de mes muestra dos
series: **nominal** y **deflactada a pesos del mes actual**.

Sin esto, un dueño argentino ve "facturé 8% más que el mes pasado" cuando en realidad
perdió poder de compra. Es una feature chica, de alto impacto, y prácticamente
imposible de encontrar en un producto traducido del inglés.

Carga del índice: manual/script al principio (12 filas por año, costo cero). Si falta
el índice de un mes, la vista real se oculta con un aviso — nunca se inventa un número.

---

## 7. Roles y permisos

| | Dueño | Recepción |
|---|---|---|
| Agenda: ver, crear, editar turnos | ✅ | ✅ |
| Registrar cortes | ✅ | ✅ |
| Registrar gastos | ✅ | ❌ |
| Cierre de mes, comisiones, resultado | ✅ | ❌ |
| Config (servicios, precios, colaboradoras, estaciones) | ✅ | ❌ |
| Gestión de usuarios | ✅ | ❌ |

Se aplica en dos capas: guard en la UI/server actions **y** políticas RLS por rol. La
UI sola no es control de acceso.

Las colaboradoras **no** inician sesión en v1: son entidades que se agendan. El modelo
de datos queda listo para darles acceso después sin migración.

---

## 8. Mejoras respecto del sistema actual

Lo que se corrige al reconstruir (no es refactor gratuito: cada punto es un bloqueante
para vender a terceros):

| # | Hoy en Maru Nails | En Clara |
|---|---|---|
| 1 | 🔴 `SUPABASE_KEY` y `ADMIN_PASSWORD` hardcodeados y commiteados en GitHub | Variables de entorno; anon key solo para lectura pública; service role solo en escrituras que lo requieran |
| 2 | 🔴 Un único password global compartido en cookie de Flask | Supabase Auth, usuarios reales, roles, sesiones |
| 3 | 🔴 Sin noción de salón: single-tenant total | `salon_id` + RLS en toda la base |
| 4 | `cortes` y `turnos` desconectados (staff/servicio como texto libre) | `cortes.turno_id` + FKs reales — **el circuito** |
| 5 | Servicios duplicados: lista `SERVICIOS` en Python para cortes + tabla `servicios` para reservas | Una sola tabla `servicios`, fuente única |
| 6 | `CAPACIDAD_ESTACIONES` y el mapa categoría→estación hardcodeados en Python | Tabla `estaciones` configurable, `servicios.estacion_id` |
| 7 | Moneda MXN y `TC_USD = 17` hardcodeados | Moneda y timezone por salón |
| 8 | Lista `STAFF` con comisiones en código | Tabla `colaboradoras` + `modelo_retribucion` (incluye alquiler de sillón) |
| 9 | Motor de slots: 140 líneas dentro de `api_slots`, no testeable | Módulo aislado en `features/agenda`, con tests |
| 10 | Reportes en pesos nominales | Nominal + deflactado por IPC |

**El motor de slots se porta con la misma lógica** (disponibilidad semanal + bloqueos +
capacidad de estaciones + servicios encadenados en secuencia). Es lo más valioso y
delicado del sistema actual y funciona. Se parametriza por salón, no se reinventa.

---

## 9. Errores, bordes y testing

**Manejo de errores:**
- Toda escritura devuelve resultado explícito; nada de `except: pass` silencioso (patrón presente hoy en `/salon`).
- Import por foto: la IA **propone**, el usuario **confirma**. Nunca inserta sin revisión. Si el JSON no parsea, se muestra el error y la foto, no se descarta la carga.
- Falta el índice IPC del mes → se oculta la vista real con aviso. Jamás se estima.
- Turno solapado o estación sin capacidad → se rechaza con el motivo concreto.

**Bordes conocidos a cubrir con tests:**
- Aislamiento entre tenants: un usuario del salón A **no** puede leer/escribir nada del salón B (test de RLS, es el test más importante del sistema).
- Recepción no accede a cierre de mes ni a gastos.
- Slots: día sin disponibilidad, colaboradora bloqueada, capacidad de estación llena, servicios encadenados que exceden el horario, turno en el pasado.
- Cortes: propina mayor al total, importe cero, moneda distinta.
- Cierre: mes sin datos, mes sin índice IPC.
- Paginación: PostgREST corta en 1000 filas (hoy resuelto con `fetch_all`) — hay que replicar el paginado o agregar por SQL.

**Enfoque:** tests de la lógica pura (slots, agregaciones, deflactado) + tests de
integración de las políticas RLS. La UI se verifica a mano en v1.

---

## 10. Prerrequisito comercial (no bloquea el desarrollo)

Mostrar el sistema de Maru Nails andando a 2-3 dueños argentinos, enfocando en el
cierre de mes y el import por foto. Preguntar cuánto pagan hoy y cuánto pagarían.

Buscar un número o un "avisame cuando esté". Si vuelven tres "está lindo" sin número,
esa señal vale más que un mes de desarrollo.

---

## 11. Preguntas abiertas

1. **Dominio:** ¿`clara.com.ar` está libre en nic.ar? (Vercel no maneja `.ar`; respaldo internacional `claragestion.com`, libre a USD 11,25).
2. **Import por foto:** ¿el costo de API por planilla entra en el precio o se limita por plan? A 14.900 ARS/mes con uso intensivo el margen se estrecha.
3. **Alquiler de sillón:** ¿cómo impacta en el cierre de mes? Una colaboradora que alquila no genera comisión sino un ingreso fijo. Hay que definir el cálculo.
4. **Facturación:** ¿Clara emite comprobantes (ARCA) o solo registra? Fuera de v1, pero define el modelo de datos si se agrega después.
5. ¿El caso de estudio mexicano (Maru, en MXN) genera fricción vendiendo en Argentina?

---

## 12. Criterios de éxito de la v1

1. Un segundo salón real, distinto de Maru Nails, operando en Clara todos los días.
2. Ese salón carga sus turnos y sus cobros en Clara y **deja de usar el Excel de la plata**.
3. El cierre de mes se genera solo, con la vista en términos reales.
4. Test de aislamiento entre tenants en verde.
5. Cero credenciales en el repo.

---

## 13. Etapas

| Etapa | Qué |
|---|---|
| **1 (este spec)** | Producto multi-tenant v1. Alta y cobro manuales |
| **2** | Billing automático con MercadoPago + auto-registro + gating por suscripción |
| **3** | Landing de venta de INFYN (referencia: nutripass.net) |
| **4** | v2 del producto: reservas online + web pública por salón |
