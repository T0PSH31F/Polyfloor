<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { getCompanyState } from "$lib/api";
  import {
    subscribeSSE,
    disconnectSSE,
    sseConnected,
    latestEvent,
  } from "$lib/stores/sse";
  import {
    loadAssets,
    computeLobbyLayout,
    drawLobby,
    hitTestLobby,
    VIEW_W,
    VIEW_H,
    type LobbyLayout,
  } from "$lib/canvas";
  import type { CompanyState, Agent, Desk, SSEEvent } from "$lib/types";

  const companyId = $derived($page.params.company_id ?? "");

  let canvas = $state<HTMLCanvasElement | null>(null);
  let companyState = $state<CompanyState | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let scale = 3;
  let frame = $state(0);
  let layout = $state<LobbyLayout | null>(null);
  let rafId: number | null = null;

  // Track which room was last clicked (for tooltip)
  let hoveredRoom = $state<string | null>(null);

  // SSE delta application
  function applySSEDelta(ev: SSEEvent) {
    if (!companyState) return;
    const data = ev.data;
    const eventType = ev.event;

    // Apply known event types as deltas to the snapshot
    if (eventType === "agent.state_changed" || eventType === "agent.paused" || eventType === "agent.resumed") {
      const agentId = data.agent_id as string | undefined;
      const newStateVal = data.state as string | undefined;
      if (agentId) {
        const agent = companyState.agents.find((a) => a.id === agentId);
        if (agent && newStateVal) {
          agent.state = newStateVal as Agent["state"];
        }
      }
    } else if (eventType === "task.advanced" || eventType === "task.created") {
      if (data.task) {
        const task = data.task as Record<string, unknown>;
        const existing = companyState.tasks.find((t) => t.id === task.id);
        if (existing) {
          Object.assign(existing, task);
        }
      }
    } else if (eventType === "approval.requested" || eventType === "approval.resolved") {
      if (data.approval) {
        const approval = data.approval as Record<string, unknown>;
        const existing = companyState.approvals.find((a) => a.id === approval.id);
        if (existing) {
          Object.assign(existing, approval);
        }
      }
    } else if (eventType === "hr.hired") {
      // Could add new agents — trigger a state refresh
      refreshState();
    }

    // Recompute layout if agents changed
    if (companyState) {
      const desks: Desk[] = [];
      layout = computeLobbyLayout(companyState.rooms, companyState.agents, desks);
    }
  }

  // Watch for SSE events
  let lastEventId: string | null = null;
  $effect(() => {
    const ev = $latestEvent;
    if (ev && ev.id !== lastEventId) {
      lastEventId = ev.id;
      applySSEDelta(ev);
    }
  });

  async function refreshState() {
    if (!companyId) return;
    try {
      const newState = await getCompanyState(companyId);
      companyState = newState;
      const desks: Desk[] = [];
      layout = computeLobbyLayout(newState.rooms, newState.agents, desks);
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to load state";
    }
  }

  function startAnimation() {
    let lastTime = 0;
    const FRAME_INTERVAL = 500; // 2fps for breath animation

    function loop(time: number) {
      if (time - lastTime >= FRAME_INTERVAL) {
        frame = (frame + 1) % 4;
        lastTime = time;
        render();
      }
      rafId = requestAnimationFrame(loop);
    }
    rafId = requestAnimationFrame(loop);
  }

  function render() {
    if (!canvas || !layout || !companyState) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    drawLobby(ctx, scale, layout, companyState.company.name, companyState.company.goal, {
      activeAgents: companyState.metrics.active_agents,
      pendingApprovals: companyState.metrics.pending_approvals,
    });
  }

  function handleCanvasClick(e: MouseEvent) {
    if (!canvas || !layout) return;
    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const hit = hitTestLobby(layout, px, py, scale);
    if (hit) {
      goto(`/c/${companyId}/room/${hit.room.id}`);
    }
  }

  function handleCanvasMove(e: MouseEvent) {
    if (!canvas || !layout) return;
    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const hit = hitTestLobby(layout, px, py, scale);
    hoveredRoom = hit ? hit.room.label : null;
    canvas.style.cursor = hit ? "pointer" : "default";
  }

  onMount(async () => {
    await loadAssets();

    try {
      companyState = await getCompanyState(companyId);
      const desks: Desk[] = [];
      layout = computeLobbyLayout(companyState.rooms, companyState.agents, desks);
      subscribeSSE(companyId);
      startAnimation();
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to load company";
    } finally {
      loading = false;
    }
  });

  onDestroy(() => {
    disconnectSSE();
    if (rafId) cancelAnimationFrame(rafId);
  });

  // Re-render when state or frame changes
  $effect(() => {
    if (companyState && layout) {
      render();
    }
  });
</script>

<svelte:head>
  <title>Polyfloor — {companyState?.company.name || "Company"}</title>
</svelte:head>

<div class="lobby">
  <div class="lobby__topbar">
    <button class="btn-back" onclick={() => goto("/")}>← DIRECTORY</button>
    {#if companyState}
      <span class="lobby__name">{companyState.company.name}</span>
    {/if}
    <span class="lobby__status">
      {#if $sseConnected}
        <span class="status-dot status-dot--on"></span> LIVE
      {:else}
        <span class="status-dot status-dot--off"></span> IDLE
      {/if}
    </span>
  </div>

  {#if loading}
    <div class="lobby__loading">
      <p class="text-dim">Loading company...</p>
    </div>
  {:else if error}
    <div class="lobby__error">
      <p class="text-red">ERROR: {error}</p>
      <button onclick={() => goto("/")}>BACK</button>
    </div>
  {:else if companyState}
    <!-- Top screen: GBA canvas -->
    <div class="top-screen">
      <canvas
        bind:this={canvas}
        width={VIEW_W * scale}
        height={VIEW_H * scale}
        onclick={handleCanvasClick}
        onmousemove={handleCanvasMove}
        class="top-screen__canvas"
      ></canvas>
      {#if hoveredRoom}
        <div class="top-screen__tooltip">{hoveredRoom}</div>
      {/if}
    </div>

    <!-- Bottom screen: directory links -->
    <div class="bottom-screen">
      <div class="bottom-screen__section">
        <h3 class="section-title">ROOMS</h3>
        <div class="room-list">
          {#each layout?.rooms || [] as rt}
            <button
              class="room-link"
              onclick={() => goto(`/c/${companyId}/room/${rt.room.id}`)}
            >
              <span class="room-link__label">{rt.room.label}</span>
              <span class="room-link__counts">
                <span class="text-green">{rt.active}</span>
                <span class="text-red">{rt.blocked}</span>
                <span class="text-dim">{rt.vacant}</span>
              </span>
            </button>
          {/each}
        </div>
      </div>

      {#if companyState.metrics.pending_approvals > 0}
        <div class="bottom-screen__section">
          <h3 class="section-title">
            APPROVALS ({companyState.metrics.pending_approvals})
          </h3>
          <p class="text-dim">Open a team room to review.</p>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .lobby {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .lobby__topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    background: var(--gba-surface);
    border: 2px solid var(--gba-border);
  }

  .btn-back {
    font-size: 8px;
    padding: 4px 8px;
  }

  .lobby__name {
    font-size: 10px;
    color: var(--gba-accent);
  }

  .lobby__status {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 7px;
    color: var(--gba-text-dim);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    display: inline-block;
  }

  .status-dot--on {
    background: var(--gba-green);
  }

  .status-dot--off {
    background: var(--gba-text-dim);
  }

  .lobby__loading,
  .lobby__error {
    text-align: center;
    padding: 40px;
    background: var(--gba-surface);
    border: 2px solid var(--gba-border);
  }

  .lobby__error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  /* Top screen — GBA canvas */
  .top-screen {
    position: relative;
    background: var(--gba-bg);
    border: 4px solid var(--gba-border-bright);
    border-radius: 4px;
    padding: 8px;
    display: flex;
    justify-content: center;
  }

  .top-screen__canvas {
    image-rendering: pixelated;
    max-width: 100%;
    height: auto;
  }

  .top-screen__tooltip {
    position: absolute;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--gba-border);
    color: var(--gba-text);
    font-size: 7px;
    padding: 4px 8px;
    border: 1px solid var(--gba-accent);
    pointer-events: none;
    white-space: nowrap;
  }

  /* Bottom screen — DOM console */
  .bottom-screen {
    background: var(--gba-surface);
    border: 4px solid var(--gba-border-bright);
    border-radius: 4px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-height: 160px;
  }

  .bottom-screen__section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-title {
    font-size: 8px;
    color: var(--gba-accent);
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 1px solid var(--gba-border);
    padding-bottom: 4px;
  }

  .room-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 6px;
  }

  .room-link {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 8px;
    background: var(--gba-surface-alt);
    border: 1px solid var(--gba-border);
    font-size: 7px;
    text-align: left;
  }

  .room-link:hover {
    border-color: var(--gba-accent);
  }

  .room-link__label {
    color: var(--gba-text);
  }

  .room-link__counts {
    display: flex;
    gap: 6px;
    font-size: 7px;
  }

  @media (max-width: 600px) {
    .top-screen__canvas {
      width: 100%;
    }
  }
</style>
