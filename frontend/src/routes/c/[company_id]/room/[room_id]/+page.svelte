<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { getRoom, getCompanyState, getAgent, getModels, updateAgentModel, avatarUrl, advanceTask, approveApproval, rejectApproval, pauseAgent, resumeAgent, stopAgent } from "$lib/api";
  import {
    subscribeSSE,
    disconnectSSE,
    sseConnected,
    latestEvent,
  } from "$lib/stores/sse";
  import {
    loadAssets,
    computeRoomLayout,
    drawTeamRoom,
    hitTestRoom,
    VIEW_W,
    VIEW_H,
    type RoomLayout,
  } from "$lib/canvas";
  import type { RoomDetail, CompanyState, AgentDossier, ModelsResponse, Agent, Desk, SSEEvent } from "$lib/types";

  const companyId = $derived($page.params.company_id ?? "");
  const roomId = $derived($page.params.room_id ?? "");

  let canvas = $state<HTMLCanvasElement | null>(null);
  let roomDetail = $state<RoomDetail | null>(null);
  let companyState = $state<CompanyState | null>(null);
  let selectedAgent = $state<AgentDossier | null>(null);
  let models = $state<ModelsResponse | null>(null);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let scale = 3;
  let frame = $state(0);
  let layout = $state<RoomLayout | null>(null);
  let rafId: number | null = null;
  let activeDrawer = $state<string | null>(null); // 'kanban' | 'approvals' | 'events' | 'logbook'
  let selectedModel = $state<string>("");
  let actionError = $state<string | null>(null);

  // Typewriter dialogue state
  let dialogue = $state("");
  let dialogueTarget = $state("");
  let typeTimer: ReturnType<typeof setTimeout> | null = null;

  function typewriter(text: string) {
    if (typeTimer) clearTimeout(typeTimer);
    dialogueTarget = text;
    dialogue = "";
    let i = 0;
    const tick = () => {
      if (i < dialogueTarget.length) {
        dialogue += dialogueTarget[i];
        i++;
        typeTimer = setTimeout(tick, 30);
      }
    };
    tick();
  }

  // SSE delta application
  function applySSEDelta(ev: SSEEvent) {
    if (!roomDetail) return;
    const eventType = ev.event;
    const data = ev.data;

    if (eventType === "agent.state_changed" || eventType === "agent.paused" || eventType === "agent.resumed") {
      const agentId = data.agent_id as string | undefined;
      const newState = data.state as string | undefined;
      if (agentId && newState) {
        const agent = roomDetail.agents.find((a) => a.id === agentId);
        if (agent) {
          agent.state = newState as Agent["state"];
        }
        // Also update in company state
        if (companyState) {
          const csAgent = companyState.agents.find((a) => a.id === agentId);
          if (csAgent) csAgent.state = newState as Agent["state"];
        }
      }
    } else if (eventType === "task.advanced" || eventType === "task.created") {
      if (data.task) {
        const task = data.task as Record<string, unknown>;
        const existing = roomDetail.tasks.find((t) => t.id === task.id);
        if (existing) {
          Object.assign(existing, task);
        }
      }
      if (companyState && data.task) {
        const task = data.task as Record<string, unknown>;
        const existing = companyState.tasks.find((t) => t.id === task.id);
        if (existing) Object.assign(existing, task);
      }
    } else if (eventType === "approval.requested" || eventType === "approval.resolved") {
      if (data.approval) {
        const approval = data.approval as Record<string, unknown>;
        if (companyState) {
          const existing = companyState.approvals.find((a) => a.id === approval.id);
          if (existing) Object.assign(existing, approval);
        }
      }
    } else if (eventType === "hr.hired") {
      // Refresh room to get new agents
      refreshRoom();
    }
  }

  let lastEventId: string | null = null;
  $effect(() => {
    const ev = $latestEvent;
    if (ev && ev.id !== lastEventId) {
      lastEventId = ev.id;
      applySSEDelta(ev);
    }
  });

  async function refreshRoom() {
    try {
      const detail = await getRoom(companyId, roomId);
      roomDetail = detail;
      layout = computeRoomLayout(detail.desks, detail.agents);
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to load room";
    }
  }

  function startAnimation() {
    let lastTime = 0;
    const FRAME_INTERVAL = 400;

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
    if (!canvas || !layout || !roomDetail) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    drawTeamRoom(
      ctx,
      scale,
      layout,
      roomDetail.room.label,
      roomDetail.wip,
      frame,
    );
  }

  async function handleCanvasClick(e: MouseEvent) {
    if (!canvas || !layout) return;
    const rect = canvas.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const hit = hitTestRoom(layout, px, py, scale);
    if (hit) {
      await openDossier(hit.id);
    }
  }

  async function openDossier(agentId: string) {
    try {
      selectedAgent = await getAgent(companyId, agentId);
      selectedModel = selectedAgent.agent.model_id || "";
      typewriter(`> ${selectedAgent.agent.name}\n> Role: ${selectedAgent.agent.role}\n> State: ${selectedAgent.agent.state}`);
      activeDrawer = null;
    } catch (e) {
      actionError = e instanceof Error ? e.message : "Failed to load agent";
    }
  }

  async function handleModelChange(modelId: string) {
    if (!selectedAgent) return;
    try {
      await updateAgentModel(selectedAgent.agent.id, companyId, modelId);
      selectedAgent.agent.model_id = modelId;
      selectedModel = modelId;
      typewriter(`> Model updated to ${modelId}`);
    } catch (e) {
      actionError = e instanceof Error ? e.message : "Failed to update model";
    }
  }

  async function handleAction(action: "approve" | "reject" | "pause" | "resume" | "stop") {
    if (!selectedAgent) return;
    try {
      actionError = null;
      if (action === "pause") {
        await pauseAgent(companyId, selectedAgent.agent.id);
        selectedAgent.agent.state = "paused";
        typewriter(`> ${selectedAgent.agent.name} paused.`);
      } else if (action === "resume") {
        await resumeAgent(companyId, selectedAgent.agent.id);
        selectedAgent.agent.state = "idle";
        typewriter(`> ${selectedAgent.agent.name} resumed.`);
      } else if (action === "stop") {
        await stopAgent(companyId, selectedAgent.agent.id);
        selectedAgent.agent.state = "retired";
        typewriter(`> ${selectedAgent.agent.name} retired.`);
      }
    } catch (e) {
      actionError = e instanceof Error ? e.message : "Action failed";
    }
  }

  async function handleAdvanceTask(taskId: number) {
    try {
      actionError = null;
      await advanceTask(companyId, taskId);
      typewriter(`> Task ${taskId} advanced.`);
      // Refresh to get updated task
      await refreshRoom();
      if (companyState) {
        companyState = await getCompanyState(companyId);
      }
    } catch (e) {
      actionError = e instanceof Error ? e.message : "Failed to advance task";
    }
  }

  async function handleApproval(approvalId: number, decision: "approve" | "reject") {
    try {
      actionError = null;
      if (decision === "approve") {
        await approveApproval(companyId, approvalId);
      } else {
        await rejectApproval(companyId, approvalId);
      }
      typewriter(`> Approval ${approvalId} ${decision}d.`);
      if (companyState) {
        companyState = await getCompanyState(companyId);
      }
    } catch (e) {
      actionError = e instanceof Error ? e.message : "Approval action failed";
    }
  }

  function toggleDrawer(name: string) {
    activeDrawer = activeDrawer === name ? null : name;
  }

  const kanbanColumns = $derived(
    companyState
      ? [
          { status: "BACKLOG", tasks: companyState.tasks.filter((t) => t.status === "BACKLOG") },
          { status: "READY", tasks: companyState.tasks.filter((t) => t.status === "READY") },
          { status: "IN_PROGRESS", tasks: companyState.tasks.filter((t) => t.status === "IN_PROGRESS") },
          { status: "REVIEW", tasks: companyState.tasks.filter((t) => t.status === "REVIEW") },
          { status: "AWAITING_APPROVAL", tasks: companyState.tasks.filter((t) => t.status === "AWAITING_APPROVAL") },
          { status: "DONE", tasks: companyState.tasks.filter((t) => t.status === "DONE") },
          { status: "BLOCKED", tasks: companyState.tasks.filter((t) => t.status === "BLOCKED") },
        ]
      : [],
  );

  const pendingApprovals = $derived(
    companyState
      ? companyState.approvals.filter((a) => a.status === "pending")
      : [],
  );

  const recentEvents = $derived(
    companyState
      ? companyState.events.slice(-20).reverse()
      : [],
  );

  onMount(async () => {
    await loadAssets();
    try {
      const [detail, state] = await Promise.all([
        getRoom(companyId, roomId),
        getCompanyState(companyId),
      ]);
      roomDetail = detail;
      companyState = state;
      layout = computeRoomLayout(detail.desks, detail.agents);
      subscribeSSE(companyId);
      startAnimation();

      // Load models in background
      try {
        models = await getModels();
      } catch {
        // Models optional
      }
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to load room";
    } finally {
      loading = false;
    }
  });

  onDestroy(() => {
    disconnectSSE();
    if (rafId) cancelAnimationFrame(rafId);
    if (typeTimer) clearTimeout(typeTimer);
  });

  $effect(() => {
    if (roomDetail && layout) {
      render();
    }
  });

  const allModels = $derived(
    models
      ? [...models.free, ...models.fast, ...models.reasoning, ...models.frontier]
      : [],
  );
</script>

<svelte:head>
  <title>Polyfloor — {roomDetail?.room.label || "Room"}</title>
</svelte:head>

<div class="room-view">
  <div class="room-view__topbar">
    <button class="btn-back" onclick={() => goto(`/c/${companyId}`)}>← LOBBY</button>
    <span class="room-view__name">{roomDetail?.room.label || "Loading..."}</span>
    <span class="room-view__status">
      {#if $sseConnected}
        <span class="status-dot status-dot--on"></span> LIVE
      {:else}
        <span class="status-dot status-dot--off"></span> IDLE
      {/if}
    </span>
  </div>

  {#if loading}
    <div class="room-view__loading">
      <p class="text-dim">Loading room...</p>
    </div>
  {:else if error}
    <div class="room-view__error">
      <p class="text-red">ERROR: {error}</p>
      <button onclick={() => goto(`/c/${companyId}`)}>BACK</button>
    </div>
  {:else}
    <!-- Top screen: canvas -->
    <div class="top-screen">
      <canvas
        bind:this={canvas}
        width={VIEW_W * scale}
        height={VIEW_H * scale}
        onclick={handleCanvasClick}
        class="top-screen__canvas"
      ></canvas>
    </div>

    <!-- Bottom screen: Pokétch console -->
    <div class="bottom-screen">
      <!-- Dialogue box (typewriter) -->
      <div class="dialogue-box">
        <pre class="dialogue-box__text">{dialogue}{#if dialogue.length < dialogueTarget.length}_{/if}</pre>
      </div>

      {#if selectedAgent}
        <!-- Agent dossier -->
        <div class="dossier">
          <div class="dossier__portrait">
            <img
              src={avatarUrl(companyId, selectedAgent.agent.id)}
              alt={selectedAgent.agent.name}
              class="dossier__img"
              onerror={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
            />
          </div>
          <div class="dossier__info">
            <div class="dossier__name">{selectedAgent.agent.name}</div>
            <div class="dossier__meta">
              <span class="text-dim">Role:</span> {selectedAgent.agent.role}
              <span class="text-dim">State:</span>
              <span class="state-badge state-badge--{selectedAgent.agent.state}">{selectedAgent.agent.state}</span>
            </div>
            <div class="dossier__bars">
              <div class="bar">
                <span class="bar__label">TOKENS</span>
                <div class="bar__track">
                  <div class="bar__fill bar__fill--blue" style="width: {Math.min(100, (selectedAgent.agent.token_spend / 10000) * 100)}%"></div>
                </div>
                <span class="bar__value">{selectedAgent.agent.token_spend}</span>
              </div>
            </div>
            <div class="dossier__model">
              <label for="model-select" class="text-dim">Model:</label>
              <select id="model-select" bind:value={selectedModel} onchange={() => handleModelChange(selectedModel)}>
                <option value="">(default)</option>
                {#each allModels as m}
                  <option value={m.id}>{m.id} ({m.tier})</option>
                {/each}
              </select>
            </div>
            <div class="dossier__actions">
              {#if selectedAgent.agent.state === "paused"}
                <button onclick={() => handleAction("resume")}>RESUME</button>
              {:else if selectedAgent.agent.state !== "retired"}
                <button onclick={() => handleAction("pause")}>PAUSE</button>
              {/if}
              {#if selectedAgent.agent.state !== "retired"}
                <button class="btn-danger" onclick={() => handleAction("stop")}>STOP</button>
              {/if}
            </div>
          </div>
        </div>
      {/if}

      {#if actionError}
        <div class="action-error text-red">{actionError}</div>
      {/if}

      <!-- Drawer buttons -->
      <div class="drawer-buttons">
        <button class="drawer-btn" class:active={activeDrawer === "kanban"} onclick={() => toggleDrawer("kanban")}>
          KANBAN {#if companyState}{companyState.tasks.length}{/if}
        </button>
        <button class="drawer-btn" class:active={activeDrawer === "approvals"} onclick={() => toggleDrawer("approvals")}>
          APPROVALS {#if pendingApprovals.length}({pendingApprovals.length}){/if}
        </button>
        <button class="drawer-btn" class:active={activeDrawer === "events"} onclick={() => toggleDrawer("events")}>
          EVENTS
        </button>
        <button class="drawer-btn" class:active={activeDrawer === "logbook"} onclick={() => toggleDrawer("logbook")}>
          LOGBOOK
        </button>
      </div>

      <!-- Drawers -->
      {#if activeDrawer === "kanban"}
        <div class="drawer">
          <div class="kanban">
            {#each kanbanColumns as col}
              <div class="kanban__col">
                <div class="kanban__col-header">
                  {col.status} ({col.tasks.length})
                </div>
                <div class="kanban__col-body">
                  {#each col.tasks as task}
                    <div class="kanban__task">
                      <div class="kanban__task-title">{task.title}</div>
                      <div class="kanban__task-meta text-dim">
                        #{task.id} · P{task.priority}
                      </div>
                      {#if col.status !== "DONE" && col.status !== "BLOCKED"}
                        <button class="kanban__advance" onclick={() => handleAdvanceTask(task.id)}>
                          ADVANCE →
                        </button>
                      {/if}
                    </div>
                  {/each}
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      {#if activeDrawer === "approvals"}
        <div class="drawer">
          {#if pendingApprovals.length === 0}
            <p class="text-dim drawer__empty">No pending approvals.</p>
          {:else}
            <div class="approvals">
              {#each pendingApprovals as approval}
                <div class="approval-item">
                  <div class="approval-item__info">
                    <div class="approval-item__title">
                      Approval #{approval.id} — {approval.policy_key}
                    </div>
                    <div class="approval-item__meta text-dim">
                      Risk: {approval.risk_level} · By: {approval.requested_by}
                    </div>
                    {#if approval.payload_json}
                      <div class="approval-item__payload text-dim">
                        {approval.payload_json.slice(0, 80)}
                      </div>
                    {/if}
                  </div>
                  <div class="approval-item__actions">
                    <button class="btn-approve" onclick={() => handleApproval(approval.id, "approve")}>APPROVE</button>
                    <button class="btn-reject" onclick={() => handleApproval(approval.id, "reject")}>REJECT</button>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      {#if activeDrawer === "events"}
        <div class="drawer">
          {#if recentEvents.length === 0}
            <p class="text-dim drawer__empty">No events yet.</p>
          {:else}
            <div class="event-log">
              {#each recentEvents as ev}
                <div class="event-log__item">
                  <span class="event-log__type">{ev.event_type}</span>
                  <span class="event-log__time text-dim">{ev.created_at?.slice(11, 19) || ""}</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      {#if activeDrawer === "logbook"}
        <div class="drawer">
          {#if selectedAgent && selectedAgent.runs.length > 0}
            <div class="logbook">
              {#each selectedAgent.runs as run}
                <div class="logbook__item">
                  <span class="logbook__status state-badge state-badge--{run.status}">{run.status}</span>
                  <span class="text-dim">{run.model_id || "default"}</span>
                  <span class="text-dim">{run.token_usage} tok</span>
                  <span class="text-dim">${run.cost_usd.toFixed(4)}</span>
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-dim drawer__empty">
              {#if selectedAgent}
                No runs recorded for this agent.
              {:else}
                Select an agent to view their logbook.
              {/if}
            </p>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .room-view {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .room-view__topbar {
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

  .room-view__name {
    font-size: 10px;
    color: var(--gba-accent);
  }

  .room-view__status {
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

  .room-view__loading,
  .room-view__error {
    text-align: center;
    padding: 40px;
    background: var(--gba-surface);
    border: 2px solid var(--gba-border);
  }

  .room-view__error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  /* Top screen */
  .top-screen {
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
    cursor: pointer;
  }

  /* Bottom screen — Pokétch */
  .bottom-screen {
    background: var(--gba-surface);
    border: 4px solid var(--gba-border-bright);
    border-radius: 4px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* Dialogue box */
  .dialogue-box {
    background: var(--gba-bg);
    border: 2px solid var(--gba-border);
    padding: 10px;
    min-height: 48px;
  }

  .dialogue-box__text {
    font-size: 8px;
    line-height: 1.6;
    color: var(--gba-text);
    white-space: pre-wrap;
    word-break: break-word;
    font-family: var(--font-pixel);
  }

  /* Dossier */
  .dossier {
    display: flex;
    gap: 12px;
    background: var(--gba-surface-alt);
    border: 2px solid var(--gba-border);
    padding: 10px;
  }

  .dossier__portrait {
    flex-shrink: 0;
    width: 48px;
    height: 48px;
    background: var(--gba-bg);
    border: 2px solid var(--gba-border-bright);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .dossier__img {
    width: 100%;
    height: 100%;
    image-rendering: pixelated;
    object-fit: cover;
  }

  .dossier__info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .dossier__name {
    font-size: 10px;
    color: var(--gba-accent);
  }

  .dossier__meta {
    font-size: 7px;
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }

  .state-badge {
    font-size: 6px;
    padding: 2px 4px;
    text-transform: uppercase;
  }

  .state-badge--idle {
    background: var(--gba-border-bright);
    color: var(--gba-text);
  }

  .state-badge--working {
    background: var(--gba-green);
    color: var(--gba-bg);
  }

  .state-badge--paused {
    background: var(--gba-yellow);
    color: var(--gba-bg);
  }

  .state-badge--retired {
    background: var(--gba-red);
    color: var(--gba-text);
  }

  .dossier__bars {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .bar {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 6px;
  }

  .bar__label {
    color: var(--gba-text-dim);
    width: 50px;
  }

  .bar__track {
    flex: 1;
    height: 6px;
    background: var(--gba-bg);
    border: 1px solid var(--gba-border);
  }

  .bar__fill {
    height: 100%;
  }

  .bar__fill--blue {
    background: var(--gba-blue);
  }

  .bar__value {
    color: var(--gba-text-dim);
    font-size: 6px;
  }

  .dossier__model {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 7px;
  }

  .dossier__model select {
    font-size: 7px;
    flex: 1;
  }

  .dossier__actions {
    display: flex;
    gap: 6px;
  }

  .dossier__actions button {
    font-size: 7px;
    padding: 4px 8px;
  }

  .btn-danger {
    border-color: var(--gba-red);
    color: var(--gba-red);
  }

  .btn-danger:hover {
    background: rgba(244, 67, 54, 0.2);
  }

  .btn-approve {
    border-color: var(--gba-green);
    color: var(--gba-green);
    font-size: 7px;
    padding: 4px 8px;
  }

  .btn-approve:hover {
    background: rgba(76, 175, 80, 0.2);
  }

  .btn-reject {
    border-color: var(--gba-red);
    color: var(--gba-red);
    font-size: 7px;
    padding: 4px 8px;
  }

  .btn-reject:hover {
    background: rgba(244, 67, 54, 0.2);
  }

  .action-error {
    font-size: 7px;
    padding: 6px;
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid var(--gba-red);
  }

  /* Drawer buttons */
  .drawer-buttons {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .drawer-btn {
    font-size: 7px;
    padding: 4px 8px;
    flex: 1;
    min-width: 60px;
  }

  .drawer-btn.active {
    background: var(--gba-accent-dim);
    border-color: var(--gba-accent);
  }

  /* Drawers */
  .drawer {
    background: var(--gba-bg);
    border: 2px solid var(--gba-border);
    padding: 10px;
    max-height: 300px;
    overflow-y: auto;
  }

  .drawer__empty {
    text-align: center;
    padding: 16px;
    font-size: 8px;
  }

  /* Kanban */
  .kanban {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    min-width: 0;
  }

  .kanban__col {
    min-width: 130px;
    flex-shrink: 0;
    background: var(--gba-surface);
    border: 1px solid var(--gba-border);
  }

  .kanban__col-header {
    font-size: 6px;
    padding: 4px 6px;
    background: var(--gba-border);
    color: var(--gba-text);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .kanban__col-body {
    padding: 4px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .kanban__task {
    background: var(--gba-bg);
    border: 1px solid var(--gba-border);
    padding: 4px 6px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .kanban__task-title {
    font-size: 7px;
    line-height: 1.3;
    word-break: break-word;
  }

  .kanban__task-meta {
    font-size: 6px;
  }

  .kanban__advance {
    font-size: 6px;
    padding: 2px 4px;
    margin-top: 2px;
    align-self: flex-start;
  }

  /* Approvals */
  .approvals {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .approval-item {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    background: var(--gba-surface);
    border: 1px solid var(--gba-border);
    padding: 8px;
  }

  .approval-item__info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .approval-item__title {
    font-size: 8px;
    color: var(--gba-accent);
  }

  .approval-item__meta {
    font-size: 6px;
  }

  .approval-item__payload {
    font-size: 6px;
    word-break: break-all;
  }

  .approval-item__actions {
    display: flex;
    flex-direction: column;
    gap: 4px;
    justify-content: center;
  }

  /* Event log */
  .event-log {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .event-log__item {
    display: flex;
    justify-content: space-between;
    font-size: 7px;
    padding: 2px 4px;
    border-bottom: 1px solid var(--gba-border);
  }

  .event-log__type {
    color: var(--gba-accent);
  }

  /* Logbook */
  .logbook {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .logbook__item {
    display: flex;
    gap: 8px;
    align-items: center;
    font-size: 7px;
    padding: 4px;
    border-bottom: 1px solid var(--gba-border);
  }

  @media (max-width: 600px) {
    .top-screen__canvas {
      width: 100%;
    }

    .dossier {
      flex-direction: column;
    }

    .dossier__portrait {
      align-self: center;
    }
  }
</style>
