-- Polyfloor Digital Production Studio Seed
-- Implements the full production workflow with all required roles
-- Run after 001_tower_core.sql

BEGIN;

-- Digital Production Studio floor
INSERT INTO tower.floor_configs (id, display_name, email, org_name, timezone, target_machine, db_schema, template, daily_budget_usd, persist_paths)
VALUES (
  'production',
  'Digital Production Studio',
  'production@polyfloor.local',
  'production',
  'America/Los_Angeles',
  'z0r0',
  'floor_production',
  'digital-production',
  0.00,
  '["outputs", "sessions", "sprint-board", "briefs", "drafts", "assets", "packages"]'
)
ON CONFLICT (id) DO UPDATE SET
  display_name = EXCLUDED.display_name,
  persist_paths = EXCLUDED.persist_paths;

-- All required roles for the Digital Production Studio
INSERT INTO tower.roles (floor_id, role_name, enable, model, max_tokens, description)
VALUES
  -- orchestrator: floor CEO; plans sprint, creates tasks, reviews staging
  ('production', 'orchestrator', true, 'free://best-reasoning', 8192,
   'Floor CEO — plans sprints, creates tasks, reviews staging, coordinates all roles'),

  -- researcher: validates demand, competitors, sources, and citations
  ('production', 'researcher', true, 'free://best-reasoning', 8192,
   'Validates demand, competitors, sources, and citations for content'),

  -- rd: deeper research, outlines, references, feasibility notes
  ('production', 'rd', true, 'free://best-reasoning', 8192,
   'Deep research — outlines, references, feasibility notes, technical validation'),

  -- writer: drafts chapters/sections from outline and references
  ('production', 'writer', true, 'free://best-fast', 4096,
   'Drafts chapters and sections from outlines and reference materials'),

  -- editor: structure, grammar, consistency, humanization, formatting
  ('production', 'editor', true, 'free://best-reasoning', 4096,
   'Reviews structure, grammar, consistency; humanizes and formats content'),

  -- illustrator: image prompts/assets/cover concepts; no external upload
  ('production', 'illustrator', true, 'free://best-fast', 4096,
   'Creates image prompts, asset descriptions, cover concepts (local only, no external upload)'),

  -- marketing: launch plan, product description, social/blog drafts
  ('production', 'marketing', true, 'free://best-fast', 4096,
   'Creates launch plans, product descriptions, social media and blog drafts'),

  -- publishing: prepares publication package and requests human approval
  ('production', 'publishing', true, 'free://best-reasoning', 4096,
   'Prepares publication packages and requests human approval before any external action'),

  -- customer_service: drafts responses and triages inquiries; no external sending
  ('production', 'customer_service', true, 'free://best-fast', 4096,
   'Drafts customer responses and triages inquiries (no external sending by default)')
ON CONFLICT (floor_id, role_name) DO UPDATE SET
  enable = EXCLUDED.enable,
  model = EXCLUDED.model,
  description = EXCLUDED.description;

-- Workflow stages for the Digital Production Studio
-- These are stored as task metadata and enforced by the application layer
-- Stage progression: brief -> research -> outline -> draft -> edit -> assets -> court_review -> staging -> human_approval -> publish_package

-- Example sprint for the production floor
INSERT INTO tower.sprints (floor_id, name, goal, status)
VALUES (
  'production',
  'Sprint 1: Initial Setup',
  'Set up Digital Production Studio workflow and create first content brief',
  'active'
)
ON CONFLICT DO NOTHING;

COMMIT;
