# Digital Production floor template
# Content creation, media production, publishing workflows
{ lib, ... }:
with lib;
{
  tower.floors.production = {
    enable = true;
    displayName = "Digital Production";
    email = "production@polyfloor.local";
    orgName = "production";
    timezone = "America/Los_Angeles";
    targetMachine = "luffy";
    dbSchema = "floor_production";
    mcps = [ ];
    template = "digital-production";

    roles = {
      orchestrator = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 8192;
        description = "Coordinates content production pipeline and task delegation";
      };
      writer = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Creates written content, scripts, and copy";
      };
      editor = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 4096;
        description = "Reviews and edits content for quality and consistency";
      };
      designer = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Creates visual assets and layout designs";
      };
    };

    dailyBudgetUSD = 0.0;
    persistPaths = [ "outputs" "sessions" "sprint-board" ];
  };
}
