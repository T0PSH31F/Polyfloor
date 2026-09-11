<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { getCompanies } from "$lib/api";
  import type { CompanyCard } from "$lib/types";

  let companies = $state<CompanyCard[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  onMount(async () => {
    try {
      companies = await getCompanies();
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to load companies";
    } finally {
      loading = false;
    }
  });

  function enterCompany(id: string) {
    goto(`/c/${id}`);
  }

  function startIntake() {
    goto("/new");
  }
</script>

<svelte:head>
  <title>Polyfloor — 1F Company Directory</title>
</svelte:head>

<div class="directory">
  <header class="directory__header">
    <h1 class="directory__title">POLYFLOOR</h1>
    <p class="directory__subtitle">1F — COMPANY DIRECTORY</p>
  </header>

  <div class="directory__actions">
    <button onclick={startIntake} class="btn-create">
      + CREATE COMPANY
    </button>
  </div>

  {#if loading}
    <div class="directory__loading">
      <p class="text-dim">Loading companies...</p>
    </div>
  {:else if error}
    <div class="directory__error">
      <p class="text-red">ERROR: {error}</p>
      <button onclick={() => location.reload()}>RETRY</button>
    </div>
  {:else if companies.length === 0}
    <div class="directory__empty">
      <p class="text-dim">No companies yet.</p>
      <p class="text-dim">Create one to get started.</p>
    </div>
  {:else}
    <div class="directory__grid">
      {#each companies as company}
        <button
          class="company-card"
          onclick={() => enterCompany(company.id)}
        >
          <div class="company-card__name">{company.name}</div>
          <div class="company-card__goal text-dim">
            {company.goal || "No goal set"}
          </div>
          <div class="company-card__meta">
            <span class="badge badge--{company.status}">{company.status}</span>
            <span class="text-dim">{company.template_id}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .directory {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .directory__header {
    text-align: center;
    padding: 20px 0;
    border-bottom: 2px solid var(--gba-border);
  }

  .directory__title {
    font-size: 24px;
    color: var(--gba-accent);
    letter-spacing: 4px;
  }

  .directory__subtitle {
    font-size: 8px;
    color: var(--gba-text-dim);
    margin-top: 8px;
    letter-spacing: 2px;
  }

  .directory__actions {
    display: flex;
    justify-content: center;
  }

  .btn-create {
    font-size: 10px;
    padding: 10px 20px;
    background: var(--gba-accent-dim);
    border-color: var(--gba-accent);
  }

  .directory__loading,
  .directory__empty,
  .directory__error {
    text-align: center;
    padding: 40px 0;
  }

  .directory__error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }

  .directory__grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
  }

  .company-card {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background: var(--gba-surface);
    border: 2px solid var(--gba-border);
    text-align: left;
    min-height: 100px;
  }

  .company-card:hover {
    border-color: var(--gba-accent);
    background: var(--gba-surface-alt);
  }

  .company-card__name {
    font-size: 10px;
    color: var(--gba-text);
    word-break: break-word;
  }

  .company-card__goal {
    font-size: 7px;
    line-height: 1.3;
    flex-grow: 1;
  }

  .company-card__meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 4px;
  }

  .badge {
    font-size: 6px;
    padding: 2px 6px;
    background: var(--gba-border-bright);
    color: var(--gba-text);
    text-transform: uppercase;
  }

  .badge--active {
    background: var(--gba-green);
    color: var(--gba-bg);
  }

  .badge--paused {
    background: var(--gba-yellow);
    color: var(--gba-bg);
  }
</style>
