<script lang="ts">
  import "../app.css";
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();
</script>

<div class="gba-shell">
  <div class="gba-shell__inner">
    {@render children()}
  </div>
</div>

<style>
  .gba-shell {
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 16px;
    background: var(--gba-bg);
  }

  .gba-shell__inner {
    width: 100%;
    max-width: 980px;
  }
</style>
