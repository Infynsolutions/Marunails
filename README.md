# 👁 Argos MVP — Dashboard Inteligente para PyMEs

## Arquitectura

```
Google Sheets → FastAPI (Python) → Supabase (PostgreSQL) → React + Recharts
                     ↕                                          ↕
               Claude API (IA)                          Tailwind CSS
```

## Requisitos

- Python 3.11+
- Node.js 20+
- Cuenta Supabase (plan gratuito)
- API Key de Anthropic
- Google Cloud Project con Sheets API habilitada

## Setup Rápido

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Completar con tus keys
uvicorn app.main:app --reload --port 8000
```

### 2. Base de Datos (Supabase)

```bash
# Ejecutar el SQL de scripts/supabase_schema.sql en el SQL Editor de Supabase
# Luego correr el seed de datos de prueba:
python scripts/seed_demo_data.py
```

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env      # Completar con URL del backend
npm run dev               # Puerto 5173
```

### 4. Google Sheets Template

Copiar la plantilla de `templates/argos_template.md` y crear un Google Sheet
con esa estructura. Compartir con la service account.

## Endpoints API (v1)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/dashboard/{tenant_id}` | KPIs + métricas del dashboard |
| GET | `/api/v1/transactions/{tenant_id}` | Últimas transacciones |
| POST | `/api/v1/chat/{tenant_id}` | Chat con Argos (Claude API) |
| POST | `/api/v1/sync/{tenant_id}` | Sincronizar datos desde Google Sheets |
| GET | `/api/v1/alerts/{tenant_id}` | Alertas activas |

## Variables de Entorno

Ver `backend/.env.example` y `frontend/.env.example`
