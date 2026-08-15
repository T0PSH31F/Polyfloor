/**
 * Task board grouping tests
 */
import { describe, it, expect } from "vitest";
import type { Task, TaskStatus } from "$lib/types";

function groupByStatus(tasks: Task[]): Record<string, Task[]> {
  const grouped: Record<string, Task[]> = {
    backlog: [],
    queued: [],
    in_progress: [],
    staging: [],
    done: [],
    rejected: [],
  };
  for (const task of tasks) {
    (grouped[task.status] ??= []).push(task);
  }
  return grouped;
}

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 1,
    floor_id: "production",
    sprint_id: null,
    title: "Test task",
    description: "",
    status: "backlog",
    assigned_role: null,
    priority: 0,
    metadata: {},
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("task board grouping", () => {
  it("groups tasks by status", () => {
    const tasks = [
      makeTask({ id: 1, status: "backlog" }),
      makeTask({ id: 2, status: "in_progress" }),
      makeTask({ id: 3, status: "backlog" }),
      makeTask({ id: 4, status: "done" }),
    ];

    const grouped = groupByStatus(tasks);

    expect(grouped.backlog).toHaveLength(2);
    expect(grouped.in_progress).toHaveLength(1);
    expect(grouped.done).toHaveLength(1);
    expect(grouped.queued).toHaveLength(0);
  });

  it("handles empty task list", () => {
    const grouped = groupByStatus([]);
    expect(grouped.backlog).toHaveLength(0);
    expect(grouped.queued).toHaveLength(0);
    expect(grouped.in_progress).toHaveLength(0);
    expect(grouped.staging).toHaveLength(0);
    expect(grouped.done).toHaveLength(0);
    expect(grouped.rejected).toHaveLength(0);
  });

  it("preserves task order within groups", () => {
    const tasks = [
      makeTask({ id: 1, title: "First", status: "backlog" }),
      makeTask({ id: 2, title: "Second", status: "backlog" }),
      makeTask({ id: 3, title: "Third", status: "backlog" }),
    ];

    const grouped = groupByStatus(tasks);

    expect(grouped.backlog[0].title).toBe("First");
    expect(grouped.backlog[1].title).toBe("Second");
    expect(grouped.backlog[2].title).toBe("Third");
  });

  it("handles all statuses", () => {
    const statuses: TaskStatus[] = [
      "backlog",
      "queued",
      "in_progress",
      "staging",
      "done",
      "rejected",
    ];

    const tasks = statuses.map((status, i) =>
      makeTask({ id: i + 1, status })
    );

    const grouped = groupByStatus(tasks);

    for (const status of statuses) {
      expect(grouped[status]).toHaveLength(1);
    }
  });

  it("isolates tasks by floor when filtered", () => {
    const tasks = [
      makeTask({ id: 1, floor_id: "production", status: "backlog" }),
      makeTask({ id: 2, floor_id: "research", status: "backlog" }),
      makeTask({ id: 3, floor_id: "production", status: "in_progress" }),
    ];

    const prodTasks = tasks.filter((t) => t.floor_id === "production");
    const grouped = groupByStatus(prodTasks);

    expect(grouped.backlog).toHaveLength(1);
    expect(grouped.in_progress).toHaveLength(1);
  });
});
