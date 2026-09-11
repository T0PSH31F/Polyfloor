# Polyfloor — NixOS service module
#
# `services.polyfloor` runs the FastAPI backend (which also serves the built
# SvelteKit SPA when `staticDir` is set). Hardened systemd sandbox per SPEC §11.
{
  config,
  lib,
  pkgs,
  ...
}:

with lib;

let
  cfg = config.services.polyfloor;
in
{
  options.services.polyfloor = {
    enable = mkEnableOption "Polyfloor — autonomous multi-company enterprise engine";

    package = mkOption {
      type = types.package;
      default = pkgs.callPackage ../../pkgs/backend.nix { };
      description = "The Polyfloor package to run (backend + optional frontend).";
    };

    host = mkOption {
      type = types.str;
      default = "127.0.0.1";
      description = "Host IP address to bind the service to.";
    };

    port = mkOption {
      type = types.port;
      default = 8080;
      description = "Port for the backend HTTP server.";
    };

    dataDir = mkOption {
      type = types.path;
      default = "/var/lib/polyfloor";
      description = "Data directory for per-company workspaces, avatars, and the SQLite DB.";
    };

    openFirewall = mkOption {
      type = types.bool;
      default = false;
      description = "Whether to open the HTTP port in the firewall.";
    };

    environmentFile = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Path to an environment file containing secrets (e.g. router API key file paths). SOPS-managed.";
    };

    # --- Model router (SPEC §9.2) ---
    routerEndpoint = mkOption {
      type = types.str;
      default = "http://127.0.0.1:4000/v1";
      description = ''
        OpenAI-compatible router base URL (Kong / Extreme Router / LiteLLM).
        Polyfloor enumerates models via `GET {routerEndpoint}/models`.
      '';
    };

    defaultHrModel = mkOption {
      type = types.str;
      default = "mimo-v2.5-pro";
      description = "Default model id for the HR coordinator agent.";
    };

    # --- Frontend ---
    staticDir = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Directory of the built SvelteKit SPA to serve. Null = API only.";
    };

    logLevel = mkOption {
      type = types.enum [
        "debug"
        "info"
        "warning"
        "error"
        "critical"
      ];
      default = "info";
      description = "Backend log level.";
    };
  };

  config = mkIf cfg.enable {
    users.users.polyfloor = {
      isSystemUser = true;
      group = "polyfloor";
      home = cfg.dataDir;
      createHome = true;
      description = "Polyfloor service user";
    };

    users.groups.polyfloor = { };

    networking.firewall.allowedTCPPorts = mkIf cfg.openFirewall [ cfg.port ];

    systemd.services.polyfloor = {
      description = "Polyfloor Service Daemon";
      wantedBy = [ "multi-user.target" ];
      after = [ "network.target" ];

      environment = {
        POLYFLOOR_HOST = cfg.host;
        POLYFLOOR_PORT = toString cfg.port;
        POLYFLOOR_DATA_DIR = "${cfg.dataDir}";
        # SQLite WAL by default — zero external services required.
        POLYFLOOR_DATABASE_URL = "sqlite+aiosqlite://${cfg.dataDir}/polyfloor.db";
        POLYFLOOR_ROUTER_ENDPOINT = cfg.routerEndpoint;
        POLYFLOOR_DEFAULT_HR_MODEL = cfg.defaultHrModel;
        POLYFLOOR_LOG_LEVEL = cfg.logLevel;
      } // optionalAttrs (cfg.staticDir != null) {
        POLYFLOOR_STATIC_DIR = "${cfg.staticDir}";
      };

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/polyfloor";
        Restart = "on-failure";
        RestartSec = "5s";

        DynamicUser = true;
        WorkingDirectory = cfg.dataDir;

        EnvironmentFile = mkIf (cfg.environmentFile != null) cfg.environmentFile;

        # Hardening sandbox primitives (SPEC §11).
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ cfg.dataDir ];
        StateDirectory = "polyfloor";

        CapabilityBoundingSet = "";
        AmbientCapabilities = "";
        ProtectKernelTunables = true;
        ProtectKernelModules = true;
        ProtectControlGroups = true;
        RestrictNamespaces = true;
        RestrictRealtime = true;
        LockPersonality = true;
      };
    };
  };
}
