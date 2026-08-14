<script lang="ts">
  import { onMount } from "svelte";
  import { loadFloors } from "$lib/stores/floors";
  import { subscribeEvents, unsubscribeEvents } from "$lib/stores/events";
  import type { Snippet } from "svelte";

  let { children }: { children: Snippet } = $props();

  onMount(() => {
    loadFloors();
    subscribeEvents();
    return () => unsubscribeEvents();
  });
</script>

<nav class="nav">
  <a href="/" class="nav__brand">Polyfloor</a>
  <div class="nav__links">
    <a href="/">Reception</a>
    <a href="/floors">Floors</a>
    <a href="/sprint-board">Sprint Board</a>
    <a href="/events">Event Log</a>
  </div>
</nav>

<main class="container">
  {@render children()}
</main>

<style>
  .nav {
    display: flex;
    align-items: center;
    gap: 2rem;
    padding: 0.75rem 1.5rem;
    background: #2d3748;
    border-bottom: 1px solid #4a5568;
  }

  .nav__brand {
    font-family: monospace;
    font-size: 1.25rem;
    font-weight: 700;
    color: #63b3ed;
    text-decoration: none;
  }

  .nav__links {
    display: flex;
    gap: 1.5rem;
  }

  .nav__links a {
    color: #a0aec0;
    font-size: 0.875rem;
    text-decoration: none;
  }

  .nav__links a:hover {
    color: #e2e8f0;
    text-decoration: none;
  }
</style>
