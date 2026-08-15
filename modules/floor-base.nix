{ lib, ... }:
with lib;
{
  options.tower.floors = mkOption {
    default = {};
    type = types.attrsOf (types.submodule ({ name, config, ... }: {
      options = {
        enable        = mkEnableOption "Tower floor '${name}'";
        displayName   = mkOption { type = types.str; description = "Human-readable floor name"; };
        email         = mkOption { type = types.nullOr types.str; default = null; description = "Floor contact email"; };
        orgName       = mkOption { type = types.str; default = name; description = "Organization identifier"; };
        timezone      = mkOption { type = types.str; default = "America/Los_Angeles"; description = "Floor timezone"; };
        targetMachine = mkOption {
          type = types.nullOr types.str;
          default = null;
          description = "Target machine metadata for deployment routing (not enforced by this module)";
        };
        dbSchema      = mkOption { type = types.str; default = "floor_${name}"; description = "Database schema for this floor"; };
        mcps          = mkOption { type = types.listOf types.str; default = []; description = "MCP servers for this floor"; };
        template      = mkOption {
          type = types.nullOr (types.enum [
            "digital-production" "marketing" "research" "dev" "customer-service" "finance" "custom"
          ]);
          default = null;
          description = "Floor template preset";
        };
        roles = mkOption {
          default = {};
          type = types.attrsOf (types.submodule {
            options = {
              enable      = mkOption { type = types.bool;   default = true; description = "Whether this role is active"; };
              model       = mkOption { type = types.str;    default = "free://best-reasoning"; description = "Model routing spec"; };
              maxTokens   = mkOption { type = types.int;    default = 8192; description = "Max tokens per model call"; };
              description = mkOption { type = types.str;    default = ""; description = "Role description"; };
            };
          });
          description = "Role configurations for this floor";
        };
        paidModelsAllowed = mkOption {
          type = types.bool;
          default = false;
          description = "Allow paid models for this floor (requires POLYFLOOR_ALLOW_PAID_MODELS=true globally too)";
        };
        dailyBudgetUSD = mkOption {
          type = types.float;
          default = 0.0;
          description = "Daily budget cap in USD for paid models";
        };
        persistPaths = mkOption {
          type = types.listOf types.str;
          default = [ "outputs" "sessions" "sprint-board" ];
          description = "Paths to persist under the floor's data directory";
        };
      };
    }));
  };
}
