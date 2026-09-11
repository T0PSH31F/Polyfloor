/**
 * Polyfloor API client — typed fetch wrapper for all frozen endpoints.
 * @see /home/user/workspace/Polyfloor/docs/API_CONTRACT.md
 */

import type {
  CompanyCard,
  CompanyCreateRequest,
  CompanyState,
  RoomDetail,
  AgentDossier,
  ModelsResponse,
  ActionRequest,
  ActionResult,
  Task,
} from "./types";

const API_BASE = "/api";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  // Some endpoints may return 204
  if (res.status === 204) {
    return undefined as T;
  }

  return res.json();
}

// --- Companies ---
export function getCompanies(): Promise<CompanyCard[]> {
  return request<CompanyCard[]>("/companies");
}

export function createCompany(body: CompanyCreateRequest): Promise<CompanyCard> {
  return request<CompanyCard>("/companies", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getCompanyState(companyId: string): Promise<CompanyState> {
  return request<CompanyState>(`/companies/${companyId}/state`);
}

// --- Rooms ---
export function getRoom(
  companyId: string,
  roomId: string,
): Promise<RoomDetail> {
  return request<RoomDetail>(
    `/companies/${companyId}/rooms/${roomId}`,
  );
}

// --- Agents ---
export function getAgent(
  companyId: string,
  agentId: string,
): Promise<AgentDossier> {
  return request<AgentDossier>(
    `/companies/${companyId}/agents/${agentId}`,
  );
}

export function avatarUrl(companyId: string, agentId: string): string {
  return `${API_BASE}/companies/${companyId}/avatars/${agentId}.png`;
}

// --- Models ---
export function getModels(): Promise<ModelsResponse> {
  return request<ModelsResponse>("/models");
}

export function updateAgentModel(
  agentId: string,
  companyId: string,
  modelId: string,
): Promise<{ agent: Record<string, unknown> }> {
  const params = new URLSearchParams({ company_id: companyId });
  return request<{ agent: Record<string, unknown> }>(
    `/agents/${agentId}/model?${params}`,
    {
      method: "PUT",
      body: JSON.stringify({ model_id: modelId }),
    },
  );
}

// --- Actions ---
export function postAction(body: ActionRequest): Promise<ActionResult> {
  return request<ActionResult>("/actions", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function advanceTask(
  companyId: string,
  taskId: number,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "advance_task",
    target_type: "task",
    target_id: String(taskId),
  });
}

export function approveApproval(
  companyId: string,
  approvalId: number,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "approve",
    target_type: "approval",
    target_id: String(approvalId),
  });
}

export function rejectApproval(
  companyId: string,
  approvalId: number,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "reject",
    target_type: "approval",
    target_id: String(approvalId),
  });
}

export function pauseAgent(
  companyId: string,
  agentId: string,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "pause",
    target_type: "agent",
    target_id: agentId,
  });
}

export function resumeAgent(
  companyId: string,
  agentId: string,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "resume",
    target_type: "agent",
    target_id: agentId,
  });
}

export function stopAgent(
  companyId: string,
  agentId: string,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "stop",
    target_type: "agent",
    target_id: agentId,
  });
}

export function requestHire(
  companyId: string,
  teamId: string,
  role = "worker",
  reason = "",
  budgetUsd = 1.0,
): Promise<ActionResult> {
  return postAction({
    company_id: companyId,
    action: "request_hire",
    target_type: "system",
    target_id: teamId,
    payload: { team_id: teamId, role, reason, budget_usd: budgetUsd },
  });
}

export type { Task };
