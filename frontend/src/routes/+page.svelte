<script lang="ts">
  import { onMount } from "svelte";
  import { floors, selectedFloorId, loadFloors } from "$lib/stores/floors";
  import { filteredEvents, agentStates } from "$lib/stores/events";
  import { getApprovals } from "$lib/api";
  import type { Approval } from "$lib/types";

  let approvals = $state<Approval[]>([]);
  let loadingApprovals = $state(true);

  onMount(async () => {
    await loadFloors();
    try {
      approvals = await getApprovals(undefined, "pending");
    } catch {
      // API may not be available
    } finally {
      loadingApprovals = false;
    }
  });

  function selectFloor(id: string) {
    selectedFloorId.set(id);
  }

  const recentEvents = $derived($filteredEvents.slice(0, 10));
</script>

<svelte:head>
  <title>Polyfloor — Reception</title>
</svelte:head>

<h1>Reception</h1>
<p class="subtitle">Company overview and approval queue</p>

<div class="grid">
  <!-- Floor overview -->
  <section class="card">
    <h2>Floors</h2>
    {#if $floors.length === 0}
      <p class="muted">No floors configured</p>
    {:else}
      <div class="floor-list">
        {#each $floors as floor}
          <button
            class="floor-item"
            class:active={$selectedFloorId === floor.id}
            onclick={() => selectFloor(floor.id)}
          >
            <span class="floor-name">{floor.display_name}</span>
            <span class="floor-id">{floor.id}</span>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Approval queue -->
  <section class="card">
    <h2>Pending Approvals</h2>
    {#if loadingApprovals}
      <p class="muted">Loading...</p>
    {:else if approvals.length === 0}
      <p class="muted">No pending approvals</p>
    {:else}
      <div class="approval-list">
        {#each approvals as approval}
          <div class="approval-item">
            <span class="badge badge--{approval.status}">{approval.status}</span>
            <span class="approval-type">{approval.approval_type}</span>
            <span class="approval-desc">{approval.description}</span>
            <span class="approval-floor">{approval.floor_id}</span>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Recent events -->
  <section class="card">
    <h2>Recent Events</h2>
    {#if recentEvents.length === 0}
      <p class="muted">No events yet</p>
    {:else}
      <div class="event-list">
        {#each recentEvents as event}
          <div class="event-item">
            <span class="event-type">{event.event_type}</span>
            <span class="event-floor">{event.floor_id}</span>
            <span class="event-actor">{event.actor}</span>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Agent states -->
  <section class="card">
    <h2>Agent Roster</h2>
    {#if Object.keys($agentStates).length === 0}
      <p class="muted">No agent activity</p>
    {:else}
      <div class="agent-list">
        {#each Object.entries($agentStates) as [key, state]}
          <div class="agent-item">
            <span class="badge badge--{state}">{state}</span>
            <span class="agent-key">{key}</span>
          </div>
        {/each}
      </div>
    {/if}
  </section>
</div>

<style>
  h1 { font-size: 1.5rem; margin-bottom: 0.25rem; }
  .subtitle { color: #a0aec0; margin-bottom: 1.5rem; font-size: 0.875rem; }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .card {
    background: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 0.5rem;
    padding: 1rem;
  }

  .card h2 {
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #a0aec0;
    margin-bottom: 0.75rem;
  }

  .muted { color: #718096; font-size: 0.875rem; }

  .floor-list { display: flex; flex-direction: column; gap: 0.5rem; }
  .floor-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    color: #e2e8f0;
    text-align: left;
  }
  .floor-item:hover { border-color: #63b3ed; }
  .floor-item.active { border-color: #63b3ed; background: #2a4365; }
  .floor-name { font-weight: 600; }
  .floor-id { color: #718096; font-family: monospace; font-size: 0.75rem; }

  .approval-list, .event-list, .agent-list {
    display: flex;
    flex-direction: column;
    gap: 0.375rem;
  }
  .approval-item, .event-item, .agent-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
  }
  .approval-type { font-weight: 600; }
  .approval-floor, .event-floor { color: #718096; font-family: monospace; font-size: 0.75rem; margin-left: auto; }
  .event-type { font-family: monospace; font-size: 0.75rem; }
  .event-actor { color: #a0aec0; }
</style>
