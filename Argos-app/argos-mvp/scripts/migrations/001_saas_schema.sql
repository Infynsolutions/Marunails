-- ============================================================
-- Argos SaaS — Migration 001: Multi-tenant auth + RLS
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor)
-- ============================================================

-- ── 1. New tables ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS user_tenants (
    user_id   UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id)    ON DELETE CASCADE,
    role      TEXT NOT NULL DEFAULT 'owner' CHECK (role IN ('owner', 'employee')),
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, tenant_id)
);

CREATE TABLE IF NOT EXISTS tenant_usage (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    month        DATE NOT NULL,
    tokens_used  INTEGER NOT NULL DEFAULT 0,
    alert_sent   BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (tenant_id, month)
);

-- ── 2. Alter tenants table ─────────────────────────────────

ALTER TABLE tenants
    ADD COLUMN IF NOT EXISTS subscription_tier    TEXT NOT NULL DEFAULT 'basic'
        CHECK (subscription_tier IN ('basic', 'pro')),
    ADD COLUMN IF NOT EXISTS stripe_customer_id   TEXT,
    ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT;

-- ── 3. RLS helper function ─────────────────────────────────

CREATE OR REPLACE FUNCTION get_my_tenant_id()
RETURNS UUID LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid() LIMIT 1;
$$;

-- ── 4. Token usage RPC (called from chat.py) ───────────────

CREATE OR REPLACE FUNCTION increment_token_usage(
    p_tenant_id UUID,
    p_month     DATE,
    p_tokens    INTEGER
)
RETURNS INTEGER LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    v_total INTEGER;
BEGIN
    INSERT INTO tenant_usage (tenant_id, month, tokens_used)
    VALUES (p_tenant_id, p_month, p_tokens)
    ON CONFLICT (tenant_id, month)
    DO UPDATE SET tokens_used = tenant_usage.tokens_used + EXCLUDED.tokens_used
    RETURNING tokens_used INTO v_total;
    RETURN v_total;
END;
$$;

-- ── 5. Enable RLS on all tables ────────────────────────────

ALTER TABLE transactions      ENABLE ROW LEVEL SECURITY;
ALTER TABLE products          ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_movements   ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts            ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_log          ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages     ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants           ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_usage      ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tenants      ENABLE ROW LEVEL SECURITY;

-- ── 6. RLS policies ────────────────────────────────────────

-- transactions
CREATE POLICY "tenant_isolation" ON transactions
    USING (tenant_id = get_my_tenant_id());

-- products
CREATE POLICY "tenant_isolation" ON products
    USING (tenant_id = get_my_tenant_id());

-- stock_movements
CREATE POLICY "tenant_isolation" ON stock_movements
    USING (tenant_id = get_my_tenant_id());

-- alerts
CREATE POLICY "tenant_isolation" ON alerts
    USING (tenant_id = get_my_tenant_id());

-- sync_log
CREATE POLICY "tenant_isolation" ON sync_log
    USING (tenant_id = get_my_tenant_id());

-- chat_messages
CREATE POLICY "tenant_isolation" ON chat_messages
    USING (tenant_id = get_my_tenant_id());

-- tenant_usage
CREATE POLICY "tenant_isolation" ON tenant_usage
    USING (tenant_id = get_my_tenant_id());

-- tenants: any member can select; only owner can update
CREATE POLICY "tenant_select" ON tenants
    FOR SELECT USING (id = get_my_tenant_id());

CREATE POLICY "tenant_owner_update" ON tenants
    FOR UPDATE USING (
        id = get_my_tenant_id()
        AND EXISTS (
            SELECT 1 FROM user_tenants
            WHERE user_id = auth.uid() AND tenant_id = tenants.id AND role = 'owner'
        )
    );

-- user_tenants: users see only their own rows
CREATE POLICY "own_rows" ON user_tenants
    FOR SELECT USING (user_id = auth.uid());

-- ── 7. Reset token usage monthly (pg_cron) ─────────────────
-- Requires pg_cron extension. Enable in Supabase: Database → Extensions → pg_cron

-- SELECT cron.schedule(
--     'reset-token-usage',
--     '0 0 1 * *',
--     $$UPDATE tenant_usage SET tokens_used = 0, alert_sent = false
--       WHERE month < date_trunc('month', now())$$
-- );

-- ── 8. product_stock view — recreate as SECURITY INVOKER ───
-- Drop and recreate so it respects the caller's RLS context.

DROP VIEW IF EXISTS product_stock;

CREATE VIEW product_stock
WITH (security_invoker = true)
AS
SELECT
    p.id,
    p.tenant_id,
    p.sku,
    p.name,
    p.unit,
    p.price,
    p.min_threshold,
    p.created_at,
    COALESCE(SUM(
        CASE WHEN sm.movement_type = 'entrada' THEN sm.quantity
             WHEN sm.movement_type = 'salida'  THEN -sm.quantity
             ELSE 0 END
    ), 0)::INTEGER AS current_stock
FROM products p
LEFT JOIN stock_movements sm
    ON sm.product_id = p.id AND sm.tenant_id = p.tenant_id
GROUP BY p.id;
