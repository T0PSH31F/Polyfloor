# Polyfloor

**Multi-floor AI company OS.** Autonomous agent teams as isolated NixOS-native departments.

> **Status:** Initial scaffold / development. Not production-ready autonomous business software.

## What is Polyfloor?

Polyfloor organizes an AI company into independent "floors" — each floor is an isolated department with its own roles, tasks, budgets, and approval gates. Agents work autonomously within their floor, but all external side effects require human approval.

## Architecture

```
┌─────────────────────────────────────────┐
│              Polyfloor Tower             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Production│ │Marketing│ │Research │   │
│  │  Floor   │ │  Floor  │ │  Floor  │   │
│  └────┬─────┘ └────┬────┘ └────┬────┘   │
│       │            │           │         │
│  ┌────┴────────────┴───────────┴────┐    │
│  │         FastAPI Backend          │    │
│  │   Auth → Router → Event Bus      │    │
│  └──────────────┬───────────────────┘    │
│                 │                         │
│  ┌──────────────┴───────────────────┐    │
│  │          PostgreSQL               │    │
│  │   tower.* schemas per floor       │    │
│  └───────────────────────────────────┘    │
│                                           │
│  ┌───────────────────────────────────┐    │
│  │      SvelteKit + Phaser Frontend   │    │
│  │   Reception · Sprint Board · Events │    │
│  └───────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Free-First Model Routing

Polyfloor uses **ExtremeRouter** for free model access by default:

- `free://best-reasoning` — complex analysis and planning
- `free://best-fast` — quick tasks and responses
- `hermes:<model>` — local Ollama/Hermes execution
- `paid://<model>` — requires explicit global + floor opt-in

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Nix (optional, for NixOS integration)

### Development

```bash
# Backend
cd backend
uv sync
uv run uvicorn polyfloor.main:app --reload --host 127.0.0.1 --port 8001

# Frontend
cd frontend
npm install
npm run dev
```

### Running Checks

```bash
just check
```

## NixOS Module Usage

```nix
{
  imports = [ inputs.polyfloor.nixosModules.polyfloor ];

  tower = {
    enable = true;
    dataDir = "/var/lib/polyfloor";
    backend = {
      enable = true;
      host = "127.0.0.1";
      port = 8001;
    };
  };
}
```

## Security

> [!WARNING]
> Do NOT expose Polyfloor API endpoints directly to public networks beyond localhost/LAN without database-backed token management (`ApiToken`) configured and TLS enabled.

- Bearer token authentication (database-backed tokens with expiration, revocation, and audit trail)
- Role-based authorization (`human_admin`, `hr`, `orchestrator`, `worker`, `readonly`)
- Floor-scoped access control
- Path traversal prevention for file outputs
- Approval gates for external side effects
- Append-only audit trail

## Graph Architecture vs NFP Supergraph

- **Polyfloor Graph (`polyfloor/graph`)**: Departmental task workflow state machine with human-in-the-loop approval gates.
- **NFP Supergraph (`.supergraph/`)**: Sibling project (`NFP`) visualizer for Nix module dependency imports and dendritic architecture layers. They serve distinct, non-overlapping domains.

## Documentation

- [Architecture](docs/architecture.md)
- [Adding a New Floor](docs/new-floor-guide.md)
- [Team Board](docs/team-board.md)
- [Deployment](docs/deployment.md)
- [Security](docs/security.md)
- [Model Routing](docs/model-routing.md)
- [OpenCode Integration](docs/opencode-integration.md)
