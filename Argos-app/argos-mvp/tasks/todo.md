# Argos MVP — Todo

## Sesión 2026-05-18 ✅ CERRADA

### Completado
- [x] Unificación frontend + backend en un solo proyecto Vercel (`infy-napp`)
- [x] `api/index.py` en raíz de `argos-mvp/` — wrapper que importa FastAPI app desde `backend/`
- [x] `requirements.txt` en raíz para que Vercel instale deps Python
- [x] `vercel.json` unificado: `@vercel/static-build` + `@vercel/python` + routes
- [x] `package.json` raíz para que static build sirva archivos en `/` y no `/frontend/`
- [x] `api.js`: `??` en lugar de `||` para que `VITE_API_URL=""` funcione como same-origin
- [x] ANTHROPIC_API_KEY actualizada en Vercel (key válida, falta crédito)
- [x] GitHub auto-deploy desactivado (`commandForIgnoringBuildStep: "exit 1"`)
- [x] Todo subido a GitHub (`INFYNapp`, rama `main`)

### Pendiente para próxima sesión
- [ ] Cargar crédito en Anthropic (console.anthropic.com → Plans & Billing) → activa el chat
- [ ] Análisis de arquitectura desde el POV del emprendedor (UX, funcionalidades faltantes, CRUD)
- [ ] Configurar GitHub Actions para deploy automático correcto (opcional)

## Review
- Deployment unificado funciona: frontend 200, API OK, dashboard carga 4 KPIs con datos de La Percha
- El mayor bloqueante fue el GitHub auto-deploy que pisaba el deploy correcto
- La key de Anthropic tiene saldo $0 — único pendiente para que el chat funcione

---

# Productización SaaS — Plan de implementación

## Decisiones de arquitectura (aprobadas 2026-05-18)
- **D1**: RLS + anon/JWT key — Row Level Security en todas las tablas + migrar a anon key para operaciones de usuario
- **D2**: RLS antes del primer cliente pagador — no hacer soft launch sin protección de DB
- **Tiers**: Basic $12/mes (1 usuario, entrada manual, AI ilimitada), Pro $35/mes (multi-usuario, OCR, agentes proactivos)
- **Auth**: Supabase Auth (email/password) — JWT validado por FastAPI con `supabase_jwt_secret` (ya en config)
- **Billing**: Stripe — webhooks actualizan `tenants.subscription_tier`, FastAPI lee desde su propia DB
- **Token budget**: `tenant_usage` table, alert 80k tokens/mes, hard limit 120k/mes
- **Employee AI**: system prompt diferenciado — owner ve todo; empleado ve stock + ventas del día, sin márgenes ni P&L
- **OCR**: Claude Vision — imagen de factura → campos pre-completados en formulario
- **Agentes proactivos**: Supabase pg_cron + Edge Functions (no Vercel serverless — límite 300s insuficiente)

---

## Milestone 1 — Auth + Multi-tenant (BLOQUEANTE para todo lo demás)

### Schema changes (Supabase)
- [ ] Crear tabla `user_tenants` (`user_id UUID references auth.users`, `tenant_id UUID references tenants`, `role TEXT CHECK(role IN ('owner','employee'))`, PK compuesta)
- [ ] Agregar campo `subscription_tier TEXT DEFAULT 'basic' CHECK(tier IN ('basic','pro'))` a tabla `tenants`
- [ ] Agregar campo `stripe_customer_id TEXT` a tabla `tenants`
- [ ] Agregar campo `stripe_subscription_id TEXT` a tabla `tenants`
- [ ] Crear tabla `tenant_usage` (`id`, `tenant_id`, `month DATE`, `tokens_used INTEGER DEFAULT 0`, `alert_sent BOOLEAN DEFAULT false`, UNIQUE(tenant_id, month))

### RLS policies (8 tablas)
- [ ] Habilitar RLS en: `transactions`, `products`, `stock_movements`, `alerts`, `sync_log`, `chat_messages`, `tenants`, `tenant_usage`
- [ ] Política base para cada tabla: `USING (tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid()))`
- [ ] Política especial `tenants`: owner puede UPDATE; employee solo SELECT
- [ ] Política `chat_messages`: filtrar también por `session_id` perteneciente al usuario
- [ ] Función helper `get_my_tenant_id()` → `SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid() LIMIT 1`
- [ ] Crear view `product_stock` con SECURITY DEFINER o actualizar para respetar RLS

### FastAPI — JWT middleware
- [ ] Crear `backend/app/api/auth.py` con dependency `get_current_user(token: str = Depends(oauth2_scheme))`
- [ ] Validar JWT con `supabase_jwt_secret` (ya en `config.py`) usando `python-jose`
- [ ] Agregar `python-jose[cryptography]` a `requirements.txt`
- [ ] Extraer `user_id` del claim `sub` del JWT
- [ ] Crear dependency `get_current_tenant(user_id) → tenant_id` — query a `user_tenants` con service key (solo para auth queries)
- [ ] Inyectar ambas dependencies en todos los endpoints de `routes.py`
- [ ] ELIMINAR validación manual `db.get_tenant(tenant_id)` de cada endpoint — reemplazar por el middleware
- [ ] Mantener service key SOLO para: auth queries, seed scripts, funciones admin

### FastAPI — migrar a anon key para operaciones de datos
- [ ] Agregar `supabase_anon_key: str = ""` a `config.py`
- [ ] Crear función `get_user_db(jwt_token: str) → Client` que usa anon key + pasa JWT como Authorization header
- [ ] Todas las queries de datos van por `get_user_db()` — RLS actúa automáticamente
- [ ] Auth queries (resolver tenant_id desde user_id) van por service key

### Frontend — auth
- [ ] Instalar `@supabase/supabase-js` en el frontend
- [ ] Crear `frontend/src/lib/supabase.js` con client usando `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`
- [ ] Crear `frontend/src/pages/Login.jsx` — email/password form → `supabase.auth.signInWithPassword()`
- [ ] Crear `frontend/src/pages/Register.jsx` — wizard paso 1 (nombre empresa → crea tenant) + paso 2 (plan) + paso 3 (Stripe)
- [ ] Crear `frontend/src/lib/auth.js` — hook `useAuth()` que expone `user`, `session`, `tenant_id`, `role`
- [ ] Reemplazar `TENANT_ID` hardcodeado en `api.js` por `useAuth().tenant_id`
- [ ] Agregar `Authorization: Bearer ${session.access_token}` header a todos los requests en `api.js`
- [ ] Auth guards en React Router: todas las rutas requieren sesión válida
- [ ] Redirigir a `/login` si no hay sesión

---

## Milestone 2 — Billing (Stripe)

### Stripe setup
- [ ] Crear cuenta Stripe (o usar existente)
- [ ] Crear productos: "Argos Basic" ($12/mes) y "Argos Pro" ($35/mes)
- [ ] Guardar `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET` en variables de entorno
- [ ] Agregar `stripe` a `requirements.txt`

### FastAPI — endpoints Stripe
- [ ] `POST /api/v1/billing/checkout/{tenant_id}` → crea Stripe Checkout Session, retorna URL
- [ ] `POST /api/v1/billing/webhook` → recibe eventos de Stripe (sin auth JWT — usa webhook secret)
- [ ] Webhook handler: `customer.subscription.created` → actualizar `tenants.subscription_tier`
- [ ] Webhook handler: `customer.subscription.updated` → actualizar tier (upgrade/downgrade)
- [ ] Webhook handler: `customer.subscription.deleted` → downgrade a 'basic'
- [ ] `GET /api/v1/billing/portal/{tenant_id}` → Stripe Customer Portal URL (manage subscription)

### FastAPI — feature gating
- [ ] Crear dependency `require_pro(tenant)` → HTTP 403 si `tenant.subscription_tier != 'pro'`
- [ ] Aplicar a: `/scan-invoice`, `/employees`, agentes proactivos, `/stock-movement` (bulk)

### Frontend — billing
- [ ] Página `/settings/billing` → muestra plan actual, botón "Upgrade" o "Manage Subscription"
- [ ] Botón Upgrade → llama a `/billing/checkout` → redirige a Stripe Checkout
- [ ] Post-checkout redirect → `/dashboard?upgraded=true` con banner de bienvenida Pro
- [ ] Bloquear features Pro en UI con lock icon + CTA "Actualizar a Pro"

---

## Milestone 3 — Token tracking

### Schema
- [ ] `tenant_usage` ya creada en Milestone 1

### FastAPI — tracking en chat
- [ ] En `chat.py`, después de cada respuesta de Claude: extraer `response.usage.input_tokens + output_tokens`
- [ ] Upsert en `tenant_usage`: `INSERT ... ON CONFLICT (tenant_id, month) DO UPDATE SET tokens_used = tokens_used + ?`
- [ ] Antes de llamar a Claude: verificar `tokens_used` actual vs límites
- [ ] Si `tokens_used >= ALERT_THRESHOLD` (80k) y `alert_sent = false`: enviar email via Resend + marcar `alert_sent = true`
- [ ] Si `tokens_used >= HARD_LIMIT` (120k): retornar 429 con mensaje claro en español
- [ ] Agregar `ALERT_TOKEN_THRESHOLD: int = 80000` y `HARD_TOKEN_LIMIT: int = 120000` a `config.py`
- [ ] Agregar `resend_api_key: str = ""` a `config.py`

### pg_cron — reset mensual
- [ ] SQL: `SELECT cron.schedule('reset-token-usage', '0 0 1 * *', 'UPDATE tenant_usage SET tokens_used = 0, alert_sent = false WHERE month < date_trunc(''month'', now())')`

---

## Milestone 4 — Empleados (Pro tier)

### Invitación
- [ ] `POST /api/v1/employees/{tenant_id}` → `supabase.auth.admin.invite_user_by_email()` + insertar en `user_tenants` con `role='employee'`
- [ ] `GET /api/v1/employees/{tenant_id}` → listar empleados del tenant
- [ ] `DELETE /api/v1/employees/{tenant_id}/{user_id}` → eliminar de `user_tenants`
- [ ] Frontend: `/settings/team` → lista empleados, botón "Invitar", formulario email

### AI context diferenciado
- [ ] En `chat.py`, recibir `role` del user (owner/employee)
- [ ] Si `role == 'employee'`: usar `EMPLOYEE_PROMPT_TEMPLATE` → solo stock + ventas del día
- [ ] Si `role == 'owner'`: usar `SYSTEM_PROMPT_TEMPLATE` actual (full context)
- [ ] El endpoint `/chat/{tenant_id}` inyecta el role del usuario autenticado (no recibido del cliente)

---

## Milestone 5 — OCR de facturas (Pro tier)

- [ ] `POST /api/v1/scan-invoice/{tenant_id}` → recibe imagen base64, llama a Claude Vision
- [ ] Prompt para Vision: extraer monto, descripción, fecha, categoría sugerida
- [ ] Retornar JSON con campos pre-completados → frontend los carga en el form de transacción
- [ ] Frontend: botón "Escanear factura" en formulario de gasto → abre cámara/file picker → envía a endpoint
- [ ] Loading state mientras Claude procesa (típicamente 2-3 segundos)
- [ ] Aplicar `require_pro` al endpoint

---

## Milestone 6 — Agentes proactivos (Pro tier)

- [ ] Crear Supabase Edge Function `weekly-summary`: corre lunes 9am ART, genera resumen semanal por tenant Pro, envía por Resend
- [ ] Crear Supabase Edge Function `anomaly-detection`: corre diario, detecta gastos >2x promedio o ingresos 0 por 3 días, crea alerta en DB
- [ ] pg_cron: `SELECT cron.schedule('weekly-summary', '0 12 * * 1', $$SELECT net.http_post(...)$$)`
- [ ] pg_cron: `SELECT cron.schedule('anomaly-detection', '0 9 * * *', $$SELECT net.http_post(...)$$)`
- [ ] Template email resumen semanal: KPIs del período, alertas activas, sugerencia de Argos
- [ ] Aplicar `require_pro` a ambas funciones

---

## Fixes técnicos (no bloqueantes pero importantes)

- [ ] **Thread safety**: reemplazar global `_client` en `database.py` por función que crea cliente por request (o usar `asynccontextmanager`)
- [ ] **Supabase anon key**: agregar `VITE_SUPABASE_ANON_KEY` y `SUPABASE_ANON_KEY` a las variables de entorno de Vercel
- [ ] **Tests de aislamiento**: escribir tests que verifican que un tenant NO puede leer datos de otro (regresar 403 o datos vacíos)
- [ ] **Tests de billing**: verificar que endpoints Pro retornan 403 para usuarios Basic
- [ ] **Tests de auth**: verificar que endpoints sin JWT retornan 401
- [ ] **Migración onboarding**: wizard de registro que crea tenant + `user_tenants` en un solo flujo

---

## Orden de implementación sugerido

```
Semana 1: M1 — Auth + RLS (bloqueante, hacer todo junto)
Semana 2: M2 — Billing Stripe (necesario para cobrar)
           M3 — Token tracking (necesario para controlar costos)
Semana 3: M4 — Empleados (diferencial Pro)
           M5 — OCR (diferencial Pro)
Semana 4: M6 — Agentes proactivos (diferencial Pro premium)
           Fixes técnicos + tests de regresión
```

**Criterio de "listo para primer cliente pagador"**: M1 + M2 completos + al menos token tracking básico (M3 sin cron).
