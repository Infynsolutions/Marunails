# Argos — Lessons Learned

## Regla · Por qué · Cuándo aplica

---

### Deploy: Vercel CLI vs GitHub auto-deploy

**Regla:** Siempre deployar con `vercel --prod --yes` desde `Argos-app/argos-mvp/`. El auto-deploy de GitHub está desactivado (`commandForIgnoringBuildStep: "exit 1"`).

**Por qué:** El repo de GitHub es monorepo (INFYN + Argos). Si GitHub auto-deploy se activa, Vercel toma la raíz del repo (sitio INFYN) en lugar de `argos-mvp/`, rompiendo el deployment. El CLI sube exactamente el directorio correcto.

**Cuándo aplica:** Cada vez que se haga `git push`. El push solo sube código; el deploy es un paso manual separado.

---

### Vercel: builds + routes vs rewrites para Python + React

**Regla:** Usar el formato `builds` + `routes` (legacy) en `vercel.json` para proyectos que combinan `@vercel/static-build` y `@vercel/python`.

**Por qué:** El formato moderno con `rewrites` no enruta correctamente los métodos POST a funciones Python. El `routes` format con `dest: "/api/index.py"` funciona para todos los métodos HTTP.

**Cuándo aplica:** Cualquier `vercel.json` con funciones Python + assets estáticos.

---

### Vercel static-build: src debe ser el package.json raíz

**Regla:** Para que los archivos estáticos se sirvan en `/` (root URL), el `src` de `@vercel/static-build` debe apuntar al `package.json` del directorio raíz, no a un subdirectorio.

**Por qué:** `@vercel/static-build` sirve archivos en la URL relativa a donde está el `src`. Si `src: "frontend/package.json"`, los archivos quedan en `/frontend/` no en `/`. Con `src: "package.json"` en la raíz y `distDir: "frontend/dist"`, los archivos van a `/`.

**Cuándo aplica:** Al configurar un frontend React en un subdirectorio con Vercel builds.

---

### VITE_API_URL vacío: usar ?? no ||

**Regla:** Para que `VITE_API_URL=""` (string vacío = same-origin) funcione, usar `??` en vez de `||`.

**Por qué:** El operador `||` considera `""` como falsy y usa el fallback. El `??` solo hace fallback en `null`/`undefined`, respetando el string vacío.

**Cuándo aplica:** Siempre que se use una variable de entorno de Vite que pueda ser string vacío intencional.

---

### ANTHROPIC_API_KEY: key válida ≠ crédito disponible

**Regla:** Al diagnosticar errores del chat, testear la key con un llamado real antes de asumir que es inválida.

**Por qué:** Una key puede ser sintácticamente válida pero con saldo $0. El error de Anthropic es `BadRequestError 400 "credit balance is too low"`, no `AuthenticationError 401`.

**Cuándo aplica:** Cuando el chat falla con el mensaje genérico de error.

---

### Vercel rootDirectory: efecto sobre CLI vs GitHub

**Regla:** No setear `rootDirectory` a nivel de proyecto si el CLI deploy corre desde un subdirectorio. El `rootDirectory` se suma al CWD del CLI y rompe el path.

**Por qué:** El proyecto Argos se linkea a `argos-mvp/` con `.vercel/project.json`. Si `rootDirectory: "Argos-app/argos-mvp"` está seteado, el CLI busca `argos-mvp/Argos-app/argos-mvp` que no existe.

**Cuándo aplica:** Al intentar configurar auto-deploy de GitHub en un monorepo donde el CLI y el repo tienen raíces distintas.

---

### SaaS multi-tenant: supabase_service_key bypasea RLS completamente

**Regla:** Usar `supabase_service_key` SOLO para operaciones admin (seed, auth queries, funciones de sistema). Para operaciones de usuario, crear un cliente con `supabase_anon_key` + JWT del usuario — así RLS actúa automáticamente.

**Por qué:** El service key bypasea Row Level Security. Si toda la app usa service key, la única protección es el código Python (una sola capa). Un bug en los filtros `.eq("tenant_id", ...)` expone datos de todos los tenants. Con anon key + JWT, la DB rechaza el query antes de que llegue al código.

**Cuándo aplica:** Al implementar cualquier feature que lee o escribe datos de usuario en Supabase.

---

### SaaS multi-tenant: el orden de implementación importa

**Regla:** Implementar en este orden: Auth → RLS → Billing → Features. No sumar usuarios pagadores sin RLS habilitado.

**Por qué:** Auth sin RLS es una sola capa de protección. RLS sin Auth no sabe quién valida el JWT. Si se invierten o se saltea alguno, se crean ventanas de exposición. Con el primer cliente real en la DB, cualquier bug cross-tenant es un incidente de seguridad.

**Cuándo aplica:** Al planificar el roadmap de productización. No negociable: M1 (Auth + RLS) antes de cualquier usuario pagador.

---

### FastAPI async: no usar singleton global para clientes DB

**Regla:** No usar un `_client: Optional[Client] = None` global en `database.py`. Crear el cliente de Supabase dentro de una función o dependency injection de FastAPI.

**Por qué:** El singleton global no es thread-safe en contextos async. Si dos requests concurrentes llegan mientras `_client is None`, ambas pueden inicializar el cliente al mismo tiempo. Usar `lru_cache` en `get_settings()` es correcto; aplicar el mismo patrón al cliente DB.

**Cuándo aplica:** Al refactorizar `database.py` en el Milestone 1 (auth). El fix es sencillo: mover la creación del cliente a `get_db()` con un lock o usar dependency injection de FastAPI.
