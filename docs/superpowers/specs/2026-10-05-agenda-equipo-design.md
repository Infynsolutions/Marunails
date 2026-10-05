# Agenda del equipo — diseño

Fecha: 2026-10-05 · Rama: `feat/agenda-equipo` · Reemplaza el calendario de Fresha.

## Objetivo

Que las chicas del local entren con su propio usuario, vean la agenda de todas
(Día / 3 días / Semana, como Fresha), carguen citas a mano y muevan turnos de
horario o de colaboradora.

## Roles

| | Equipo (cada chica) | Admin (Sofia, encargada) |
|---|---|---|
| Login | Nombre + PIN de 4 dígitos | Contraseña `ADMIN_PASSWORD` |
| Sesión | 30 días (su celular) | Hasta cerrar el navegador |
| Agenda: ver, crear, mover, editar | Sí | Sí |
| Cambiar estado (cancelar, no-show) | Sí | Sí |
| Historial de clienta | Sí | Sí |
| Monto de cada turno | Sí | Sí |
| Total facturado del día | No | Sí |
| Devolver seña | No | Sí |
| Resto del sistema (`/sistema`, cashflow, comisiones, reportes, admin…) | No (redirige a `/agenda`) | Sí |

## Datos — migración `005_agenda_equipo.sql`

- `equipo_acceso (colaboradora_id PK, pin_hash, intentos_fallidos, bloqueado_hasta, updated_at)`.
  RLS activo sin políticas → solo se lee con la service key. Va en tabla aparte
  porque `colaboradoras` se lee con la key anon y `/api/colaboradoras` es pública.
- `turno_cambios (turno_id, autor, autor_colaboradora_id, accion, detalle, antes, despues, created_at)`.
  RLS activo sin políticas. Registra creación, movimientos, ediciones y cambios de estado.
- No agrega columnas a `turnos`: deployar antes de correr la migración no rompe
  nada (el login del equipo no anda y el registro de cambios se omite).

## Acceso

- PIN: lo carga la admin en `/admin` → Equipo → "PIN". Hash con werkzeug.
  5 intentos fallidos → bloqueo de 15 min.
- Quitar el acceso (o desactivar a la colaboradora) borra la fila de
  `equipo_acceso` y la sesión de esa chica deja de valer en el próximo request.
- `require_equipo` (admin o equipo) protege la agenda y sus APIs.
  `require_admin` manda al equipo a `/agenda` (páginas) o responde 403 (APIs).
- Cookie de sesión `SameSite=Lax`.

## Calendario (`/agenda`)

- Barra: `Hoy` `‹ fecha ›` `[Día | 3 días | Semana | Mes]` `Todas / Solo yo`
  `+ Nueva cita` `+ Walk-in`.
- **Día**: EventCalendar (`@event-calendar/build@5.16.0`, MIT, CDN)
  `resourceTimeGridDay`. Una columna por colaboradora activa, 8:00–21:00,
  línea de hora actual, turnos lado a lado si se pisan. Color por categoría de
  servicio (Manicure rosa, Pedicure celeste, Brows & Lashes amarillo, Glow Up
  Facial durazno, Additional verde). Arrastrar = mover (paso de 5 min; en
  táctil, mantener apretado). Clic en hueco = nueva cita con chica y fecha
  precargadas.
- **3 días / Semana**: tabla chicas × días con chips "hora · clienta". Clic en
  chip = detalle; clic en celda vacía = nueva cita; arrastrar chip a otra celda
  (escritorio) = mover manteniendo la hora.
- **Mes**: queda como estaba.
- Cancelados y reprogramados ocultos por defecto (interruptor "Ver cancelados").
- Refresco automático cada 60 s si no hay un modal abierto.

## Mover / editar

- `PUT /api/turno/<id>` `{fecha, hora_inicio, colaboradora_id, servicio_id?, notas?, mover_grupo, forzar}`.
- Duración: se conserva; si cambia el servicio, toma la duración y el precio del nuevo.
- **Cita de varios servicios**: los turnos encadenados (misma clienta, día y
  chica, uno empieza donde termina el otro) se mueven juntos si `mover_grupo`.
- **Choques** (otra cita de esa chica, estación llena, fuera de su horario o
  día bloqueado): responde 409 con la lista; la UI pregunta "¿Mover igual?" y
  reenvía con `forzar`.
- Cada movimiento confirma en un panel ("Mover a Sorimar a 13:30 con FANNY",
  casilla "Mover toda la cita") y al terminar ofrece "Avisar a la clienta"
  (WhatsApp con el nuevo horario).
- El detalle del turno muestra los últimos cambios ("FANNY · movió de 12:50 GABY a 13:30 FANNY").

## Fuera de alcance

Recordatorios automáticos, bloqueos/descansos cargados por las chicas,
asignación de mesa específica, citas fuera de la grilla de 30 min al crear
(se crean en un horario libre y después se arrastran).

## Verificación

- Tests de las funciones puras (cadena de turnos, choques) con pytest.
- Prueba manual local de solo lectura contra la base real (login, vistas).
- Mover/crear se prueba en el preview de Vercel con un turno de prueba.
