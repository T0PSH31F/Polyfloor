-- Polyfloor Tower Core Schema
-- Idempotent migration — safe to re-run
-- Requires: PostgreSQL 15+

BEGIN;

-- Schema for tower-level tables
CREATE SCHEMA IF NOT EXISTS tower;

-- Floor configurations (hot-editable by HR/admin agents)
CREATE TABLE IF NOT EXISTS tower.floor_configs (
    id              TEXT PRIMARY KEY,
    display_name    TEXT NOT NULL,
    email           TEXT,
    org_name        TEXT NOT NULL,
    timezone        TEXT NOT NULL DEFAULT 'America/Los_Angeles',
    target_machine  TEXT,
    db_schema       TEXT NOT NULL,
    mcps            JSONB NOT NULL DEFAULT '[]',
    template        TEXT,
    paid_models_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    daily_budget_usd    NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    persist_paths   JSONB NOT NULL DEFAULT '["outputs","sessions","sprint-board"]',
    config_json     JSONB NOT NULL DEFAULT '{}',
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by      TEXT
);

-- Per-floor role configurations
CREATE TABLE IF NOT EXISTS tower.roles (
    id          SERIAL PRIMARY KEY,
    floor_id    TEXT NOT NULL REFERENCES tower.floor_configs(id) ON DELETE CASCADE,
    role_name   TEXT NOT NULL,
    enable      BOOLEAN NOT NULL DEFAULT TRUE,
    model       TEXT NOT NULL DEFAULT 'free://best-reasoning',
    max_tokens  INTEGER NOT NULL DEFAULT 8192,
    description TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(floor_id, role_name)
);

-- Append-only audit/event log
CREATE TABLE IF NOT EXISTS tower.events (
    id          BIGSERIAL PRIMARY KEY,
    floor_id    TEXT,
    event_type  TEXT NOT NULL,
    actor       TEXT NOT NULL,
    payload     JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Prevent updates/deletes on events (append-only)
CREATE OR REPLACE FUNCTION tower.events_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'tower.events is append-only; updates and deletes are prohibited';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS events_no_update ON tower.events;
CREATE TRIGGER events_no_update
    BEFORE UPDATE OR DELETE ON tower.events
    FOR EACH ROW EXECUTE FUNCTION tower.events_immutable();

-- Sprints
CREATE TABLE IF NOT EXISTS tower.sprints (
    id          SERIAL PRIMARY KEY,
    floor_id    TEXT NOT NULL REFERENCES tower.floor_configs(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    goal        TEXT,
    status      TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('planning', 'active', 'completed', 'cancelled')),
    start_date  TIMESTAMPTZ,
    end_date    TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tasks with constrained lifecycle
CREATE TABLE IF NOT EXISTS tower.tasks (
    id          SERIAL PRIMARY KEY,
    floor_id    TEXT NOT NULL REFERENCES tower.floor_configs(id) ON DELETE CASCADE,
    sprint_id   INTEGER REFERENCES tower.sprints(id) ON DELETE SET NULL,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'backlog'
        CHECK (status IN ('backlog', 'queued', 'in_progress', 'staging', 'done', 'rejected')),
    assigned_role TEXT,
    priority    INTEGER NOT NULL DEFAULT 0,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_floor_status ON tower.tasks(floor_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_sprint ON tower.tasks(sprint_id);

-- Valid task status transitions
CREATE OR REPLACE FUNCTION tower.validate_task_transition()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status = NEW.status THEN RETURN NEW; END IF;

    -- Allowed transitions
    IF OLD.status = 'backlog'    AND NEW.status IN ('queued') THEN RETURN NEW; END IF;
    IF OLD.status = 'queued'     AND NEW.status IN ('in_progress', 'backlog') THEN RETURN NEW; END IF;
    IF OLD.status = 'in_progress' AND NEW.status IN ('staging', 'rejected', 'queued') THEN RETURN NEW; END IF;
    IF OLD.status = 'staging'    AND NEW.status IN ('done', 'rejected', 'in_progress') THEN RETURN NEW; END IF;
    IF OLD.status = 'rejected'   AND NEW.status IN ('backlog', 'queued') THEN RETURN NEW; END IF;
    IF OLD.status = 'done'       AND NEW.status IN ('backlog') THEN RETURN NEW; END IF;

    RAISE EXCEPTION 'Invalid task status transition: % -> %', OLD.status, NEW.status;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS task_validate_transition ON tower.tasks;
CREATE TRIGGER task_validate_transition
    BEFORE UPDATE OF status ON tower.tasks
    FOR EACH ROW EXECUTE FUNCTION tower.validate_task_transition();

-- Role memory (agent context persistence)
CREATE TABLE IF NOT EXISTS tower.role_memory (
    id          SERIAL PRIMARY KEY,
    floor_id    TEXT NOT NULL REFERENCES tower.floor_configs(id) ON DELETE CASCADE,
    role_name   TEXT NOT NULL,
    key         TEXT NOT NULL,
    value       JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(floor_id, role_name, key)
);

-- Project briefs
CREATE TABLE IF NOT EXISTS tower.project_briefs (
    id          SERIAL PRIMARY KEY,
    floor_id    TEXT NOT NULL REFERENCES tower.floor_configs(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    status      TEXT NOT NULL DEFAULT 'draft'
        CHECK (status IN ('draft', 'active', 'completed', 'archived')),
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Approval queue (human gate for external side effects)
CREATE TABLE IF NOT EXISTS tower.approvals (
    id              SERIAL PRIMARY KEY,
    floor_id        TEXT NOT NULL REFERENCES tower.floor_configs(id) ON DELETE CASCADE,
    task_id         INTEGER REFERENCES tower.tasks(id) ON DELETE SET NULL,
    approval_type   TEXT NOT NULL,
    description     TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_by    TEXT NOT NULL,
    resolved_by     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_approvals_status ON tower.approvals(status) WHERE status = 'pending';

-- Updated_at trigger
CREATE OR REPLACE FUNCTION tower.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at_floor_configs ON tower.floor_configs;
CREATE TRIGGER set_updated_at_floor_configs
    BEFORE UPDATE ON tower.floor_configs
    FOR EACH ROW EXECUTE FUNCTION tower.set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_roles ON tower.roles;
CREATE TRIGGER set_updated_at_roles
    BEFORE UPDATE ON tower.roles
    FOR EACH ROW EXECUTE FUNCTION tower.set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_sprints ON tower.sprints;
CREATE TRIGGER set_updated_at_sprints
    BEFORE UPDATE ON tower.sprints
    FOR EACH ROW EXECUTE FUNCTION tower.set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_tasks ON tower.tasks;
CREATE TRIGGER set_updated_at_tasks
    BEFORE UPDATE ON tower.tasks
    FOR EACH ROW EXECUTE FUNCTION tower.set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_role_memory ON tower.role_memory;
CREATE TRIGGER set_updated_at_role_memory
    BEFORE UPDATE ON tower.role_memory
    FOR EACH ROW EXECUTE FUNCTION tower.set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at_project_briefs ON tower.project_briefs;
CREATE TRIGGER set_updated_at_project_briefs
    BEFORE UPDATE ON tower.project_briefs
    FOR EACH ROW EXECUTE FUNCTION tower.set_updated_at();

COMMIT;
