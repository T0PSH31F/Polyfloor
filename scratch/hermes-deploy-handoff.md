# Polyfloor Deployment Handoff — Hermes-Agent on z0r0

## Mission

Deploy Polyfloor (multi-floor AI company OS) on z0r0. The Nix module is already configured in NFP. You need to: create the PostgreSQL database, run migrations, verify the service, and test the API.

## Context

- **Repo:** `T0PSH31F/Polyfloor` (already a flake input in NFP)
- **NFP config:** `~/Clan/NFP/machines/z0r0/default.nix` already has `ai-services.polyfloor.enable = true`
- **SOPS secret:** `polyfloor_api_token` already exists in `layers/00-cyberia/03-treasure/secrets/external_services.yaml`
- **SOPS template:** `polyfloor-env` template exists in `layers/20-services/22-ai/polyfloor-secrets.nix`

## Steps

### 1. Build the NixOS configuration

```bash
cd ~/Clan/NFP
nixos-rebuild build --flake .#z0r0
```

If this fails, report the exact error. Common issues:
- Missing `polyfloor_api_token` in SOPS secrets → run `sops layers/00-cyberia/03-treasure/secrets/external_services.yaml` and add it
- PostgreSQL not running → `systemctl start postgresql`

### 2. Switch to the new configuration

```bash
sudo nixos-rebuild switch --flake .#z0r0
```

### 3. Verify the service is running

```bash
systemctl status polyfloor-backend
journalctl -u polyfloor-backend -n 50 --no-pager
```

The service should be `active (running)`. If it fails, check logs for:
- Missing environment file → SOPS template not rendering
- Port conflict → change `ai-services.polyfloor.port` in z0r0 config
- PostgreSQL connection → ensure DB exists (step 4)

### 4. Create PostgreSQL database and user

```bash
sudo -u postgres psql -c "CREATE USER polyfloor WITH PASSWORD 'from-sops';"
sudo -u postgres psql -c "CREATE DATABASE polyfloor OWNER polyfloor;"
```

Or if you prefer to get the password from SOPS:

```bash
cd ~/Clan/NFP
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops --decrypt layers/00-cyberia/03-treasure/secrets/postgres.yaml | grep postgres-password
```

Use that password in the CREATE USER command.

### 5. Run database migrations

```bash
# Get the Polyfloor source
POLYFLOOR_SRC=$(nix build ~/Clan/NFP#nixosConfigurations.z0r0.config.services.ai-services.polyfloor.package --print-out-paths 2>/dev/null || echo "")

# If no package, use the git source
cd /tmp
git clone https://github.com/T0PSH31F/Polyfloor.git polyfloor-migrations 2>/dev/null || true
cd polyfloor-migrations

# Run migrations
psql -U polyfloor -d polyfloor -h localhost -f db/migrations/001_tower_core.sql
psql -U polyfloor -d polyfloor -h localhost -f db/migrations/002_digital_production_studio.sql
```

If `psql` asks for password, use the one from SOPS secrets.

### 6. Verify API is responding

```bash
# Health check
curl -s http://127.0.0.1:8001/healthz

# Get the API token from SOPS
cd ~/Clan/NFP
TOKEN=$(SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops --decrypt layers/00-cyberia/03-treasure/secrets/external_services.yaml | grep polyfloor_api_token | awk '{print $2}')

# Test authenticated endpoint
curl -s http://127.0.0.1:8001/api/v1/floors -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# List floors (should show production, research, dev, marketing, customer-service)
curl -s http://127.0.0.1:8001/api/v1/floors -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | grep '"id"'

# List production floor roles
curl -s http://127.0.0.1:8001/api/v1/floors/production/roles -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

### 7. Create a test task

```bash
curl -s -X POST http://127.0.0.1:8001/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "floor_id": "production",
    "title": "Test task: Verify Polyfloor deployment",
    "description": "Confirm all systems operational",
    "assigned_role": "orchestrator"
  }' | python3 -m json.tool
```

### 8. Report results

Report back:
- Did `nixos-rebuild build` succeed?
- Did `nixos-rebuild switch` succeed?
- Is `polyfloor-backend.service` active?
- Did migrations run successfully?
- Does `/healthz` return `{"status":"ok"}`?
- How many floors are listed?
- How many roles does the production floor have?
- Did the test task creation succeed?

## Troubleshooting

### Service won't start
```bash
journalctl -u polyfloor-backend -n 100 --no-pager
```

### Database connection refused
```bash
systemctl status postgresql
sudo -u postgres psql -c "SELECT 1"
```

### SOPS decryption fails
```bash
cd ~/Clan/NFP
SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt sops --decrypt layers/00-cyberia/03-treasure/secrets/external_services.yaml | head -5
```

If this fails, check that the age key exists at `~/.config/sops/age/keys.txt`.

### Port conflict
```bash
ss -tlnp | grep 8001
```

If port 8001 is in use, change `ai-services.polyfloor.port` in `~/Clan/NFP/machines/z0r0/default.nix` and rebuild.

## Files Reference

| File | Purpose |
|------|---------|
| `~/Clan/NFP/machines/z0r0/default.nix` | Machine config (polyfloor enabled here) |
| `~/Clan/NFP/layers/20-services/22-ai/polyfloor.nix` | Service module |
| `~/Clan/NFP/layers/20-services/22-ai/polyfloor-secrets.nix` | SOPS template |
| `~/Clan/NFP/layers/00-cyberia/03-treasure/secrets/external_services.yaml` | API token |
| `~/Clan/NFP/layers/00-cyberia/03-treasure/secrets/postgres.yaml` | DB password |
| `~/Clan/NFP/db/migrations/001_tower_core.sql` | Core schema |
| `~/Clan/NFP/db/migrations/002_digital_production_studio.sql` | Floor seeds |
