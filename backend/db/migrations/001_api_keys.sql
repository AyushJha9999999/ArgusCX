-- Durable API-key storage. Apply this migration without dropping existing tables.
-- The application requires the `tenants` table before this migration is applied.
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    client_id VARCHAR(80) NOT NULL UNIQUE,
    key_prefix VARCHAR(32) NOT NULL,
    secret_hash VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used TIMESTAMP NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    revoked_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_api_keys_tenant_id ON api_keys (tenant_id);
CREATE INDEX IF NOT EXISTS ix_api_keys_prefix ON api_keys (key_prefix);
