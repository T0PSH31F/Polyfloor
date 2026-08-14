<script lang="ts">
  import { onMount } from "svelte";
  import { floors, loadFloors, selectedFloorId, selectedFloor, tasks, loadTasks, tasksByStatus } from "$lib/stores/floors";
  import { getRoles } from "$lib/api";
  import type { RoleConfig } from "$lib/types";

  let roles = $state<RoleConfig[]>([]);

  onMount(async () => {
    await loadFloors();
  });

  $effect(() => {
    if ($selectedFloorId) {
      loadTasks($selectedFloorId);
      getRoles($selectedFloorId).then(r => roles = r).catch(() => roles = []);
    }
  });
</script>

<svelte:head>
  <title>Polyfloor — Floors</title>
</svelte:head>

<h1>Floor Overview</h1>

<div class="layout">
  <!-- Floor selector sidebar -->
  <aside class="sidebar">
    <h2>Floors</h2>
    {#each $floors as floor}
      <button
        class="floor-btn"
        class:active={$selectedFloorId === floor.id}
        onclick={() => selectedFloorId.set(floor.id)}
      >
        {floor.display_name}
      </button>
    {/each}
  </aside>

  <!-- Floor detail -->
  <div class="detail">
    {#if $selectedFloor}
      <h2>{$selectedFloor.display_name}</h2>
      <div class="meta">
        <span class="meta-item">ID: <code>{$selectedFloor.id}</code></span>
        <span class="meta-item">Schema: <code>{$selectedFloor.db_schema}</code></span>
        <span class="meta-item">Template: <code>{$selectedFloor.template ?? "none"}</code></span>
        <span class="meta-item">Budget: ${$selectedFloor.daily_budget_usd}/day</span>
      </div>

      <!-- Roles -->
      <section>
        <h3>Roles</h3>
        {#if roles.length === 0}
          <p class="muted">No roles configured</p>
        {:else}
          <div class="role-grid">
            {#each roles as role}
              <div class="role-card" class:disabled={!role.enable}>
                <div class="role-header">
                  <strong>{role.role_name}</strong>
                  <span class="badge badge--{role.enable ? 'working' : 'idle'}">
                    {role.enable ? "active" : "disabled"}
                  </span>
                </div>
                <div class="role-model">{role.model}</div>
                <div class="role-desc">{role.description}</div>
              </div>
            {/each}
          </div>
        {/if}
      </section>

      <!-- Sprint board preview -->
      <section>
        <h3>Current Tasks</h3>
        <div class="task-columns">
          {#each Object.entries($tasksByStatus) as [status, statusTasks]}
            <div class="task-column">
              <h4 class="column-header">
                <span class="badge badge--{status}">{status}</span>
                <span class="column-count">{statusTasks.length}</span>
              </h4>
              {#each statusTasks as task}
                <div class="task-card">
                  <div class="task-title">{task.title}</div>
                  {#if task.assigned_role}
                    <div class="task-role">{task.assigned_role}</div>
                  {/if}
                </div>
              {/each}
            </div>
          {/each}
        </div>
      </section>
    {:else}
      <p class="muted">Select a floor to view details</p>
    {/if}
  </div>
</div>

<style>
  h1 { font-size: 1.5rem; margin-bottom: 1rem; }

  .layout { display: flex; gap: 1.5rem; min-height: 70vh; }

  .sidebar {
    width: 200px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .sidebar h2 { font-size: 0.75rem; text-transform: uppercase; color: #a0aec0; margin-bottom: 0.5rem; }

  .floor-btn {
    background: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    color: #e2e8f0;
    text-align: left;
    font-size: 0.875rem;
  }
  .floor-btn:hover { border-color: #63b3ed; }
  .floor-btn.active { border-color: #63b3ed; background: #2a4365; }

  .detail { flex: 1; }
  .detail h2 { font-size: 1.25rem; margin-bottom: 0.75rem; }
  .detail h3 { font-size: 0.875rem; text-transform: uppercase; color: #a0aec0; margin: 1.5rem 0 0.75rem; }

  .meta { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.8125rem; color: #a0aec0; }
  .meta code { color: #63b3ed; }

  .muted { color: #718096; }

  .role-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; }
  .role-card {
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 0.375rem;
    padding: 0.75rem;
  }
  .role-card.disabled { opacity: 0.5; }
  .role-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
  .role-model { font-family: monospace; font-size: 0.75rem; color: #63b3ed; margin-bottom: 0.25rem; }
  .role-desc { font-size: 0.75rem; color: #a0aec0; }

  .task-columns { display: flex; gap: 0.75rem; overflow-x: auto; }
  .task-column { min-width: 160px; flex: 1; }
  .column-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; }
  .column-count { color: #718096; font-size: 0.75rem; }
  .task-card {
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 0.25rem;
    padding: 0.5rem;
    margin-bottom: 0.375rem;
    font-size: 0.8125rem;
  }
  .task-title { font-weight: 600; margin-bottom: 0.25rem; }
  .task-role { font-size: 0.6875rem; color: #a0aec0; font-family: monospace; }
</style>
