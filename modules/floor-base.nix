{ lib, ... }:
with lib;
{
  options.tower.floors = mkOption {
    default = {};
    type = types.attrsOf (types.submodule ({ name, config, ... }: {
      options = {
        enable        = mkEnableOption "Tower floor '${name}'";
        displayName   = mkOption { type = types.str; };
        email         = mkOption { type = types.str; };
        orgName       = mkOption { type = types.str; default = name; };
        timezone      = mkOption { type = types.str; default = "America/Los_Angeles"; };
        targetMachine = mkOption { type = types.enum [ "luffy" "z0r0" ]; default = "luffy"; };
        dbSchema      = mkOption { type = types.str; default = "floor_${name}"; };
        mcps          = mkOption { type = types.listOf types.str; default = []; };
        template      = mkOption {
          type = types.nullOr (types.enum [
            "digital-production" "marketing" "research" "dev" "customer-service" "finance" "custom"
          ]);
          default = null;
        };
        roles = mkOption {
          default = {};
          type = types.attrsOf (types.submodule {
            options = {
              enable      = mkOption { type = types.bool;   default = true; };
              model       = mkOption { type = types.str;    default = "free://best-reasoning"; };
              maxTokens   = mkOption { type = types.int;    default = 8192; };
              description = mkOption { type = types.str;    default = ""; };
            };
          });
        };
        dailyBudgetUSD = mkOption { type = types.float;           default = 0.0; };
        persistPaths   = mkOption { type = types.listOf types.str; default = []; };
      };
    }));
  };
}
