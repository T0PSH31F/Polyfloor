# NFP Integration Handoff

## Context

Polyfloor is designed to integrate into `T0PSH31F/NFP` — a flake-parts + clan-core NixOS configuration managing two machines:

- **luffy**: Desktop — meta/interactive services, Hyprland/UWSM, Noctalia
- **z0r0**: Laptop — worker/autonomous services

## Integration Steps

### 1. Add Polyfloor as a Flake Input

In `~/Clan/NFP/flake.nix`:

```nix
inputs.polyfloor = {
  url = "github:T0PSH31F/Polyfloor";
  inputs.nixpkgs.follows = "nixpkgs";
  inputs.flake-parts.follows = "flake-parts";
  inputs.systems.follows = "systems";
};
```

### 2. Import the Module

Create a new layer file (e.g., `layers/20-services/22-ai/polyfloor.nix`):

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
    # Do NOT set manageDatabase=true — use NFP's shared PostgreSQL
    database.manageDatabase = false;
    # Do NOT set persistence.enable — NFP manages impermanence
  };
}
```

### 3. Configure Secrets via SOPS

Add to your SOPS-encrypted secrets file:

```yaml
# In secrets/external_services.yaml
polyfloor_api_token: <secure-token>
```

Create a SOPS template in your NFP config:

```nix
sops.templates."polyfloor-env" = {
  content = ''
    POLYFLOOR_DATABASE_DSN=postgresql://polyfloor:${config.sops.placeholder.postgres-password}@localhost:5432/polyfloor
    POLYFLOOR_API_TOKEN=${config.sops.placeholder.polyfloor_api_token}
  '';
  owner = "polyfloor";
  group = "polyfloor";
  mode = "0400";
};
```

Wire to the service:

```nix
tower.backend.environmentFile = config.sops.templates."polyfloor-env".path;
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
psql -U polyfloor -d polyfloor -f db/migrations/002_digital_production_studio.sql
```

### 5. Configure Persistence

Use NFP's existing impermanence configuration:

```nix
environment.persistence."/persist".directories = [
  { directory = "/var/lib/polyfloor"; user = "polyfloor"; group = "polyfloor"; mode = "0750"; }
];
```

Do NOT set `tower.persistence.enable = true` — NFP controls impermanence through its own layer.

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
