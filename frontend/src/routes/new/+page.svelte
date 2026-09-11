<script lang="ts">
  import { goto } from "$app/navigation";
  import { createCompany } from "$lib/api";

  let step = $state(0);
  let name = $state("");
  let goal = $state("");
  let intensity = $state(1);
  let budget = $state(100);
  let submitting = $state(false);
  let error = $state<string | null>(null);

  const intensities = [
    {
      value: 0,
      label: "GENTLE",
      desc: "Hands-off. Agents proceed with minimal questioning.",
    },
    {
      value: 1,
      label: "STANDARD",
      desc: "Balanced scrutiny. Key decisions get reviewed.",
    },
    {
      value: 2,
      label: "THOROUGH",
      desc: "Deep review at every stage. Slower but safer.",
    },
    {
      value: 3,
      label: "INTERROGATION",
      desc: "Every artifact grilled. Maximum friction.",
    },
  ];

  function next() {
    if (step < 3) step++;
  }

  function prev() {
    if (step > 0) step--;
  }

  function selectIntensity(val: number) {
    intensity = val;
  }

  async function submit() {
    if (!name.trim()) {
      error = "Company name is required";
      return;
    }
    submitting = true;
    error = null;
    try {
      const company = await createCompany({
        name: name.trim(),
        goal: goal.trim() || undefined,
        template_id: "digital-products",
        grilling_intensity: intensity,
      });
      goto(`/c/${company.id}`);
    } catch (e) {
      error = e instanceof Error ? e.message : "Failed to create company";
      submitting = false;
    }
  }

  const greetings = [
    "Welcome to Polyfloor.",
    "Let's build your company.",
    "What should we call it?",
  ];
</script>

<svelte:head>
  <title>Polyfloor — New Company Intake</title>
</svelte:head>

<div class="intake">
  <div class="intake__header">
    <button class="btn-back" onclick={() => goto("/")}>← BACK</button>
    <h2 class="intake__title">1F INTAKE</h2>
    <div class="intake__steps">{step + 1}/4</div>
  </div>

  <div class="intake__screen">
    {#if step === 0}
      <!-- Greeting + Goal -->
      <div class="step">
        <p class="step__greeting">{greetings[0]}</p>
        <p class="step__greeting">{greetings[1]}</p>
        <div class="step__field">
          <label for="goal-input">What is your company's goal?</label>
          <textarea
            id="goal-input"
            bind:value={goal}
            placeholder="e.g. Ship a SaaS landing page for a fintech startup"
            rows="3"
          ></textarea>
        </div>
      </div>
    {:else if step === 1}
      <!-- Grilling intensity -->
      <div class="step">
        <p class="step__label">How thoroughly should agents grill their work?</p>
        <div class="intensity-grid">
          {#each intensities as opt}
            <button
              class="intensity-option"
              class:selected={intensity === opt.value}
              onclick={() => selectIntensity(opt.value)}
            >
              <div class="intensity-option__label">{opt.label}</div>
              <div class="intensity-option__desc text-dim">{opt.desc}</div>
            </button>
          {/each}
        </div>
      </div>
    {:else if step === 2}
      <!-- Name + budget -->
      <div class="step">
        <div class="step__field">
          <label for="name-input">Company name</label>
          <input
            id="name-input"
            bind:value={name}
            placeholder="e.g. Acme Corp"
            maxlength="80"
          />
        </div>
        <div class="step__field">
          <label for="budget-input">Daily budget (USD): {budget}</label>
          <input
            id="budget-input"
            type="range"
            min="10"
            max="1000"
            step="10"
            bind:value={budget}
          />
        </div>
        <div class="step__field">
          <span class="text-dim step__field-label">Template</span>
          <div class="template-info text-dim">digital-products (locked)</div>
        </div>
      </div>
    {:else if step === 3}
      <!-- Confirm -->
      <div class="step">
        <p class="step__label">Review and create:</p>
        <div class="confirm-grid">
          <div class="confirm-row">
            <span class="text-dim">Name:</span>
            <span>{name || "(unnamed)"}</span>
          </div>
          <div class="confirm-row">
            <span class="text-dim">Goal:</span>
            <span>{goal || "(default)"}</span>
          </div>
          <div class="confirm-row">
            <span class="text-dim">Intensity:</span>
            <span>{intensities[intensity].label}</span>
          </div>
          <div class="confirm-row">
            <span class="text-dim">Template:</span>
            <span>digital-products</span>
          </div>
          <div class="confirm-row">
            <span class="text-dim">Budget:</span>
            <span>${budget}/day</span>
          </div>
        </div>
        {#if error}
          <p class="text-red step__error">{error}</p>
        {/if}
      </div>
    {/if}
  </div>

  <div class="intake__nav">
    {#if step > 0}
      <button onclick={prev} disabled={submitting}>← PREV</button>
    {/if}
    {#if step < 3}
      <button onclick={next}>NEXT →</button>
    {:else}
      <button onclick={submit} disabled={submitting || !name.trim()}>
        {submitting ? "CREATING..." : "CREATE COMPANY"}
      </button>
    {/if}
  </div>
</div>

<style>
  .intake {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .intake__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 2px solid var(--gba-border);
  }

  .btn-back {
    font-size: 8px;
    padding: 4px 8px;
  }

  .intake__title {
    font-size: 12px;
    color: var(--gba-accent);
    letter-spacing: 2px;
  }

  .intake__steps {
    font-size: 8px;
    color: var(--gba-text-dim);
  }

  .intake__screen {
    background: var(--gba-surface);
    border: 2px solid var(--gba-border);
    padding: 24px;
    min-height: 300px;
  }

  .step {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .step__greeting {
    font-size: 10px;
    color: var(--gba-text);
    line-height: 1.6;
  }

  .step__label {
    font-size: 10px;
    color: var(--gba-accent);
    margin-bottom: 8px;
  }

  .step__field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .step__field label,
  .step__field-label {
    font-size: 8px;
    color: var(--gba-text-dim);
  }

  .step__field input,
  .step__field textarea {
    width: 100%;
    font-size: 9px;
  }

  .intensity-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .intensity-option {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px;
    text-align: left;
    background: var(--gba-surface-alt);
    border: 2px solid var(--gba-border);
  }

  .intensity-option:hover {
    border-color: var(--gba-accent-dim);
  }

  .intensity-option.selected {
    border-color: var(--gba-accent);
    background: var(--gba-accent-dim);
  }

  .intensity-option__label {
    font-size: 10px;
    color: var(--gba-text);
  }

  .intensity-option__desc {
    font-size: 7px;
    line-height: 1.3;
  }

  .template-info {
    font-size: 8px;
    padding: 6px 8px;
    background: var(--gba-bg);
    border: 1px solid var(--gba-border);
  }

  .confirm-grid {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .confirm-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 8px;
    padding: 4px 0;
    border-bottom: 1px solid var(--gba-border);
  }

  .step__error {
    font-size: 8px;
    padding: 8px;
    background: rgba(244, 67, 54, 0.1);
    border: 1px solid var(--gba-red);
  }

  .intake__nav {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  @media (max-width: 600px) {
    .intensity-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
