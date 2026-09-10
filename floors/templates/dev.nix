# Development floor template
# Software architecture, coding, code review, testing
{ lib, ... }:
with lib;
{
  tower.floors.dev = {
    enable = true;
    displayName = "Development";
    email = "dev@polyfloor.local";
    orgName = "dev";
    timezone = "America/Los_Angeles";
    targetMachine = "luffy";
    dbSchema = "floor_dev";
    mcps = [ ];
    template = "dev";

    roles = {
      architect = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 8192;
        description = "Designs system architecture, makes technical decisions";
      };
      developer = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Writes code, implements features, fixes bugs";
      };
      reviewer = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 4096;
        description = "Reviews code quality, security, and maintainability";
      };
    };

    dailyBudgetUSD = 0.0;
    persistPaths = [ "outputs" "sessions" "sprint-board" ];
  };
}
