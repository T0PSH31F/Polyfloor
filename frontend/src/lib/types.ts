/** Polyfloor API types */

export interface FloorConfig {
  id: string;
  display_name: string;
  email: string | null;
  org_name: string;
  timezone: string;
  target_machine: string | null;
  db_schema: string;
  mcps: string[];
  template: string | null;
  paid_models_allowed: boolean;
  daily_budget_usd: number;
  persist_paths: string[];
  config_json: Record<string, unknown>;
  version: number;
}

export interface RoleConfig {
  role_name: string;
  enable: boolean;
  model: string;
  max_tokens: number;
  description: string;
}

export interface Task {
  id: number;
  floor_id: string;
  sprint_id: number | null;
  title: string;
  description: string;
  status: TaskStatus;
  assigned_role: string | null;
  priority: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type TaskStatus =
  | "backlog"
  | "queued"
  | "in_progress"
  | "staging"
  | "done"
  | "rejected";

export interface Approval {
  id: number;
  floor_id: string;
  task_id: number | null;
  approval_type: string;
  description: string;
  payload: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
  requested_by: string;
  resolved_by: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface FloorEvent {
  floor_id: string;
  event_type: string;
  actor: string;
  payload: Record<string, unknown>;
  id?: number;
  created_at?: string;
}

export interface Sprint {
  id: number;
  floor_id: string;
  name: string;
  goal: string | null;
  status: "planning" | "active" | "completed" | "cancelled";
  start_date: string | null;
  end_date: string | null;
}

/** Agent state derived from backend events */
export type AgentState = "idle" | "working" | "alert" | "done";
