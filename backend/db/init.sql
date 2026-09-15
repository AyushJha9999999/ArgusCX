-- ArgusCX PostgreSQL Initialization Script
-- Runs once when the Postgres container is first created

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────
--  USERS & AUTH
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    full_name   VARCHAR(255),
    role        VARCHAR(50) NOT NULL DEFAULT 'agent',  -- customer | agent | admin
    hashed_pw   TEXT,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  TICKETS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    assigned_agent  UUID REFERENCES users(id) ON DELETE SET NULL,
    channel         VARCHAR(50) NOT NULL DEFAULT 'web',   -- web | mobile | whatsapp | email | voice | social
    subject         TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'open',  -- open | investigating | resolved | escalated | closed
    priority        VARCHAR(20) NOT NULL DEFAULT 'medium',-- low | medium | high | critical
    category        VARCHAR(100),
    tags            TEXT[],
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- ─────────────────────────────────────────────
--  TICKET MESSAGES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id   UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    sender_id   UUID REFERENCES users(id) ON DELETE SET NULL,
    sender_role VARCHAR(50) NOT NULL DEFAULT 'customer',  -- customer | agent | ai
    content     TEXT NOT NULL,
    media_urls  TEXT[],
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  EVIDENCE (uploaded files / screenshots)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS evidence (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id       UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    file_url        TEXT NOT NULL,
    file_type       VARCHAR(100),
    original_name   VARCHAR(255),
    size_bytes      BIGINT,
    is_ai_generated BOOLEAN,
    exif_data       JSONB DEFAULT '{}',
    fraud_score     FLOAT,
    verdict         VARCHAR(50),  -- authentic | suspicious | manipulated | ai_generated
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  AGENT RUNS (LangGraph trace log)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id       UUID REFERENCES tickets(id) ON DELETE SET NULL,
    graph_state     JSONB DEFAULT '{}',
    steps           JSONB DEFAULT '[]',
    final_decision  VARCHAR(100),
    confidence      FLOAT,
    duration_ms     INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
--  INDEXES
-- ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_tickets_status    ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_customer  ON tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_ticket   ON messages(ticket_id);
CREATE INDEX IF NOT EXISTS idx_evidence_ticket   ON evidence(ticket_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_ticket ON agent_runs(ticket_id);

-- Seed a default admin user (password: admin123 — CHANGE THIS)
INSERT INTO users (email, full_name, role, hashed_pw)
VALUES (
    'admin@arguscx.ai',
    'ArgusCX Admin',
    'admin',
    crypt('admin123', gen_salt('bf'))
)
ON CONFLICT (email) DO NOTHING;
