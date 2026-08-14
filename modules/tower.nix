{ config, lib, pkgs, ... }:
with lib;
let cfg = config.tower; in
{
  imports = [ ./floor-base.nix ];

  options.tower = {
    enable   = mkEnableOption "Polyfloor Tower";
    dataDir  = mkOption { type = types.path;   default = "/var/polyfloor"; };
    dbHost   = mkOption { type = types.str;    default = "localhost"; };
    dbPort   = mkOption { type = types.port;   default = 5432; };
    hostRole = mkOption {
      type    = types.enum [ "meta" "worker" "all" ];
      default = "all";
    };
    omniroute = {
      enable      = mkEnableOption "OmniRoute LLM gateway" // { default = true; };
      port        = mkOption { type = types.port; default = 20128; };
      secretsFile = mkOption { type = types.path; };
    };
  };

  config = mkIf cfg.enable {
    systemd.tmpfiles.rules = [
      "d ${cfg.dataDir}        0750 polyfloor polyfloor -"
      "d ${cfg.dataDir}/floors 0750 polyfloor polyfloor -"
      "d ${cfg.dataDir}/outputs 0750 polyfloor polyfloor -"
      "d ${cfg.dataDir}/logs   0750 polyfloor polyfloor -"
    ];

    users.users.polyfloor  = { isSystemUser = true; group = "polyfloor"; home = cfg.dataDir; };
    users.groups.polyfloor = {};

    # Use existing PostgreSQL — only ensure DB and user exist
    services.postgresql.ensureUsers     = [{ name = "polyfloor"; ensureDBOwnership = true; }];
    services.postgresql.ensureDatabases = [ "polyfloor" ];

    environment.persistence."/persist".directories = [
      { directory = "/var/polyfloor"; user = "polyfloor"; group = "polyfloor"; mode = "0750"; }
    ];

    systemd.services.polyfloor-backend = {
      description = "Polyfloor FastAPI backend";
      wantedBy    = [ "multi-user.target" ];
      after       = [ "postgresql.service" "network.target" ];
      environment = {
        WAYLAND_DISPLAY           = "wayland-1";
        XDG_SESSION_TYPE          = "wayland";
        XDG_RUNTIME_DIR           = "/run/user/1000";
        NIXOS_OZONE_WL            = "1";
        MOZ_ENABLE_WAYLAND        = "1";
        GBM_BACKEND               = "nvidia-drm";
        __GLX_VENDOR_LIBRARY_NAME = "nvidia";
        WLR_NO_HARDWARE_CURSORS   = "1";
      };
      serviceConfig = {
        User       = "polyfloor";
        WorkingDirectory = "${cfg.dataDir}";
        ExecStart  = "${pkgs.uv}/bin/uv run uvicorn main:app --host 127.0.0.1 --port 8001";
        Restart    = "on-failure";
        RestartSec = "5s";
      };
    };
  };
}
