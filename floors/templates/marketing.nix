# Marketing floor template
# Campaign strategy, copywriting, analytics, brand management
{ lib, ... }:
with lib;
{
  tower.floors.marketing = {
    enable = true;
    displayName = "Marketing";
    email = "marketing@polyfloor.local";
    orgName = "marketing";
    timezone = "America/Los_Angeles";
    targetMachine = "luffy";
    dbSchema = "floor_marketing";
    mcps = [ ];
    template = "marketing";

    roles = {
      strategist = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 8192;
        description = "Plans campaigns, analyzes market trends, sets strategy";
      };
      copywriter = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Writes marketing copy, ad text, social posts";
      };
      analyst = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 4096;
        description = "Analyzes campaign performance and market data";
      };
    };

    dailyBudgetUSD = 0.0;
    persistPaths = [ "outputs" "sessions" "sprint-board" ];
  };
}
