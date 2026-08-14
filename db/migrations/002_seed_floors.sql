-- Polyfloor Floor Seeds
-- Idempotent: uses ON CONFLICT to safely re-run
-- Run after 001_tower_core.sql

BEGIN;

-- Digital Production floor (your primary floor)
INSERT INTO tower.floor_configs (id, display_name, email, org_name, timezone, target_machine, db_schema, template, daily_budget_usd)
VALUES ('production', 'Digital Production', 'production@polyfloor.local', 'production', 'America/Los_Angeles', 'z0r0', 'floor_production', 'digital-production', 0.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tower.roles (floor_id, role_name, model, max_tokens, description)
VALUES
  ('production', 'orchestrator', 'free://best-reasoning', 8192, 'Coordinates content production pipeline and task delegation'),
  ('production', 'writer', 'free://best-fast', 4096, 'Creates written content, scripts, and copy'),
  ('production', 'editor', 'free://best-reasoning', 4096, 'Reviews and edits content for quality and consistency'),
  ('production', 'designer', 'free://best-fast', 4096, 'Creates visual assets and layout designs')
ON CONFLICT (floor_id, role_name) DO NOTHING;

-- Research floor
INSERT INTO tower.floor_configs (id, display_name, email, org_name, timezone, target_machine, db_schema, template, daily_budget_usd)
VALUES ('research', 'Research Lab', 'research@polyfloor.local', 'research', 'America/Los_Angeles', 'z0r0', 'floor_research', 'research', 0.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tower.roles (floor_id, role_name, model, max_tokens, description)
VALUES
  ('research', 'lead', 'free://best-reasoning', 8192, 'Leads research direction, synthesizes findings'),
  ('research', 'analyst', 'free://best-fast', 4096, 'Performs data analysis and fact-checking'),
  ('research', 'writer', 'free://best-fast', 4096, 'Produces research reports and documentation')
ON CONFLICT (floor_id, role_name) DO NOTHING;

-- Development floor
INSERT INTO tower.floor_configs (id, display_name, email, org_name, timezone, target_machine, db_schema, template, daily_budget_usd)
VALUES ('dev', 'Development', 'dev@polyfloor.local', 'dev', 'America/Los_Angeles', 'z0r0', 'floor_dev', 'dev', 0.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tower.roles (floor_id, role_name, model, max_tokens, description)
VALUES
  ('dev', 'architect', 'free://best-reasoning', 8192, 'Designs system architecture and technical decisions'),
  ('dev', 'developer', 'free://best-fast', 4096, 'Writes code, implements features, fixes bugs'),
  ('dev', 'reviewer', 'free://best-reasoning', 4096, 'Reviews code quality and maintainability')
ON CONFLICT (floor_id, role_name) DO NOTHING;

-- Marketing floor
INSERT INTO tower.floor_configs (id, display_name, email, org_name, timezone, target_machine, db_schema, template, daily_budget_usd)
VALUES ('marketing', 'Marketing', 'marketing@polyfloor.local', 'marketing', 'America/Los_Angeles', 'z0r0', 'floor_marketing', 'marketing', 0.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tower.roles (floor_id, role_name, model, max_tokens, description)
VALUES
  ('marketing', 'strategist', 'free://best-reasoning', 8192, 'Plans campaigns and analyzes market trends'),
  ('marketing', 'copywriter', 'free://best-fast', 4096, 'Writes marketing copy and ad text'),
  ('marketing', 'analyst', 'free://best-reasoning', 4096, 'Analyzes campaign performance')
ON CONFLICT (floor_id, role_name) DO NOTHING;

-- Customer Service floor
INSERT INTO tower.floor_configs (id, display_name, email, org_name, timezone, target_machine, db_schema, template, daily_budget_usd)
VALUES ('customer-service', 'Customer Service', 'support@polyfloor.local', 'customer-service', 'America/Los_Angeles', 'z0r0', 'floor_customer_service', 'customer-service', 0.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO tower.roles (floor_id, role_name, model, max_tokens, description)
VALUES
  ('customer-service', 'manager', 'free://best-reasoning', 8192, 'Manages support team and handles escalations'),
  ('customer-service', 'agent', 'free://best-fast', 4096, 'Handles customer tickets and provides responses'),
  ('customer-service', 'analyst', 'free://best-fast', 4096, 'Analyzes support metrics and trends')
ON CONFLICT (floor_id, role_name) DO NOTHING;

COMMIT;
