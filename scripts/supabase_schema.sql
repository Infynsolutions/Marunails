-- =============================================
-- ARGOS MVP — Supabase Schema
-- Run this in Supabase SQL Editor
-- =============================================

-- ── Enable UUID extension ──
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ══════════════════════════════════════════════
-- TENANTS (empresas clientes)
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'starter' CHECK (plan IN ('starter', 'pro', 'enterprise')),
    currency TEXT NOT NULL DEFAULT 'ARS',
    timezone TEXT NOT NULL DEFAULT 'America/Argentina/Buenos_Aires',
    spreadsheet_ids TEXT[] DEFAULT '{}',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- TRANSACTIONS (movimientos financieros)
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    date TIMESTAMPTZ NOT NULL,
    amount NUMERIC(14,2) NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('ingreso', 'gasto')),
    category TEXT NOT NULL DEFAULT 'Sin clasificar',
    description TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pendiente' CHECK (status IN ('cobrado', 'pagado', 'pendiente')),
    reference TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent duplicate imports
    UNIQUE(tenant_id, date, description)
);

CREATE INDEX IF NOT EXISTS idx_tx_tenant_date ON transactions(tenant_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_tx_tenant_type ON transactions(tenant_id, type);
CREATE INDEX IF NOT EXISTS idx_tx_tenant_status ON transactions(tenant_id, status);

-- ══════════════════════════════════════════════
-- ALERTS
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    severity TEXT NOT NULL DEFAULT 'info' CHECK (severity IN ('critica', 'advertencia', 'info')),
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'activa' CHECK (status IN ('activa', 'resuelta')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alerts(tenant_id, status, created_at DESC);

-- ══════════════════════════════════════════════
-- CHAT MESSAGES
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(tenant_id, session_id, created_at);

-- ══════════════════════════════════════════════
-- SYNC LOG
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS sync_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    rows_processed INTEGER DEFAULT 0,
    rows_new INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    errors TEXT[] DEFAULT '{}',
    completed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sync_tenant ON sync_log(tenant_id, completed_at DESC);

-- ══════════════════════════════════════════════
-- ROW LEVEL SECURITY (multi-tenant isolation)
-- ══════════════════════════════════════════════
-- Note: For the MVP with service_key, RLS is bypassed.
-- Enable these policies when adding user auth:

-- ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE sync_log ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Tenant isolation" ON transactions
--     FOR ALL USING (tenant_id = auth.uid());

-- ══════════════════════════════════════════════
-- HELPER FUNCTION: update updated_at
-- ══════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ══════════════════════════════════════════════
-- PRODUCTS (catálogo por tenant)
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    sku TEXT NOT NULL,
    unit_price NUMERIC(14,2) NOT NULL DEFAULT 0,
    min_threshold INTEGER NOT NULL DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, sku)
);

CREATE INDEX IF NOT EXISTS idx_products_tenant ON products(tenant_id);


-- ══════════════════════════════════════════════
-- STOCK MOVEMENTS
-- ══════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS stock_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('entrada', 'salida', 'venta', 'ajuste')),
    -- entrada/salida/venta: always positive; ajuste: signed (negative = loss)
    quantity INTEGER NOT NULL,
    note TEXT DEFAULT '',
    date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stock_tenant_product ON stock_movements(tenant_id, product_id);
CREATE INDEX IF NOT EXISTS idx_stock_tenant_date ON stock_movements(tenant_id, date DESC);


-- ══════════════════════════════════════════════
-- ADD product_id TO TRANSACTIONS (Sprint 1 migration)
-- ══════════════════════════════════════════════
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS product_id UUID REFERENCES products(id);


-- ══════════════════════════════════════════════
-- VIEW: product_stock (D4 — single aggregating query, no N+1)
-- ══════════════════════════════════════════════
CREATE OR REPLACE VIEW product_stock AS
SELECT
    p.id,
    p.tenant_id,
    p.name,
    p.sku,
    p.unit_price,
    p.min_threshold,
    p.created_at,
    COALESCE(
        SUM(
            CASE
                WHEN sm.type = 'entrada' THEN sm.quantity
                WHEN sm.type IN ('salida', 'venta') THEN -sm.quantity
                WHEN sm.type = 'ajuste' THEN sm.quantity  -- signed: ajuste -2 subtracts
                ELSE 0
            END
        ), 0
    )::INTEGER AS current_stock
FROM products p
LEFT JOIN stock_movements sm ON sm.product_id = p.id AND sm.tenant_id = p.tenant_id
GROUP BY p.id, p.tenant_id, p.name, p.sku, p.unit_price, p.min_threshold, p.created_at;


-- ══════════════════════════════════════════════
-- FUNCTION: create_sale (D2 — atomic Transaction + StockMovement)
-- ══════════════════════════════════════════════
CREATE OR REPLACE FUNCTION create_sale(
    p_tenant_id UUID,
    p_product_id UUID,
    p_quantity INTEGER,
    p_amount NUMERIC(14,2),
    p_category TEXT,
    p_description TEXT,
    p_date TIMESTAMPTZ,
    p_status TEXT DEFAULT 'pendiente',
    p_reference TEXT DEFAULT ''
) RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    v_tx_id UUID;
    v_mv_id UUID;
BEGIN
    INSERT INTO transactions (tenant_id, date, amount, type, category, description, status, reference, product_id)
    VALUES (p_tenant_id, p_date, p_amount, 'ingreso', p_category, p_description, p_status, p_reference, p_product_id)
    RETURNING id INTO v_tx_id;

    INSERT INTO stock_movements (tenant_id, product_id, type, quantity, note, date)
    VALUES (p_tenant_id, p_product_id, 'venta', p_quantity, p_description, p_date)
    RETURNING id INTO v_mv_id;

    RETURN json_build_object('transaction_id', v_tx_id, 'movement_id', v_mv_id);
END;
$$;
