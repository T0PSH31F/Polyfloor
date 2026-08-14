# NFP Integration Handoff

## Context

Polyfloor is designed to integrate into `T0PSH31F/NFP` — a flake-parts + clan-core NixOS configuration managing two machines:

- **luffy**: Desktop — meta/interactive services, Hyprland/UWSM, Noctalia
- **z0r0**: Laptop — worker/autonomous services

## Integration Steps

### 1. Add Polyfloor as a Flake Input

In `~/Clan/NFP/flake.nix`:

```nix
inputs.polyfloor.url = "github:T0PSH31F/polyfloor";
```

### 2. Import the Module

Create a new layer file (e.g., `layers/30-services/32-polyfloor/polyfloor.nix`):

```nix
{ inputs, ... }: {
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

### 3. Configure Secrets via SOPS

Add to your SOPS configuration:

```yaml
# In secrets/polyfloor.yaml
POLYFLOOR_DATABASE_DSN: "postgresql://polyfloor:<password>@localhost:5432/polyfloor"
POLYFLOOR_API_TOKEN: "<secure-token>"
POLYFLOOR_EXTREMEROUTER_API_KEY: "<api-key>"
```

Wire to the service:

```nix
tower.backend.environmentFile = config.sops.secrets.polyfloor-env.path;
```

### 4. Use Existing PostgreSQL

luffy has an existing shared PostgreSQL service. Polyfloor must use a separate DB/user without replacing or blindly enabling another PostgreSQL instance.

Provision through NFP's existing PostgreSQL mechanism:

```sql
CREATE USER polyfloor WITH PASSWORD '<from-sops>';
CREATE DATABASE polyfloor OWNER polyfloor;
```

Run migrations:

```bash
psql -U polyfloor -d polyfloor -f db/migrations/001_tower_core.sql
```

### 5. Configure Persistence

Use NFP's existing impermanence configuration:

```nix
environment.persistence."/persist".directories = [
  { directory = "/var/lib/polyfloor"; user = "polyfloor"; group = "polyfloor"; mode = "0750"; }
];
```

Do NOT rely on unconditional module declarations — the parent NFP config controls impermanence.

### 6. Reverse Proxy

Bind backend to loopback. Place any reverse proxy route in NFP's existing Caddy setup deliberately:

```nix
# In Caddy config
"polyfloor.local" {
  reverse_proxy 127.0.0.1:8001
}
```

### 7. Machine Placement

Start with one floor enabled on luffy. Optionally use z0r0 later for worker floors.

The `targetMachine` field is metadata — it does not deploy services remotely by itself.

### 8. Build and Test

```bash
# Build without switching
nixos-rebuild build --flake .#luffy

# Verify service
systemctl status polyfloor-backend
curl http://127.0.0.1:8001/healthz
```

## Important Notes

- **No Wayland variables** in the backend systemd service — it's headless
- **No second PostgreSQL** — use the existing shared instance
- **No unconditional impermanence** — use NFP's existing pattern
- **ExtremeRouter URL** is an explicit NFP secret/config value, not hardcoded
- Polyfloor backend runs as a system service, not a user service

## Files to Import

From the Polyfloor flake:
- `nixosModules.polyfloor` — main tower module
- `nixosModules.floor-base` — floor base options
- `clan.modules.*` — clan integration (optional)
