# Polyfloor Architecture

## Overview

Polyfloor is a multi-floor AI company OS — each "floor" is an isolated AI department with its own roles, tasks, budgets, and approval gates.

## Static vs Runtime Configuration

| Layer                | Managed By              | Examples                                                                                 |
| -------------------- | ----------------------- | ---------------------------------------------------------------------------------------- |
| **Static (Nix)**     | `nixos-rebuild switch`  | Floor existence, service enablement, filesystem ownership, persistence, deployment shape |
| **Runtime (DB/API)** | HR/admin agents via API | Roles, prompts, model routing, tasks, sprint board, agent memory, approvals              |

The static layer defines _what floors exist_ and _how services run_. The runtime layer defines _how floors behave_ and _what work happens_. This separation lets agents modify floor behavior without NixOS rebuilds.

## Data Flow

```
User/Agent → FastAPI (auth) → PostgreSQL (tower.*)
                ↓
          Event Bus → SSE → Frontend (SvelteKit + Phaser)
```

## Model Routing

Free-first by default:

1. **Local Hermes/Ollama** — `hermes:<model>` for local execution
1. **ExtremeRouter** — `free://best-reasoning`, `free://best-fast` (default)
1. **Paid models** — `paid://gpt-4o` (requires global + floor opt-in)

## Approval Gate

All external side effects require human approval:

- Publishing content
- Sending emails
- Spending money
- Changing secrets/Nix configuration

Agents create approval requests; humans resolve them through the API or frontend.

## Floor Isolation

Each floor gets:

- Dedicated DB schema (`floor_<name>`)
- Isolated output directory (`<output_root>/<floor_id>/outputs/`)
- Independent role configuration
- Separate budget tracking
- Scoped API access

## Persistence

Static config lives in Nix modules. Runtime state persists in PostgreSQL. Floor outputs persist under the configured output root. Impermanence integration is optional and controlled by the parent NixOS configuration.

## Future: Clan Migration

Floors can evolve from NixOS modules to dedicated clan machines with minimal rewrite. The `targetMachine` field is metadata today but can become an enforcement point later.
