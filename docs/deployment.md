# Deployment

## NixOS Module Usage

Import the Polyfloor module into your NixOS configuration:

```nix
# In your flake.nix
inputs.polyfloor.url = "github:T0PSH31F/polyfloor";

# In your NixOS configuration
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

## Database Setup

Polyfloor uses an existing PostgreSQL instance. It does not manage PostgreSQL itself.

1. Create the database and user:
```sql
CREATE USER polyfloor WITH PASSWORD '<secure-password>';
CREATE DATABASE polyfloor OWNER polyfloor;
```

2. Run migrations:
```bash
psql -U polyfloor -d polyfloor -f db/migrations/001_tower_core.sql
```

## Secrets

Use SOPS + age for secret management:

```nix
tower.backend.environmentFile = config.sops.secrets.polyfloor-env.path;
```

Example `.env` file (encrypted with SOPS):
```
POLYFLOOR_DATABASE_DSN=postgresql://polyfloor:<password>@localhost:5432/polyfloor
POLYFLOOR_API_TOKEN=<secure-token>
POLYFLOOR_EXTREMEROUTER_API_KEY=<api-key>
```

## Health Check

```bash
curl http://127.0.0.1:8001/healthz
```

## Persistence

Configure impermanence for `/var/lib/polyfloor` in your NixOS config:

```nix
environment.persistence."/persist".directories = [
  { directory = "/var/lib/polyfloor"; user = "polyfloor"; group = "polyfloor"; mode = "0750"; }
];
```
