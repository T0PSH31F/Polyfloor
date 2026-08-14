# Polyfloor — Agent Instructions

## Working in This Repository

### Before Committing

Run all checks:
```bash
just check
```

This includes formatting, linting, type checking, unit tests, and Nix flake evaluation.

### Never Do These

- Add secrets, API keys, passwords, or tokens to source code
- Silently relax authentication or authorization gates
- Add Wayland/GUI environment variables to system services
- Assume specific ExtremeRouter model IDs without documenting them as configurable aliases
- Modify NixOS/flake integration assumptions without updating docs and tests
- Create a second PostgreSQL service by default
- Implement automatic publishing, spending, or command execution

### Always Do These

- Use free-first model routing defaults
- Follow the `src/` Python layout
- Use Svelte 5 idioms (not Svelte 4)
- Validate task status transitions server-side
- Require human approval for external side effects
- Keep static (Nix) and runtime (DB/API) configuration separate
- Bind backend services to loopback by default
- Use parameterized queries (never raw SQL)

### Code Style

**Python:**
- Ruff for formatting and linting
- mypy for type checking
- pytest for tests
- asyncpg for database access
- Pydantic for models and settings

**Svelte/TypeScript:**
- Prettier for formatting
- ESLint for linting
- svelte-check for type checking
- Vitest for tests
- Svelte 5 runes ($state, $derived, $effect)

**Nix:**
- nixfmt for formatting
- flake-parts for structure

### Architecture Boundaries

- **Static layer** (Nix): floor existence, service enablement, filesystem, persistence
- **Runtime layer** (DB/API): roles, prompts, model routing, tasks, approvals
- Agents modify runtime config through the API, never by editing Nix files
- Each floor has isolated output paths, DB schemas, and API scopes

### Testing

Backend tests use mocks for database and model providers. A test database integration suite is optional and requires `POLYFLOOR_TEST_DATABASE_DSN`.

Frontend tests cover event stores, Phaser bridge behavior, and task grouping helpers without requiring WebGL.
