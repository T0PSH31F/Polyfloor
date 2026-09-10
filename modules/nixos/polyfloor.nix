{ config, lib, ... }:

with lib;

let
  cfg = config.services.polyfloor;
in
{
  options.services.polyfloor = {
    enable = mkEnableOption "Polyfloor AI company OS service daemon";

    package = mkOption {
      type = types.package;
      description = "The Polyfloor package to run.";
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
      description = "Data directory for Polyfloor application state.";
    };

    openFirewall = mkOption {
      type = types.bool;
      default = false;
      description = "Whether to open the HTTP port in the firewall.";
    };

    environmentFile = mkOption {
      type = types.nullOr types.path;
      default = null;
      description = "Path to environment file containing secrets (e.g. API keys, tokens).";
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
        POLYFLOOR_OUTPUT_ROOT = "${cfg.dataDir}/floors";
      };

      serviceConfig = {
        ExecStart = "${cfg.package}/bin/polyfloor";
        Restart = "on-failure";
        RestartSec = "5s";

        DynamicUser = true;
        WorkingDirectory = cfg.dataDir;

        EnvironmentFile = mkIf (cfg.environmentFile != null) cfg.environmentFile;

        # Hardening sandboxing primitives
        NoNewPrivileges = true;
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        ReadWritePaths = [ cfg.dataDir ];
        StateDirectory = "polyfloor";

        # Security bounds
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
