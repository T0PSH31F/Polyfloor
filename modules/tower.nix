{ config, lib, pkgs, ... }:
with lib;
let cfg = config.tower; in
{
  imports = [ ./floor-base.nix ];

  options.tower = {
    enable  = mkEnableOption "Polyfloor Tower";
    dataDir = mkOption {
      type = types.path;
      default = "/var/lib/polyfloor";
      description = "Root data directory for Polyfloor";
    };

    backend = {
      enable = mkEnableOption "Polyfloor FastAPI backend service" // { default = true; };
      package = mkOption {
        type = types.package;
        default = pkgs.polyfloor or (pkgs.callPackage ../backend/package.nix {});
        description = "Packaged Polyfloor backend executable";
      };
      host = mkOption {
        type = types.str;
        default = "127.0.0.1";
        description = "Host to bind the backend to (loopback by default)";
      };
      port = mkOption {
        type = types.port;
        default = 8001;
        description = "Port for the backend HTTP server";
      };
      environmentFile = mkOption {
        type = types.nullOr types.path;
        default = null;
        description = "Path to environment file with secrets (e.g. SOPS-generated)";
      };
      logLevel = mkOption {
        type = types.enum [ "debug" "info" "warning" "error" "critical" ];
        default = "info";
        description = "Backend log level";
      };
    };

    database = {
      host = mkOption {
        type = types.str;
        default = "127.0.0.1";
        description = "PostgreSQL host";
      };
      port = mkOption {
        type = types.port;
        default = 5432;
        description = "PostgreSQL port";
      };
      name = mkOption {
        type = types.str;
        default = "polyfloor";
        description = "PostgreSQL database name";
      };
      user = mkOption {
        type = types.str;
        default = "polyfloor";
        description = "PostgreSQL user";
      };
      manageDatabase = mkOption {
        type = types.bool;
        default = false;
        description = ''
          Whether to create the database and user via services.postgresql.
          Disable when using an existing shared PostgreSQL instance (e.g. NFP).
          NFP will provision the DB/user through its own mechanism.
        '';
      };
    };

    persistence = {
      enable = mkEnableOption ''
        Impermanence persistence for Polyfloor data.
        Only enable if your NixOS config imports impermanence.
        NFP manages this through its own layer — do not enable here.
      '';
      mountPoint = mkOption {
        type = types.path;
        default = "/persist";
        description = "Impermanence mount point";
      };
    };
  };

  config = mkIf cfg.enable {
    assertions = [
      {
        assertion = cfg.database.manageDatabase -> (cfg.database.host == "127.0.0.1" || cfg.database.host == "localhost");
        message = "tower.database.manageDatabase only works with local PostgreSQL. Set manageDatabase=false for remote DBs.";
      }
    ];

    # ── Data directories ──────────────────────────────────────────────
    systemd.tmpfiles.rules = [
      "d ${cfg.dataDir}            0750 polyfloor polyfloor -"
      "d ${cfg.dataDir}/floors     0750 polyfloor polyfloor -"
      "d ${cfg.dataDir}/outputs    0750 polyfloor polyfloor -"
      "d ${cfg.dataDir}/logs       0750 polyfloor polyfloor -"
    ];

    # ── System user ───────────────────────────────────────────────────
    users.users.polyfloor = {
      isSystemUser = true;
      group = "polyfloor";
      home = cfg.dataDir;
      description = "Polyfloor service user";
    };
    users.groups.polyfloor = {};

    # ── PostgreSQL (opt-in) ───────────────────────────────────────────
    services.postgresql = mkIf cfg.database.manageDatabase {
      ensureUsers = [{
        name = cfg.database.user;
        ensureDBOwnership = true;
      }];
      ensureDatabases = [ cfg.database.name ];
    };

    # ── Impermanence persistence (opt-in) ─────────────────────────────
    environment.persistence."${cfg.persistence.mountPoint}" = mkIf cfg.persistence.enable {
      directories = [{
        directory = cfg.dataDir;
        user = "polyfloor";
        group = "polyfloor";
        mode = "0750";
      }];
    };

    # ── Backend systemd service ───────────────────────────────────────
    systemd.services.polyfloor-backend = mkIf cfg.backend.enable {
      description = "Polyfloor FastAPI backend";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      environment = {
        POLYFLOOR_HOST = cfg.backend.host;
        POLYFLOOR_PORT = toString cfg.backend.port;
        POLYFLOOR_LOG_LEVEL = cfg.backend.logLevel;
        POLYFLOOR_OUTPUT_ROOT = "${cfg.dataDir}/floors";
      };

      serviceConfig = {
        # Execution
        ExecStart = "${cfg.backend.package}/bin/polyfloor";
        Restart = "on-failure";
        RestartSec = "5s";

        # User isolation
        User = "polyfloor";
        Group = "polyfloor";
        WorkingDirectory = cfg.dataDir;

        # Secrets
        EnvironmentFile = mkIf (cfg.backend.environmentFile != null) cfg.backend.environmentFile;

        # Hardening
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ cfg.dataDir ];
        StateDirectory = "polyfloor";

        # Network — bind to loopback only; no unnecessary exposure
        IPAddressAllow = [ "127.0.0.1" "::1" ];

        # Capabilities
        CapabilityBoundingSet = "";
        AmbientCapabilities = "";
        ProtectKernelTunables = true;
        ProtectKernelModules = true;
        ProtectControlGroups = true;
        RestrictNamespaces = true;
        RestrictRealtime = true;
        LockPersonality = true;
        MemoryDenyWriteExecute = true;
      };
    };
  };
}
