# Deployment

## NixOS module

Import the Polyfloor module into your NixOS configuration:

```nix
{
  inputs.polyfloor.url = "github:T0PSH31F/Polyfloor";

  imports = [ inputs.polyfloor.nixosModules.default ];

  services.polyfloor = {
    enable = true;
    package = inputs.polyfloor.packages.${system}.default;
    host = "127.0.0.1";
    port = 8001;
    dataDir = "/var/lib/polyfloor";
    routerEndpoint = "http://127.0.0.1:4000/v1"; # Kong / Extreme Router / LiteLLM
    defaultHrModel = "mimo-v2.5-pro";
    environmentFile = config.sops.secrets.polyfloor-env.path;
  };
}
```

`nixosModules.default` is `modules/nixos/polyfloor.nix` — a hardened systemd
service (`DynamicUser`, `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp`,
`NoNewPrivileges`, `StateDirectory=polyfloor`).

## Quick run (no NixOS config)

```bash
nix run github:T0PSH31F/Polyfloor         # backend :8001 + served SPA
nix profile install github:T0PSH31F/Polyfloor
```

## Database

Polyfloor uses **SQLite WAL** by default so a fresh run needs zero external
services. For PostgreSQL, set `POLYFLOOR_DATABASE_URL` in the environment file:

```
POLYFLOOR_DATABASE_URL=postgresql://polyfloor:<password>@localhost:5432/polyfloor
```

## Secrets (sops)

Never put secrets in the module config or env vars. Use a sops-managed
`environmentFile`:

```nix
services.polyfloor.environmentFile = config.sops.secrets.polyfloor-env.path;
```

The env file may contain:

```
POLYFLOOR_ROUTER_API_KEY_FILE=/run/secrets/polyfloor-router-key
POLYFLOOR_API_TOKEN_FILE=/run/secrets/polyfloor-api-token
POLYFLOOR_DATABASE_URL=postgresql://polyfloor:<password>@localhost:5432/polyfloor
```

Secrets are read from **file paths** (`*_FILE`) so they never appear in the
process environment or logs.

## Health check

```bash
curl http://127.0.0.1:8001/healthz   # → {"status":"ok"}
curl http://127.0.0.1:8001/metrics  # → Prometheus text
```

## Persistence

Configure impermanence for `/var/lib/polyfloor` in your NixOS config:

```nix
environment.persistence."/persist".directories = [
  { directory = "/var/lib/polyfloor"; user = "polyfloor"; group = "polyfloor"; mode = "0750"; }
];
```

## Reverse proxy

The backend binds to `127.0.0.1` by default. Put a reverse proxy (Caddy, nginx)
with TLS and auth in front for remote access; do not expose the API directly.
