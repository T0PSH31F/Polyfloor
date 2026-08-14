<script lang="ts">
  import { events, filteredEvents, activeFloorId, clearEvents, connected } from "$lib/stores/events";
  import { floors } from "$lib/stores/floors";

  function formatTime(iso?: string) {
    if (!iso) return "";
    return new Date(iso).toLocaleTimeString();
  }
</script>

<svelte:head>
  <title>Polyfloor — Event Log</title>
</svelte:head>

<h1>Event Log</h1>

<div class="controls">
  <label>
    Floor filter:
    <select bind:value={$activeFloorId}>
      <option value={null}>All floors</option>
      {#each $floors as floor}
        <option value={floor.id}>{floor.display_name}</option>
      {/each}
    </select>
  </label>

  <span class="connection" class:connected={$connected}>
    {$connected ? "Connected" : "Disconnected"}
  </span>

  <button onclick={clearEvents}>Clear</button>
</div>

<div class="event-table">
  <div class="event-header">
    <span class="col-type">Type</span>
    <span class="col-floor">Floor</span>
    <span class="col-actor">Actor</span>
    <span class="col-payload">Payload</span>
    <span class="col-time">Time</span>
  </div>
  {#each $filteredEvents as event, i}
    <div class="event-row" class:even={i % 2 === 0}>
      <span class="col-type">
        <span class="badge badge--{event.event_type.includes('approval') ? 'alert' : 'working'}">
          {event.event_type}
        </span>
      </span>
      <span class="col-floor">{event.floor_id}</span>
      <span class="col-actor">{event.actor}</span>
      <span class="col-payload">
        <code>{JSON.stringify(event.payload).slice(0, 80)}</code>
      </span>
      <span class="col-time">{formatTime(event.created_at)}</span>
    </div>
  {:else}
    <p class="muted">No events recorded</p>
  {/each}
</div>

<style>
  h1 { font-size: 1.5rem; margin-bottom: 1rem; }

  .controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
    font-size: 0.875rem;
  }
  .controls select, .controls button {
    background: #2d3748;
    color: #e2e8f0;
    border: 1px solid #4a5568;
    border-radius: 0.25rem;
    padding: 0.375rem 0.5rem;
  }
  .controls button:hover { border-color: #63b3ed; }

  .connection {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    background: #742a2a;
    color: #fc8181;
  }
  .connection.connected {
    background: #22543d;
    color: #68d391;
  }

  .event-table { font-size: 0.8125rem; }
  .event-header, .event-row {
    display: grid;
    grid-template-columns: 140px 120px 100px 1fr 100px;
    gap: 0.5rem;
    padding: 0.5rem;
    align-items: center;
  }
  .event-header {
    font-weight: 600;
    color: #a0aec0;
    text-transform: uppercase;
    font-size: 0.6875rem;
    letter-spacing: 0.05em;
    border-bottom: 1px solid #4a5568;
  }
  .event-row.even { background: rgba(255,255,255,0.02); }
  .col-payload code { font-size: 0.6875rem; color: #a0aec0; }
  .col-floor, .col-actor { font-family: monospace; }
  .col-time { color: #718096; font-size: 0.75rem; }

  .muted { color: #718096; padding: 1rem; }
</style>
