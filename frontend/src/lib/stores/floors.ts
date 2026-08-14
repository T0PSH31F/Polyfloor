/**
 * Floor store — floor data and selection state.
 */

import { writable, derived } from "svelte/store";
import type { FloorConfig, Task } from "./types";
import { getFloors, getTasks } from "./api";

export const floors = writable<FloorConfig[]>([]);
export const selectedFloorId = writable<string | null>(null);
export const tasks = writable<Task[]>([]);
export const loading = writable(false);
export const error = writable<string | null>(null);

export const selectedFloor = derived(
  [floors, selectedFloorId],
  ([$floors, $selectedFloorId]) =>
    $floors.find((f) => f.id === $selectedFloorId) ?? null,
);

export const tasksByStatus = derived(tasks, ($tasks) => {
  const grouped: Record<string, Task[]> = {
    backlog: [],
    queued: [],
    in_progress: [],
    staging: [],
    done: [],
    rejected: [],
  };
  for (const task of $tasks) {
    (grouped[task.status] ??= []).push(task);
  }
  return grouped;
});

export async function loadFloors() {
  loading.set(true);
  error.set(null);
  try {
    const data = await getFloors();
    floors.set(data);
  } catch (e) {
    error.set(e instanceof Error ? e.message : "Failed to load floors");
  } finally {
    loading.set(false);
  }
}

export async function loadTasks(floorId?: string) {
  loading.set(true);
  error.set(null);
  try {
    const data = await getTasks(floorId);
    tasks.set(data);
  } catch (e) {
    error.set(e instanceof Error ? e.message : "Failed to load tasks");
  } finally {
    loading.set(false);
  }
}
