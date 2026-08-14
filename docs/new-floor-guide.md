# Adding a New Floor

## 1. Create a Nix Template

Create `floors/templates/<name>.nix`:

```nix
{ config, lib, ... }:
with lib;
{
  tower.floors.<name> = {
    enable        = true;
    displayName   = "My Floor";
    email         = "<name>@polyfloor.local";
    orgName       = "<name>";
    timezone      = "America/Los_Angeles";
    targetMachine = "luffy";
    dbSchema      = "floor_<name>";
    template      = "<template-type>";

    roles = {
      lead = {
        model       = "free://best-reasoning";
        description = "Floor lead";
      };
      worker = {
        model       = "free://best-fast";
        description = "Floor worker";
      };
    };

    dailyBudgetUSD = 0.0;
    persistPaths   = [ "outputs" "sessions" "sprint-board" ];
  };
}
```

## 2. Register in flake-module.nix

Add to `flake.clan.modules`:

```nix
floor-<name> = ./floors/templates/<name>.nix;
```

## 3. Run Database Migration

The floor configuration is stored in `tower.floor_configs`. Insert via API or directly:

```sql
INSERT INTO tower.floor_configs (id, display_name, org_name, db_schema, template)
VALUES ('<name>', 'My Floor', '<name>', 'floor_<name>', '<template-type>');
```

## 4. Configure Roles via API

```bash
curl -X PUT http://127.0.0.1:8001/api/v1/floors/<name>/roles/lead \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model": "free://best-reasoning", "description": "Floor lead"}'
```

## 5. Set Up Output Directory

The output service automatically creates `<output_root>/<floor_id>/outputs/` on first write.

## 6. Test

```bash
curl http://127.0.0.1:8001/api/v1/floors/<name>
```
