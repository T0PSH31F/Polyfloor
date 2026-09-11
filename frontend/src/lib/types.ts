/**
 * Polyfloor API types — matching the frozen API contract.
 * @see /home/user/workspace/Polyfloor/docs/API_CONTRACT.md
 */

// --- Company ---
export interface CompanyCard {
  id: string;
  name: string;
  slug: string;
  template_id: string;
  goal: string;
  status: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  template_id: string;
  goal: string;
  status: string;
  grilling_intensity: number;
  budget_policy_json: string;
  channels_json: string;
  logo: string | null;
  visual_theme: string;
  created_at: string;
}

// --- Floor ---
export interface Floor {
  id: string;
  company_id: string;
  ordinal: number;
  label: string;
  template_id: string;
  layout_json: string;
  created_at: string;
}

// --- Room ---
export type RoomType = "ceo" | "hr" | "csuite" | "qa" | "team";

export interface Room {
  id: string;
  company_id: string;
  company_floor_id: string;
  room_type: RoomType;
  label: string;
  team_id: string | null;
  wip_limit: number;
  layout_json: string;
  created_at: string;
}

// --- Desk ---
export interface Desk {
  id: string;
  company_id: string;
  room_id: string;
  ordinal: number;
  agent_id: string | null;
}

// --- Team ---
export interface Team {
  id: string;
  company_id: string;
  name: string;
  role_type: string;
  room_id: string;
  lead_agent_id: string;
  policy_json: string;
  created_at: string;
}

// --- Agent ---
export type AgentRole =
  "ceo" | "hr" | "cfo" | "cto" | "coo" | "cho" | "lead" | "worker" | "qa";

export type AgentState = "idle" | "working" | "paused" | "retired";

export interface Agent {
  id: string;
  company_id: string;
  team_id: string | null;
  role: AgentRole;
  name: string;
  model_id: string | null;
  avatar_uri: string;
  state: AgentState;
  home_room_id: string;
  home_desk_id: string;
  avatar_recipe: string;
  token_spend: number;
}

export interface AgentRun {
  id: number;
  agent_id: string;
  company_id: string;
  task_id: number | null;
  status: string;
  started_at: string;
  finished_at: string | null;
  model_id: string | null;
  token_usage: number;
  cost_usd: number;
  trace_id: string | null;
}

export interface AgentDossier {
  agent: Agent;
  runs: AgentRun[];
}

// --- Task ---
export type TaskStatus =
  | "BACKLOG"
  | "READY"
  | "IN_PROGRESS"
  | "REVIEW"
  | "AWAITING_APPROVAL"
  | "DONE"
  | "BLOCKED";

export interface Task {
  id: number;
  company_id: string;
  team_id: string;
  owner_agent_id: string | null;
  parent_task_id: number | null;
  title: string;
  description: string;
  status: TaskStatus;
  priority: number;
  acceptance_criteria_json: string;
  budget_limit: number;
  retry_limit: number;
  trace_id: string | null;
  created_at: string;
  updated_at: string;
}

// --- Approval ---
export interface Approval {
  id: number;
  company_id: string;
  task_id: number | null;
  requested_by: string;
  policy_key: string;
  risk_level: string;
  payload_json: string;
  status: "pending" | "approved" | "rejected";
  resolved_by: string | null;
  created_at: string;
  resolved_at: string | null;
}

// --- Artifact ---
export interface Artifact {
  id: number;
  company_id: string;
  task_id: number | null;
  agent_id: string | null;
  artifact_type: string;
  title: string;
  content_ref: string;
  review_status: string;
  created_at: string;
}

// --- Event ---
export interface FloorEvent {
  id: number;
  company_id: string;
  event_type: string;
  target_type: string;
  payload_json: string;
  source_agent_id: string | null;
  created_at: string;
}

// --- Metrics ---
export interface Metrics {
  tasks_by_status: Record<string, number>;
  active_agents: number;
  total_agents: number;
  pending_approvals: number;
}

// --- Full state snapshot ---
export interface CompanyState {
  company: Company;
  floors: Floor[];
  rooms: Room[];
  teams: Team[];
  agents: Agent[];
  tasks: Task[];
  events: FloorEvent[];
  artifacts: Artifact[];
  approvals: Approval[];
  metrics: Metrics;
}

// --- Room detail ---
export interface RoomDetail {
  room: Room;
  desks: Desk[];
  agents: Agent[];
  tasks: Task[];
  wip: {
    in_progress: number;
    limit: number;
  };
}

// --- Models ---
export interface ModelInfo {
  id: string;
  owned_by: string;
  tier: string;
  context: number;
  pricing: Record<string, unknown> | null;
}

export interface ModelsResponse {
  free: ModelInfo[];
  fast: ModelInfo[];
  reasoning: ModelInfo[];
  frontier: ModelInfo[];
  _source: string;
}

// --- Actions ---
export interface ActionRequest {
  company_id: string;
  action: string;
  target_type: string;
  target_id: string;
  payload?: Record<string, unknown>;
}

export interface ActionResult {
  ok: boolean;
  result: Record<string, unknown>;
}

// --- Company create ---
export interface CompanyCreateRequest {
  name: string;
  goal?: string;
  template_id?: string;
  grilling_intensity?: number;
  budget_policy?: Record<string, unknown>;
  channels?: unknown[];
  logo?: string;
}

// --- SSE event ---
export interface SSEEvent {
  id: string;
  event: string;
  data: Record<string, unknown>;
}
