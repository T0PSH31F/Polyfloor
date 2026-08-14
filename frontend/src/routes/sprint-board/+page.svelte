<script lang="ts">
  import { onMount } from "svelte";
  import { tasks, loadTasks, tasksByStatus } from "$lib/stores/floors";
  import { floors, loadFloors } from "$lib/stores/floors";

  let filterFloor = $state<string>("");
  let filterStatus = $state<string>("");

  onMount(async () => {
    await loadFloors();
    await loadTasks();
  });

  async function refresh() {
    await loadTasks(filterFloor || undefined);
  }

  $effect(() => {
    refresh();
  });
</script>

<svelte:head>
  <title>Polyfloor — Sprint Board</title>
</svelte:head>

<h1>Sprint Board</h1>

<div class="filters">
  <label>
    Floor:
    <select bind:value={filterFloor}>
      <option value="">All floors</option>
      {#each $floors as floor}
        <option value={floor.id}>{floor.display_name}</option>
      {/each}
    </select>
  </label>
</div>

<div class="board">
  {#each ["backlog", "queued", "in_progress", "staging", "done", "rejected"] as status}
    <div class="column">
      <div class="column-header">
        <span class="badge badge--{status}">{status}</span>
        <span class="count">{($tasksByStatus[status] ?? []).length}</span>
      </div>
      <div class="column-body">
        {#each ($tasksByStatus[status] ?? []) as task}
          <div class="task-card">
            <div class="task-title">{task.title}</div>
            <div class="task-meta">
              <span class="task-floor">{task.floor_id}</span>
              {#if task.assigned_role}
                <span class="task-role">{task.assigned_role}</span>
              {/if}
            </div>
            {#if task.description}
              <div class="task-desc">{task.description}</div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/each}
</div>

<style>
  h1 { font-size: 1.5rem; margin-bottom: 1rem; }

  .filters {
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }
  .filters select {
    background: #2d3748;
    color: #e2e8f0;
    border: 1px solid #4a5568;
    border-radius: 0.25rem;
    padding: 0.375rem 0.5rem;
  }

  .board {
    display: flex;
    gap: 0.75rem;
    overflow-x: auto;
    padding-bottom: 1rem;
  }

  .column {
    min-width: 180px;
    flex: 1;
    max-width: 250px;
  }

  .column-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #4a5568;
  }
  .count { color: #718096; font-size: 0.75rem; }

  .column-body {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .task-card {
    background: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 0.375rem;
    padding: 0.625rem;
  }
  .task-title { font-weight: 600; font-size: 0.8125rem; margin-bottom: 0.25rem; }
  .task-meta { display: flex; gap: 0.5rem; font-size: 0.6875rem; }
  .task-floor { font-family: monospace; color: #63b3ed; }
  .task-role { color: #a0aec0; }
  .task-desc { font-size: 0.75rem; color: #718096; margin-top: 0.375rem; }
</style>
