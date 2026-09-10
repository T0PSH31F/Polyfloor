# Research floor template
# Investigation, analysis, knowledge synthesis, report writing
{ lib, ... }:
with lib;
{
  tower.floors.research = {
    enable = true;
    displayName = "Research";
    email = "research@polyfloor.local";
    orgName = "research";
    timezone = "America/Los_Angeles";
    targetMachine = "luffy";
    dbSchema = "floor_research";
    mcps = [ ];
    template = "research";

    roles = {
      lead = {
        enable = true;
        model = "free://best-reasoning";
        maxTokens = 8192;
        description = "Leads research direction, synthesizes findings, coordinates team";
      };
      analyst = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Performs data analysis, fact-checking, source verification";
      };
      writer = {
        enable = true;
        model = "free://best-fast";
        maxTokens = 4096;
        description = "Produces research reports, summaries, documentation";
      };
    };

    dailyBudgetUSD = 0.0;
    persistPaths = [ "outputs" "sessions" "sprint-board" ];
  };
}
