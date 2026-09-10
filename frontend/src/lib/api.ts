/**
 * Polyfloor API client — typed fetch wrapper.
 */

import type {
  FloorConfig,
  RoleConfig,
  Task,
  Approval,
  FloorEvent,
  Sprint,
} from "./types";

const API_BASE = "/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("polyfloor_token")
      : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json();
}

// Floors
export const getFloors = () => request<FloorConfig[]>("/floors");
export const getFloor = (id: string) => request<FloorConfig>(`/floors/${id}`);
export const updateFloorConfig = (id: string, update: Partial<FloorConfig>) =>
  request<FloorConfig>(`/floors/${id}/config`, {
    method: "PUT",
    body: JSON.stringify(update),
  });

// Roles
export const getRoles = (floorId: string) =>
  request<RoleConfig[]>(`/floors/${floorId}/roles`);
export const updateRole = (
  floorId: string,
  roleName: string,
  update: Partial<RoleConfig>,
) =>
  request<RoleConfig>(`/floors/${floorId}/roles/${roleName}`, {
    method: "PUT",
    body: JSON.stringify(update),
  });

// Tasks
export const getTasks = (floorId?: string, status?: string) => {
  const params = new URLSearchParams();
  if (floorId) params.set("floor_id", floorId);
  if (status) params.set("status", status);
  const qs = params.toString();
  return request<Task[]>(`/tasks${qs ? `?${qs}` : ""}`);
};

export const createTask = (task: {
  floor_id: string;
  title: string;
  description?: string;
  assigned_role?: string;
  priority?: number;
}) =>
  request<Task>("/tasks", {
    method: "POST",
    body: JSON.stringify(task),
  });

export const updateTask = (
  taskId: number,
  update: { status?: string; assigned_role?: string; priority?: number },
) =>
  request<Task>(`/tasks/${taskId}`, {
    method: "PATCH",
    body: JSON.stringify(update),
  });

// Approvals
export const getApprovals = (floorId?: string, status?: string) => {
  const params = new URLSearchParams();
  if (floorId) params.set("floor_id", floorId);
  if (status) params.set("status", status);
  const qs = params.toString();
  return request<Approval[]>(`/approvals${qs ? `?${qs}` : ""}`);
};

export const resolveApproval = (
  approvalId: number,
  status: "approved" | "rejected",
  resolvedBy: string,
) =>
  request<Approval>(`/approvals/${approvalId}/resolve`, {
    method: "POST",
    body: JSON.stringify({ status, resolved_by: resolvedBy }),
  });

// Sprints
export const getSprints = (floorId: string) =>
  request<Sprint[]>(`/floors/${floorId}/sprints`);
